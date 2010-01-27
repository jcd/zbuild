#!/bin/bash
#
# Run all available tests
#

SCRIPTPATH=`readlink -f ../zbuild`
export PYTHONPATH=$PYTHONPATH:`dirname $SCRIPTPATH`

rm -rf .zbuild

ARGS=""

# Import the test scripts
../zbuild $ARGS sync ./scripts/
if [ "$?" != "0" ]; then echo "ERROR: could not sync scripts"; fi

../zbuild $ARGS list
if [ "$?" != "0" ]; then echo "ERROR: could list sync scripts"; fi

# Setup buildsets
addbscript() {
    ../zbuild $ARGS add $*
    if [ "$?" != "0" ]; then echo "ERROR: could add script '$*'"; fi
}

addbscript testbuildset0 0
addbscript testbuildset0 1
addbscript testbuildset0 2
addbscript 0 6
addbscript 0 7

../zbuild $ARGS list 0
if [ "$?" != "0" ]; then echo "ERROR: could list sync scripts"; fi

../zbuild $ARGS build 0
if [ "$?" != "0" ]; then echo "ERROR: could build 0"; fi

addbscript testbuildset1 repos1

../zbuild $ARGS build 1
if [ "$?" != "0" ]; then echo "ERROR: could build 0"; fi

#../zbuild $ARGS schedule 0 '23:58'
#if [ "$?" != "0" ]; then echo "ERROR: could build 0"; fi

#../zbuild $ARGS server

# addbscript testbuildset1 success.sh
# addbscript testbuildset1 failure.sh
# addbscript testbuildset1 subscript1
# addbscript 0 subscript2/success.sh
# addbscript 0 subscript2/failure.sh

rm -rf $T

exit 0



