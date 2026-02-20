# OPAL regression tests

## Introduction

The _OPAL_ regression tests are mantained in this repository. To run all
(active) tests, you have to compile _OPAL_ with all relevant features
enabled (AMR, AMR_MG_SOLVER, BANDRF, MSLANG, OPAL_FEL, SAAMG_SOLVER).

## Directory hierarchy

`RegressionTests`: active regression tests.

`DisabledTests`: tests which are somehow broken and require a review.

## Running a single regression tests

* Setup the environment required to run _OPAL_ (e.g. by loading required modules)
* Set the environment variable `OPAL_EXE_PATH` to the directory where the `opal` binary is located.
* Run the script `<TEST>.local` (replace `<TEST>` with the name of the regression test to run).

Notes:
* You can but don't have to change into the directory of the regression test. For example: You can start the AWAGun-1 test with the command `./RegressionTests/AWAGun-1/AWAGun-1.local`.
* With the above steps, a regression test is performed, but the results are not verified! The verification must be done in a seperate step, see below.

## Verifing the result of a regression test

The results of a regression test can be verified with the tool `verify_test` which is available in the NightlyBuild repository:
```
verify_test <DIR_OF_TEST>
```
if the script is in available via `PATH` or otherwise
```
<DIR>/verify_test <DIR_OF_TEST>
```
(replace `<DIR>` with the directory where the script is located).

Example:
```
verify_test RegressionTests/AWAGun-1
```

Notes:
* `verify_test` is written in Python and requires some non-default modules like pathlib. You might have to setup our own Python environment. At PSI you can use the module `Python/3.6.3`.

## Run and verify all regression test

* setup environment to run _OPAL_ (don't forget to set `OPAL_EXE_PATH`)
* clone this repository
* cd into the cloned repository
* run all tests
```
for test in ./RegressionTests/*; do
    ${test}/*.local
done
```
* verify all tests
```
VERIFY_TEST_DIR=<DIR>
for test in ./RegressionTests/*; do
    ${VERIY_TEST_DIR}/verify_test ${test}
done
```


## Create a Reference Solution

1. run the simulation in an isolated directory
2. execute the script below
3. commit the directory to the repository

```
#
F=`ls *.in`
FB=`basename -s ".in" $F`
F1=`ls $FB.out`
F2=`ls $FB.stat`
F3=`ls $FB.lbal`
#
mkdir -p reference
cp $F1 reference/
cp $F2 reference/
cp $F3 reference/
#
cd reference
md5sum $F1 > $F1.md5
md5sum $F2 > $F2.md5
md5sum $F3 > $F3.md5
```
