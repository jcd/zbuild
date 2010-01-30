#!/bin/bash
#
# Run all available tests
#

# make sure to include the 'to-be-tested' zbuild dir
# before all other paths
TEST_SCRIPTPATH=`readlink -f $0`
export TEST_SCRIPTDIR=`dirname $TEST_SCRIPTPATH`
ZBUILD_DIR=`dirname $(dirname $TEST_SCRIPTPATH)`
export PYTHONPATH=$ZBUILD_DIR:$PYTHONPATH

# The zbuild exec to test with
ZEB=$ZBUILD_DIR/zbuild

echo "Testing zbuild in dir $ZBUILD_DIR"

WD=/tmp/zbuild-functest
rm -rf $WD
mkdir $WD

pushd $WD

ARGS=""

$ZEB $ARGS init 

# Import the test scripts
$ZEB $ARGS sync $ZBUILD_DIR/test/scripts/
if [ "$?" != "0" ]; then echo "ERROR: could not sync scripts"; fi

$ZEB $ARGS list
if [ "$?" != "0" ]; then echo "ERROR: could list sync scripts"; fi

# Setup buildsets
addbscript() {
    $ZEB $ARGS add $*
    if [ "$?" != "0" ]; then echo "ERROR: could add script '$*'"; fi
}

addbscript testbuildset0 0
addbscript testbuildset0 1
addbscript testbuildset0 2
addbscript 0 6
addbscript 0 7

$ZEB $ARGS list 0
if [ "$?" != "0" ]; then echo "ERROR: could list sync scripts"; fi

$ZEB $ARGS build 0
if [ "$?" != "0" ]; then echo "ERROR: could not build 0"; fi

exit 0

addbscript testbuildset1 repos1

$ZEB $ARGS build 1
if [ "$?" != "0" ]; then echo "ERROR: could not build 1"; fi


$ZEB $ARGS sync localhost:$ZBUILD_DIR#test/scripts/
if [ "$?" != "0" ]; then echo "ERROR: could not sync scripts"; fi

addbscript testbuildset2 18

$ZEB $ARGS build 2
if [ "$?" != "0" ]; then echo "ERROR: could not build 2"; fi

#$ZEB $ARGS schedule 0 '23:58'
#if [ "$?" != "0" ]; then echo "ERROR: could build 0"; fi

#$ZEB $ARGS server

# addbscript testbuildset1 success.sh
# addbscript testbuildset1 failure.sh
# addbscript testbuildset1 subscript1
# addbscript 0 subscript2/success.sh
# addbscript 0 subscript2/failure.sh

# rm -rf $T

exit 0



