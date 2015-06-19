#!/usr/bin/python
import datetime
import sys
if sys.version_info < (3,0):
    import commands as subprocess
else:
    import subprocess
import os
import shutil

from reporter import Reporter
from reporter import TempXMLElement

from regressiontest import RegressionTest

from documentation import OpalDocumentation
from documentation import OpalDoxygen

from tools import readfile
from tools import module_load
from tools import sendmails

#FIXME: ugly global variables
totalNrTests = 0
totalNrPassed = 0

"""
This method traverses the directory tree. It will check and execute regression tests for the following directory-layouts:

    DIR Structure:
    name/name.in
         name.rt
         run
         run-parallel
         *.T7
         reference/name.lbal
         reference/name.out
         reference/name.stat
         reference/name.lbal.md5
         reference/name.out.md5
         reference/name.stat.md5

Please make sure you use this naming scheme!
"""
def callback(arg, dirname, fnames):

    global totalNrPassed
    global totalNrTests

    if ".svn" in dirname or "reference" in dirname:
        return   #exclude svn and reference dirs

    dir = str.split(dirname, "/")
    simname = dir[len(dir)-1]

    # check if all files required are available
    if not (os.path.isfile(dirname + "/" + simname + ".in") and \
       os.path.isfile(dirname + "/" + simname + ".rt") and \
       os.path.isfile(dirname + "/" + simname + ".sge") and \
       os.path.isdir(dirname + "/" + "reference")):
        return

    rep = Reporter()
    rep.appendReport("Found valid test in %s \n" % dirname)

    # check if we really want to run this test
    # empty list = run all
    runtests = arg[0]
    if runtests:
        if not simname in runtests:
            rep.appendReport("User decided to skip regression test %s \n" % simname)
            rep.appendReport("\n\n")
            return

    d = datetime.date.today()
    resultdir = "results/" + d.isoformat() + "/" + simname
    if not os.path.isdir(resultdir):
        os.makedirs (resultdir)

    simulation_report = TempXMLElement("Simulation")
    simulation_report.addAttribute("name", simname)
    simulation_report.addAttribute("date", "%s" % d)

    rt = RegressionTest(dirname, simname, resultdir)
    rt.run(simulation_report, arg[1], arg[2])
    totalNrTests += rt.totalNrTests
    totalNrPassed += rt.totalNrPassed
    rep.appendReport("\n\n")

def bailout(runAsUser):
    rep = Reporter()
    d = datetime.date.today()
    rep.appendReport("==========================================================\n")
    rep.appendReport("Finished Regression Test on %s \n" % datetime.datetime.today())
    rep.appendReport("\n")
    rep.appendReport("http://amas.web.psi.ch/regressiontests/results_%s_%s_%s.xml \n\n" % (d.day, d.month, d.year))

    #send/print report
    if not runAsUser:
        os.chdir(sys.path[0])
        emails = readfile("email-list")
        sendmails(emails, rep.getReport(), totalNrTests)
    else:
        print (rep.getReport())


def main(argv):
    rep = Reporter()
    d = datetime.date.today()
    rep.appendReport("Results: http://amas.web.psi.ch/regressiontests/results_%s_%s_%s.xml \n\n" % (d.day, d.month, d.year))

    # tests are one level up starting from directory of this script
    rundir = sys.path[0]   # get absolute path name of this script
    regdir = os.path.dirname (rundir)

    global totalNrPassed
    global totalNrTests
    totalNrTests = 0
    totalNrPassed = 0
    runAsUser = False
    runtests = list()
    run_local = False
    do_publish = True

    if "--dont-publish" in argv:
        do_publish = False

    if "--run-local" in argv:
        run_local = True

    if "--user" in argv:
        runAsUser = True
        #build a list of tests user wants to run
        for arg in argv:
            if arg.startswith("--tests"):
                tests = str.split(arg, "=")[1]
                runtests = str.split(tests, ",")
    else:
        #"load" modules need to compile and run regression tests
        modules = readfile("modules")
        for module in modules:
            module_load(module)
        os.environ["SGE_CELL"]="sgefelsim"
        os.environ["SGE_EXECD_PORT"]="6445"
        os.environ["SGE_QMASTER_PORT"]="6444"
        os.environ["SGE_ROOT"]="/gpfs/homefelsim/export/sge"
        os.environ["SGE_CLUSTER_NAME"]="sgeclusterfelsim"
        os.environ["PATH"]= os.getenv("PATH") + ":/gpfs/homefelsim/export/sge/bin/lx24-amd64:/usr/kerberos/bin"

    www_folder = os.getenv("REGTEST_WWW")
    if do_publish and www_folder is None:
        rep.appendReport("Error: REGTEST_WWW not set")
        bailout(runAsUser)
        return

    if not os.getenv("OPAL_EXE_PATH"):
        rep.appendReport("Error: OPAL_EXE_PATH not set")
        bailout(runAsUser)
        return

    if not os.path.isfile(os.getenv("OPAL_EXE_PATH") + "/opal"):
        rep.appendReport("Error: OPAL_EXE_PATH is invalid")
        bailout(runAsUser)
        return

    queue = ""
    for arg in argv:
        if arg.startswith("--queue"):
            tmp = str.split(arg, "=")
            if (len(tmp) < 2 or tmp[1] == ""):
                print("no queue given, exiting")
                sys.exit()
            queue = "-q " + tmp[1]

    rep.appendReport("\n")
    rep.appendReport("Start Regression Test on %s \n" % datetime.datetime.today())
    rep.appendReport("==========================================================\n")

    os.chdir(regdir)
    #walk the run dir tree
    arglist = [runtests, run_local, queue]
    for root, dirs, files in os.walk("./"):
        callback(arglist, root, files)

    rep.dumpXML("results.xml")

    #cp report to webdir and add entry in index.html
    if do_publish:
        failedtests = rep.NrFailed()
        brokentests = rep.NrBroken()
        webfilename = "results_%s_%s_%s.xml" % (d.day, d.month, d.year)
        shutil.copy ("results.xml", www_folder + "/" + webfilename)
        subprocess.getoutput("cp -rf results/" + d.isoformat() + "/plots " + www_folder + "/plots_" + d.isoformat())
        indexhtml = open(www_folder + "/index.html").readlines()
        for line in range(len(indexhtml)):
            if "insert here" in indexhtml[line]:
                indexhtml.insert(line+1, "<a href=\"%s\">%s.%s.%s</a> [passed:%d | broken:%d | failed:%d | total:%d] <br/>\n" % (webfilename, d.day, d.month, d.year, totalNrPassed, brokentests, failedtests, totalNrTests))
                break
        indexhtmlout = open(www_folder + "/index.html", "w")
        indexhtmlout.writelines(indexhtml)
        indexhtmlout.close()
        #update xslt formating file
        shutil.copy (rundir + "/results.xslt", www_folder + "/")

        if not runAsUser:
            #update manual
            OpalDocumentation()

            #update doxygen
            OpalDoxygen()

    #move xml results to result-dir
    if os.path.isfile('results.xml'):
        resultdir = regdir + "/results/" + d.isoformat()
        if not os.path.isdir(resultdir):
            os.mkdir (resultdir)

        subprocess.getoutput("cp -rf " + "results.xml " + resultdir)

    bailout(runAsUser)

#call main
if __name__ == "__main__":
    main(sys.argv[1:])