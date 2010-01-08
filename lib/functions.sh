# Remember args
ARGC=$#
ARG1=$1
export LANG="en_US.UTF-8"

#
# Common functions that can be helpfull in creating build bash scripts
#
if [ -z $ZBUILD_REPOS_LOCAL_COPY ]; then
    export ZBUILD_REPOS_LOCAL_COPY=~/zbuild-workdir/repos-local-copy
fi
if [ -z $ZBUILD_WORKDIR ]; then
    export ZBUILD_WORKDIR=~/zbuild-workdir
fi
if [ -z $ZBUILD_BUILDDIR ]; then
    export ZBUILD_BUILDDIR=~/zbuild-workdir/build-area
fi
if [ -z $ZBUILD_RELEASE_DIR ]; then
    export ZBUILD_RELEASE_DIR=~/zbuild-workdir/deb-repos
fi

#
# Logging
#
zlog() {
    date +"%Y-%m-%d %H:%M:%S: $*"
}

zerr() {
    date +"%Y-%m-%d %H:%M:%S: $*" 1>&2
}

filter_stderr()  
    { $1 2>&1 >&3 3>&- | grep -v "$2" >&2 3>&- ; } 3>&1


#
# A pseudo unique jail ID. If not in jail it is just the username
#
zjail_id() {
    JID="${USER}"
    if is_jailed ; then
	JID="${JAILHOME//\//_}"
    fi
    
    if [ -z "$JID" ]; then 
	zlog "Cannot resolve jail ID -> aborting"
	exit 1
    fi
    echo $JID
}

zbuild_get_ip() {
    if [ -z "$JAILIP" ]; then
	ip addr | sed -ne'/^...eth0/,/^[^ ]/ p' | grep inet | head -n1 | sed -ne's/^.*inet.\(.\+\)\/.*/\1/ p'
    else
	echo $JAILIP
    fi
}

#
# Function to test enabled flags
#
zbuild_noclean_enabled() {
    test "$ZBUILD_NOCLEAN_ENABLED" != ""
    return $?
}

zbuild_release_enabled() {
    test "$ZBUILD_RELEASE_ENABLED" != ""
    return $?
}

#
# Get the debian version from the changelog file in [curdir]/debian/changelog
#
zbuild_get_version() {

    if [ $# -lt 1 ]; then zlog "zbuild_get_version needs build dir as first parameter"; fi

    head -n 1 $1/debian/changelog | sed -e 's/.*(\(.*\)).*/\1/'
}

zbuild_get_repos_revision() {

    if [ $# -lt 1 ]; then zlog "zbuild_get_repos_revision needs build dir as first parameter"; fi

    git log --pretty=oneline | wc -l
    
    #D=`git log | head -n 3 | tail -n 1 | sed -ne 's/^Date:[[:blank:]]\+\(.*\) +..../\1/ p'`
    #TF=`tempfile`
    #echo "import time" > $TF
    #echo "print str(int(time.mktime(time.strptime('$D', '%c'))))" >> $TF
    #python $TF
}

zbuild_get_requested_revision() {
    zbuild buildinfo $1 | sed -ne 's/^revision[[:blank:]]\(.*\)/\1/ p'
}

zbuild_get_requested_branch() {
    zbuild buildinfo $1 | sed -ne 's/^branch[[:blank:]]\(.*\)/\1/ p'
}

#
# Echo working dir of specified package + revision
#
zbuild_get_builddir() {

    # Src dir is the first arg
    if [ $# -ge 1 ]; then
	PACKDIR="$1"
    else
	echo "No package directory provided to build in zbuild_checkout"
	return 1
    fi

    # Revision to build is optionally 2nd param
    REV="HEAD"
    if [ $# -ge 2 ]; then
	REV="$2"
    fi
    echo "$ZBUILD_BUILDDIR/$PACKDIR/$REV"
    return 0
}


#
# Checkout a package from git: repos [branch]
#
zbuild_checkout() {

    # Src dir is the first arg
    if [ $# -ge 1 ]; then
	PACKNAME=`basename "$1"`
	GITSOURCE="$1"
   else
	zerr "No git source provided to build in zbuild_checkout" 
	return 1
    fi

    # Branch to build 
    REFSPEC="$ZBUILD_REFSPEC"
    if [ -z $ZBUILD_REFSPEC ]; then
	REFSPEC="master"
    fi

    # Checkout the revision 
    mkdir -p "$ZBUILD_BUILDDIR"

    BUILDDIR="$ZBUILD_BUILDDIR/$PACKNAME"

    OPT=""
    if zbuild_noclean_enabled; then
	if [ -e "$BUILDDIR" ]; then
	    zlog "Noclean flag enabled -> reusing git checkout"
	    zlog "Updating checkout in build dir"
	    cd "$BUILDDIR"
	    git pull 
	    filter_stderr "git checkout $REFSPEC" 'Already on'
	    return 0
	fi
	# No existing checkout. Just proceed with normal checkout
	# then.
    fi

    # Ensure local git copy dir exists
    mkdir -p "$ZBUILD_REPOS_LOCAL_COPY"

    if [ ! -d "$ZBUILD_REPOS_LOCAL_COPY/$PACKNAME" ]; then
	zlog "git checkout of local git copy $GITSOURCE"
	cd "$ZBUILD_REPOS_LOCAL_COPY"
	git clone "$GITSOURCE"
    else
	zlog "git update of local git copy $GITSOURCE"
	zlog "local copy in $ZBUILD_REPOS_LOCAL_COPY/$PACKNAME"
	cd "$ZBUILD_REPOS_LOCAL_COPY/$PACKNAME"
	git pull 2>&1
    fi
    
    # Remove existing checkout if any
    zlog "Removing old working copy of $PACKNAME"
    rm -rf "$BUILDDIR"

    # Copy local GIT repos copy to working area
    zlog "Copying local git copy to workdir $BUILDDIR"
    zlog "cp -r $ZBUILD_REPOS_LOCAL_COPY/$PACKNAME $ZBUILD_BUILDDIR/"
    cp -r "$ZBUILD_REPOS_LOCAL_COPY/$PACKNAME" "$ZBUILD_BUILDDIR/"

    # Update the correct refspec
    zlog "Updating checkout in build dir to revision $REV"
    cd "$BUILDDIR"
    filter_stderr "git checkout $REFSPEC" 'Already on'

    zlog "Done updating checkout in $BUILDDIR"

    cd "$BUILDDIR"
    return 0
}

zbuild_packnames() {

    if [ $# -lt 1 ]; then zlog "zbuild_packnames needs build dir as first parameter"; fi

    PACKS=`grep "Package" $1/debian/control | cut -f2 -d':'`
    VER=`head -n 1 $1/debian/changelog | sed -e 's/.*(\([0-9\.]*\)-.*).*/\1/'`
    REV=`zbuild_get_repos_revision $1`
    for PACK in $PACKS ; do 
	DEB_BASEPACK="${PACK}_${VER}-${REV}"
	echo $DEB_BASEPACK
    done    
}

zbuild_aptget_packnames() {

    if [ $# -lt 1 ]; then zlog "zbuild_aptget_packnames needs build dir as first parameter"; fi

    PACKS=`grep "Package" $1/debian/control | cut -f2 -d':'`
    VER=`head -n 1 $1/debian/changelog | sed -e 's/.*(\([0-9\.]*\)-.*).*/\1/'`
    REV=`zbuild_get_repos_revision $1`
    for PACK in $PACKS ; do 
	DEB_BASEPACK="${PACK}=${VER}-${REV}"
	echo $DEB_BASEPACK
    done
}

zbuild_build() {

    # Src dir is the first arg
    if [ $# -ge 1 ]; then
	PACKNAME="$1"
    else
	echo "No package directory provided to build in zbuild_build_git"
	return 1
    fi

    # Branch to build 
    REFSPEC="$ZBUILD_REFSPEC"
    if [ -z $ZBUILD_REFSPEC ]; then
	REFSPEC="master"
    fi

    BUILDDIR="$ZBUILD_BUILDDIR/$PACKNAME"
    zbuild_build_internal $BUILDDIR $PACKNAME
}

#
# zbuild_build <build dir> <pack_name> 
#
zbuild_build_internal() {

    BUILDDIR=$1
    cd $BUILDDIR

    PACK=$2

    # First remove build revision if present
    pwd
    sed -i -e "1,1 s/\(.*\)(\([0-9\.]*\)-.*)\(.*\)/\1(\2)\3/" debian/changelog

    # First remove any existing debian packages matching this dir
    PACKS=`grep "Package" debian/control | cut -f2 -d':'`

    # Current version according to debian/control
    VER=`zbuild_get_version .`
    ORIG_VER=$VER

    # Actual revision to be used
    REV=`zbuild_get_repos_revision .`

    echo "$PACKS"

    rm debian/files 2>/dev/null

    for PACK in $PACKS ; do 
	DEB_BASEPACK="${PACK}_${VER}-${REV}"
	echo "Removing existing packages '$DEB_BASEPACK*.{deb,changes,tar.gz,dsc}'"
	rm -f ./../$DEB_BASEPACK*.{deb,changes,tar.gz,dsc}
    done

    if [ ! -z "$ZBUILD_RELEASING" ]; then

	# This is a release and we should update the 

	# the releasing flag has been set which mean that instead of
	# checking out we should give the option to enter the version
	# number
	#VS="$ZBUILD_STARTDIR/versions"
	#if [ -e "$VS" ]; then
	#    VER_CAND=`sed -ne "s/${PACK}[[:blank:]]\+=[[:blank:]]\+\([0-9\.]\+\).*/\1/ p" $VS`
	#    if [ ! -z "$VER_CAND" ]; then
	#	echo "Vercand is '$VER_CAND'"
	#	VER=$VER_CAND
	#	DEB_BASEPACK=`echo "$DEB_BASEPACK" | sed -ne "s/\([^_]\+_\)[^-]\+\(-.*\)/\1${VER}\2/ p"`
	#    fi
	#    echo "Setting version to '$VER'"
	#fi
	echo ""
    fi

    # Dont let modified file disturb tagging
    git checkout -- debian/changelog

    if [ ! -z "$ZBUILD_RELEASING" ]; then

	# This is a release and we should create a tag to the current
        # commit named vVERSION-REVISION
	git fetch --tags 2>/dev/null
	git tag -f -a "v$VER-$REV" -m "Release of version v$VER-$REV (build system)"
	git push --tags 2>/dev/null
    fi

    # Modify the changelog version number to include the build
    sed -i -e "1,1 s/\(.*\)(\(.*\))\(.*\)/\1($VER-$REV)\3/" debian/changelog

    # Build package and install
    LOGFILE=`tempfile`

    OPT=""
    if zbuild_noclean_enabled ; then
	zlog "Noclean enabled -> rebuilding packages without cleaning (-nc flag)"
	OPT="-nc"
    fi

    pushd .
    if dpkg-buildpackage $OPT -us -uc -rfakeroot 2>&1 >$LOGFILE
	then 
	echo "Building $DEB_BASEPACK successful"
	rm $LOGFILE
	popd
    else
	echo "Error: during building of package(s) $PACKS"
	echo "Build and packaging log :"
	cat $LOGFILE
	rm $LOGFILE
	popd
	return 1
    fi
    return 0
}

zbuild_install() {

    # Src dir is the first arg
    if [ $# -ge 1 ]; then
	PACKDIR="$1"
    else
	echo "No package directory provided to build in zbuild_install"
	return 1
    fi

    # Revision to build is optionally 2nd param
    REV="HEAD"
    if [ $# -ge 2 ]; then
	REV="$2"
    fi

    # Pre-seed the debconf selections
    if [ $# -ge 3 ]; then
	echo "Preceeding debconf selections using:"
	cat "$3"
	sudo debconf-set-selections "$3"
    fi

    # cd "$ZBUILD_BUILDDIR/$PACKDIR/$REV"
    cd "$ZBUILD_BUILDDIR/$PACKDIR"

    PACKS=`zbuild_aptget_packnames .`
    IPACKS=""
    for PACK in $PACKS ; do 
	# P=`ls -1 ../${PACK}*.deb`
	IPACKS="$IPACKS $PACK"
    done

    sudo apt-get update | grep -v "http://"

    echo "Installing $IPACKS"
    if sudo apt-get --force-yes --assume-yes install --reinstall $IPACKS ; then
	echo "$PACK installed"
    else
	echo "Error: error during installation of $IPACKS"
	exit 1
    fi
}

zbuild_upload() {

    # Src dir is the first arg
    if [ $# -ge 1 ]; then
	PACKDIR="$1"
    else
	echo "No package directory provided to build in zbuild_install"
	return 1
    fi

    cd "$ZBUILD_BUILDDIR/$PACKDIR"

    PACKS=`zbuild_packnames .`
    IPACKS=""
    for PACK in $PACKS ; do 
	echo "Uploading $PACK to $ZBUILD_RELEASE_DIR"
	P=`ls -1 ../${PACK}*.deb`
	cp $P $ZBUILD_RELEASE_DIR/
    done

    cd $ZBUILD_RELEASE_DIR
    dpkg-scanpackages . /dev/null 2>/dev/null | gzip > Packages.gz
    
    # Ensure apt-get knows about the location of our apt repository
    sudo bash -c "echo 'deb file:$ZBUILD_RELEASE_DIR ./' > /etc/apt/sources.list.d/zbuild.list" 
}

zbuild_release() {

    if ! zbuild_release_enabled; then
	zlog "Release flag not set -> skipping release deb repository"
	return 0
    fi

    # Src dir is the first arg
    if [ $# -ge 1 ]; then
	PACKDIR="$1"
    else
	echo "No package directory provided to build in zbuild_release"
	return 1
    fi

    # Revision to build is optionally 2nd param
    REV="HEAD"
    if [ $# -ge 2 ]; then
	REV="$2"
    fi

    cd "$ZBUILD_BUILDDIR/$PACKDIR/$REV"

    mkdir -p "$ZBUILD_RELEASE_DIR"

    PACKS=`zbuild_packnames .`
    IPACKS=""
    for PACK in $PACKS ; do 
	P=`ls -1 ../${PACK}*.deb`
	cp $P "$ZBUILD_RELEASE_DIR/"
    done

    cd "$ZBUILD_RELEASE_DIR"
    
    dpkg-scanpackages . /dev/null 2>/dev/null | gzip > Packages.gz
}

is_jailed() {
    ! stat / | grep -q "Inode: 2 "
    return $?
}

export -f zjail_id
export -f is_jailed
export -f zbuild_get_ip
export -f zbuild_checkout
export -f zbuild_build
export -f zbuild_build_internal
export -f zbuild_install
export -f zbuild_upload
export -f zbuild_release
export -f zbuild_get_builddir
export -f zbuild_get_version
export -f zbuild_get_repos_revision
export -f zbuild_packnames
export -f zbuild_aptget_packnames
export -f zbuild_noclean_enabled
export -f zbuild_release_enabled
export -f zlog
export -f filter_stderr

# execute script as first arg if available
if [ $ARGC -ge 1 ]; then
    $ARG1 ;
fi
