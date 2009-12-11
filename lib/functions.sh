# Remember args
ARGC=$#
ARG1=$1
export LANG="en_US.UTF-8"

#
# Common functions that can be helpfull in creating build bash scripts
#
if [ -z $BUILDER_REPOS_LOCAL_COPY ]; then
    export BUILDER_REPOS_LOCAL_COPY=~/zbuild-repos-local-copy
fi
if [ -z $BUILDER_GIT ]; then
    export BUILDER_GIT=git@github.com:jcd/
fi
if [ -z $BUILDER_WORKDIR ]; then
    export BUILDER_WORKDIR=~/zbuildworkdir
fi
if [ -z $BUILDER_RELEASE_DIR ]; then
    export BUILDER_RELEASE_DIR=~/zbuild-deb-repos
fi

#
# Logging
#
zlog() {
    date +"%Y-%m-%d %H:%M:%S: $*"
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

zpack_get_ip() {
    if [ -z "$JAILIP" ]; then
	ip addr | sed -ne'/^...eth0/,/^[^ ]/ p' | grep inet | head -n1 | sed -ne's/^.*inet.\(.\+\)\/.*/\1/ p'
    else
	echo $JAILIP
    fi
}

#
# Function to test enabled flags
#
zpack_noclean_enabled() {
    test "$BUILDER_NOCLEAN_ENABLED" != ""
    return $?
}

zpack_release_enabled() {
    test "$BUILDER_RELEASE_ENABLED" != ""
    return $?
}

#
# Get the debian version from the changelog file in [curdir]/debian/changelog
#
zpack_get_version() {

    if [ $# -lt 1 ]; then zlog "zpack_get_version needs workdir as first parameter"; fi

    head -n 1 $1/debian/changelog | sed -e 's/.*(\(.*\)).*/\1/'
}

zpack_get_svn_revision() {

    if [ $# -lt 1 ]; then zlog "zpack_get_svn_revision needs workdir as first parameter"; fi

    svn info $1 | grep "Revision" | cut -d':' -f2 | sed -e 's/[^0-9]*\([[:digit:]]*\)/\1/'
}

zpack_get_git_revision() {

    if [ $# -lt 1 ]; then zlog "zpack_get_git_revision needs workdir as first parameter"; fi

    git log --pretty=oneline | wc -l
    
    #D=`git log | head -n 3 | tail -n 1 | sed -ne 's/^Date:[[:blank:]]\+\(.*\) +..../\1/ p'`
    #TF=`tempfile`
    #echo "import time" > $TF
    #echo "print str(int(time.mktime(time.strptime('$D', '%c'))))" >> $TF
    #python $TF
}

zpack_get_repos_revision() {
    if [ -e .git ]; then
	zpack_get_git_revision $1
    else
	zpack_get_svn_revision $1
    fi
}

zpack_get_requested_revision() {
    zbuild buildinfo $1 | sed -ne 's/^revision[[:blank:]]\(.*\)/\1/ p'
}

zpack_get_requested_branch() {
    zbuild buildinfo $1 | sed -ne 's/^branch[[:blank:]]\(.*\)/\1/ p'
}

#
# Echo working dir of specified package + revision
#
zpack_get_workdir() {

    # Src dir is the first arg
    if [ $# -ge 1 ]; then
	PACKDIR="$1"
    else
	echo "No package directory provided to build in zpack_checkout"
	return 1
    fi

    # Revision to build is optionally 2nd param
    REV="HEAD"
    if [ $# -ge 2 ]; then
	REV="$2"
    fi
    echo "$BUILDER_WORKDIR/$PACKDIR/$REV"
    return 0
}

#
# Checkout a package: <packdir>
#
zpack_checkout() {

    # Src dir is the first arg
    if [ $# -ge 1 ]; then
	PACKDIR="$1"
    else
	echo "No package directory provided to build in zpack_checkout"
	return 1
    fi

    # Revision to build is optionally 2nd param
    REV=`zpack_get_requested_revision $PACKDIR`
    BRANCH=`zpack_get_requested_branch $PACKDIR`

    BUILD_DIR="$BUILDER_WORKDIR/$PACKDIR/$BRANCH/$REV"

    # Checkout the revision 
    mkdir -p "$BUILDER_WORKDIR"

    OPT=""
    if zpack_noclean_enabled; then
	if [ -e "$BUILD_DIR" ]; then
	    echo "Noclean flag enabled -> reusing svn checkout"
	    echo "Updating checkout in workdir to revision $REV"
	    svn update -r "$REV" "$BUILD_DIR"
	    cd "$BUILD_DIR"
	    return 0
	fi
    fi

    # Remove existing checkout if any
    echo "Removing old working copy of revision $REV"
    rm -rf "$BUILD_DIR"

    # Ensure local svn copy dir exists
    mkdir -p "$BUILDER_REPOS_LOCAL_COPY"

    if [ ! -d "$BUILDER_REPOS_LOCAL_COPY/$PACKDIR" ]; then
	echo "svn checkout of local svn copy $BUILDER_SVN/$PACKDIR"
	svn checkout "$BUILDER_SVN/$PACKDIR" "$BUILDER_REPOS_LOCAL_COPY/$PACKDIR"
    else
	echo "svn update of local svn copy $BUILDER_SVN/$PACKDIR"
	svn update "$BUILDER_REPOS_LOCAL_COPY/$PACKDIR"
    fi
    
    echo "copying local svn copy to workdir $BUILDER_WORKDIR"
    mkdir -p "$BUILDER_WORKDIR/$PACKDIR"
    cp -r "$BUILDER_REPOS_LOCAL_COPY/$PACKDIR" "$BUILD_DIR"

    echo "Updating checkout in workdir to revision $REV"
    svn update -r "$REV" "$BUILD_DIR"
    echo "Done updating checkout in $BUILD_DIR"

    cd "$BUILD_DIR"

    return 0
}

#
# Checkout a package from git: repos [branch]
#
zpack_checkout_git() {

    # Src dir is the first arg
    if [ $# -ge 1 ]; then
	PACKNAME="$1"
    else
	echo "No git source provided to build in zpack_checkout_git"
	return 1
    fi

    # Branch to build 
    REFSPEC="$BUILDER_REFSPEC"
    if [ -z $BUILDER_REFSPEC ]; then
	REFSPEC="master"
    fi

    # Checkout the revision 
    mkdir -p "$BUILDER_WORKDIR"

    WORKDIR="$BUILDER_WORKDIR/$PACKNAME"

    OPT=""
    if zpack_noclean_enabled; then
	if [ -e "$WORKDIR" ]; then
	    echo "Noclean flag enabled -> reusing git checkout"
	    echo "Updating checkout in workdir"
	    cd "$WORKDIR"
	    git pull 
	    filter_stderr "git checkout $REFSPEC" 'Already on'
	    return 0
	fi
	# No existing checkout. Just proceed with normal checkout
	# then.
    fi

    # Ensure local svn copy dir exists
    mkdir -p "$BUILDER_REPOS_LOCAL_COPY"

    if [ ! -d "$BUILDER_REPOS_LOCAL_COPY/$PACKNAME" ]; then
	echo "git checkout of local git copy $BUILDER_GIT/$PACKNAME"
	cd "$BUILDER_REPOS_LOCAL_COPY"
	git clone "$BUILDER_GIT/$PACKNAME"
    else
	echo "git update of local svn copy $BUILDER_GIT/$PACKNAME"
	echo "local copy in $BUILDER_REPOS_LOCAL_COPY/$PACKNAME"
	cd "$BUILDER_REPOS_LOCAL_COPY/$PACKNAME"
	git pull 2>&1
    fi
    
    # Remove existing checkout if any
    echo "Removing old working copy of $PACKNAME"
    rm -rf "$WORKDIR"

    # Copy local GIT repos copy to working area
    echo "Copying local git copy to workdir $WORKDIR"
    echo "cp -r $BUILDER_REPOS_LOCAL_COPY/$PACKNAME $BUILDER_WORKDIR/"
    cp -r "$BUILDER_REPOS_LOCAL_COPY/$PACKNAME" "$BUILDER_WORKDIR/"

    # Update the correct refspec
    echo "Updating checkout in workdir to revision $REV"
    cd "$WORKDIR"
    filter_stderr "git checkout $REFSPEC" 'Already on'

    echo "Done updating checkout in $WORKDIR"

    cd "$WORKDIR"
    return 0
}

zpack_packnames() {

    if [ $# -lt 1 ]; then zlog "zpack_packnames needs workdir as first parameter"; fi

    PACKS=`grep "Package" $1/debian/control | cut -f2 -d':'`
    VER=`head -n 1 $1/debian/changelog | sed -e 's/.*(\([0-9\.]*\)-.*).*/\1/'`
    REV=`zpack_get_repos_revision $1`
    for PACK in $PACKS ; do 
	DEB_BASEPACK="${PACK}_${VER}-${REV}"
	echo $DEB_BASEPACK
    done    
}

zpack_build() {

    if [ -e .git ]; then
	zpack_build_git $1 $2
    else
	zpack_build_svn $1 $2
    fi
}

zpack_build_svn() {

    # Src dir is the first arg
    if [ $# -ge 1 ]; then
	PACKDIR="$1"
    else
	echo "No package directory provided to build in zpack_build"
	return 1
    fi

    # Revision to build is optionally 2nd param
    REV="HEAD"
    if [ $# -ge 2 ]; then
	REV="$2"
    fi

    WORKDIR="$BUILDER_WORKDIR/$PACKDIR/$REV"
    zpack_build_internal $WORKDIR $PACKDIR
}

zpack_build_git() {

    # Src dir is the first arg
    if [ $# -ge 1 ]; then
	PACKNAME="$1"
    else
	echo "No package directory provided to build in zpack_build_git"
	return 1
    fi

    # Branch to build 
    REFSPEC="$BUILDER_REFSPEC"
    if [ -z $BUILDER_REFSPEC ]; then
	REFSPEC="master"
    fi

    WORKDIR="$BUILDER_WORKDIR/$PACKNAME"
    zpack_build_internal $WORKDIR $PACKNAME
}

#
# zpack_build <workdir> <pack_name> 
#
zpack_build_internal() {

    WORKDIR=$1
    cd $WORKDIR

    PACK=$2

    # First remove build revision if present
    pwd
    sed -i -e "1,1 s/\(.*\)(\([0-9\.]*\)-.*)\(.*\)/\1(\2)\3/" debian/changelog

    # First remove any existing debian packages matching this dir
    PACKS=`grep "Package" debian/control | cut -f2 -d':'`

    # Current version according to debian/control
    VER=`zpack_get_version .`
    ORIG_VER=$VER

    # Actual revision to be used
    REV=`zpack_get_repos_revision .`

    echo "$PACKS"

    rm debian/files 2>/dev/null

    for PACK in $PACKS ; do 
	DEB_BASEPACK="${PACK}_${VER}-${REV}"
	echo "Removing existing packages '$DEB_BASEPACK*.{deb,changes,tar.gz,dsc}'"
	rm -f ./../$DEB_BASEPACK*.{deb,changes,tar.gz,dsc}
    done

    if [ ! -z "$BUILDER_RELEASING" ]; then

	# This is a release and we should update the 

	# the releasing flag has been set which mean that instead of
	# checking out we should give the option to enter the version
	# number
	#VS="$BUILDER_STARTDIR/versions"
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

    if [ ! -z "$BUILDER_RELEASING" ]; then

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
    if zpack_noclean_enabled ; then
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

zpack_install() {

    # Src dir is the first arg
    if [ $# -ge 1 ]; then
	PACKDIR="$1"
    else
	echo "No package directory provided to build in zpack_install"
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

    cd "$BUILDER_WORKDIR/$PACKDIR/$REV"

    PACKS=`zpack_packnames .`
    IPACKS=""
    for PACK in $PACKS ; do 
	P=`ls -1 ../${PACK}*.deb`
	IPACKS="$IPACKS $P"
    done

    echo "Installing $IPACKS"
    if sudo dpkg -i $IPACKS ; then
	echo "$PACK installed"
    else
	echo "Error: error during installation of $IPACKS"
	exit 1
    fi
}

zpack_release() {

    if ! zpack_release_enabled; then
	zlog "Release flag not set -> skipping release deb repository"
	return 0
    fi

    # Src dir is the first arg
    if [ $# -ge 1 ]; then
	PACKDIR="$1"
    else
	echo "No package directory provided to build in zpack_release"
	return 1
    fi

    # Revision to build is optionally 2nd param
    REV="HEAD"
    if [ $# -ge 2 ]; then
	REV="$2"
    fi

    cd "$BUILDER_WORKDIR/$PACKDIR/$REV"

    mkdir -p "$BUILDER_RELEASE_DIR"

    PACKS=`zpack_packnames .`
    IPACKS=""
    for PACK in $PACKS ; do 
	P=`ls -1 ../${PACK}*.deb`
	cp $P "$BUILDER_RELEASE_DIR/"
    done

    cd "$BUILDER_RELEASE_DIR"
    
    dpkg-scanpackages . /dev/null 2>/dev/null | gzip > Packages.gz
}

is_jailed() {
    ! stat / | grep -q "Inode: 2 "
    return $?
}

export -f zjail_id
export -f is_jailed
export -f zpack_get_ip
export -f zpack_checkout
export -f zpack_checkout_git
export -f zpack_build
export -f zpack_build_git
export -f zpack_build_svn
export -f zpack_build_internal
export -f zpack_install
export -f zpack_release
export -f zpack_get_workdir
export -f zpack_get_version
export -f zpack_get_repos_revision
export -f zpack_get_svn_revision
export -f zpack_get_git_revision
export -f zpack_packnames
export -f zpack_noclean_enabled
export -f zpack_release_enabled
export -f zlog
export -f filter_stderr

# execute script as first arg if available
if [ $ARGC -ge 1 ]; then
    $ARG1 ;
fi
