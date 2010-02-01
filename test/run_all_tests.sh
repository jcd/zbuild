#!/bin/bash

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



