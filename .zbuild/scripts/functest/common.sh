#!/bin/bash
#
# Unit testing helper vars
#

# make sure to include the 'to-be-tested' zbuild dir
# before all other paths
TEST_SCRIPTPATH=`readlink -f $0`
export TEST_SCRIPTDIR=`dirname $TEST_SCRIPTPATH`

ZBUILD_DIR=`dirname $(dirname $(dirname $(dirname $TEST_SCRIPTPATH)))`
export PYTHONPATH=$ZBUILD_DIR:$PYTHONPATH

# The zbuild exec to test with
ZEB=$ZBUILD_DIR/zbuild

ARGS=""

WD=/tmp/zbuild-functest

# Setup buildsets
addbscript() {
    $ZEB $ARGS add $*
    if [ "$?" != "0" ]; then echo "ERROR: could add script '$*'"; exit 1; fi
}
