#!/usr/bin/python3

import os
import sys
import time
import subprocess as sub
import re
import shutil
import argparse
import datetime
import collections
import distutils.core

### Requires:
### 1. Java 1.7, Git >= 1.9, SVN >= 1.8, Perl >= 5.0.10
### 2. Install Defects4J and add it to the PATH. The "defects4j" command should be accessible.

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__)) # Dir of this script
DEFECTS4J_BIN = SCRIPT_DIR + '/defects4j/framework/bin/defects4j'
_DOWNLOADS_DIR = SCRIPT_DIR + '/_downloads'
_RESULTS_DIR = SCRIPT_DIR + '/_results'
INTEGRATE_BASH_SCRIPT = SCRIPT_DIR + '/integrate.sh'

LANG_FLAKY_TESTS = ['ToStringBuilderTest']
MATH_FLAKY_TESTS = ['FastMathTest', 'RandomDataTest', \
                    'ValueServerTest', 'RandomAdaptorTest', \
                    'TDistributionTest',
                    'RandomGeneratorAbstractTest', 'MersenneTwisterTest', 'Well19937cTest', \
                    'Well44497aTest', 'BitsStreamGeneratorTest', 'AbstractRandomGeneratorTest', \
                    'Well19937aTest', 'Well1024aTest', 'ISAACTest', 'Well512aTest', \
                    'Well44497bTest', 'EmpiricalDistributionTest']
TIME_FLAKY_TESTS = ['TestDateTimeZone', 'TestDateTimeFormatter', 'TestDateTimeFormat', \
                    'TestDateTimeFormatStyle', 'TestDateTimeFormatterBuilder', \
                    'TestPeriodType']

TOOLS = ['notool', 'ekstazi', 'clover', 'starts'] # 'notool' means RetestAll
#TOOLS = ['notool']

def parseArgs(argv):
    '''
    Parse the args of the script.
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', help='Run all RTS tools on all examples', \
                        action='store_true', required=False)
    parser.add_argument('--run-one', help='Run all RTS tools on one example', required=False)
    parser.add_argument('--tool', help='Specify the RTS tool', required=False)
    parser.add_argument('--same-version-twice', help='Run all examples same version twice', \
                        action='store_true', required=False)
    parser.add_argument('--same-version-twice-one', help='Run one example same version twice', \
                        required=False)
    parser.add_argument('--enable-math', help='Include commons-math examples in experiments', \
                        action='store_true', required=False)

    if (len(argv) == 0):
        parser.print_help()
        exit(1)
    opts = parser.parse_args(argv)
    return opts

def searchFile(dir_root, file_name):
    for dir_path, subpaths, files in os.walk(dir_root):
        for f in files:
            if f == file_name:
                return dir_path + '/' + f
    return None

def setD4JExamples(enable_math): # invalid examples are excluded
    examples = []
    # lang-1 to lang-27 do not compile with Java 8
    # lang-54 to lang-59 do not compile with Java 8 : enum keyword
    for i in range(28, 54):
        examples.append('lang-' + str(i))
    # time-27 does not build: 1.5
    for i in range(1, 27):
        examples.append('time-' + str(i))
    if enable_math:
        # math-1 to math-4 do not build: -javaagent fail
        for i in range(5, 105):
            examples.append('math-' + str(i))
    return examples

def cloneProject(project, example_number, defects4j_bin=DEFECTS4J_BIN, \
                 downloads_dir=_DOWNLOADS_DIR):
    if not os.path.isdir(downloads_dir + '/' + project):
        os.makedirs(downloads_dir + '/' + project)
    # if exist, delete and re-clone it
    if os.path.isdir(downloads_dir + '/' + project + '/' + project + '-' + example_number):
        shutil.rmtree(downloads_dir + '/' + project + '/' + project + '-' + example_number)
    os.chdir(downloads_dir + '/' + project)
    sub.run(defects4j_bin + ' checkout -p %s -v %sb -w %s-%s' \
            % (project.title(), example_number, project, example_number), shell=True, \
            stdout=open(os.devnull, 'w'), stderr=sub.STDOUT)

# checkout to fixed version
def checkoutToFixedVer(project, example_number, downloads_dir=_DOWNLOADS_DIR):
    os.chdir(downloads_dir + '/' + project + '/' + project + '-' + example_number)
    sub.run('git checkout D4J_%s_%s_FIXED_VERSION' \
            % (project.title(), example_number), shell=True, \
            stdout=open(os.devnull, 'w'), stderr=sub.STDOUT)

# checkout to buggy version
def checkoutToBuggyVer(project, example_number, downloads_dir=_DOWNLOADS_DIR):
    os.chdir(downloads_dir + '/' + project + '/' + project + '-' + example_number)
    sub.run('git checkout D4J_%s_%s_BUGGY_VERSION' \
            % (project.title(), example_number), shell=True, \
            stdout=open(os.devnull, 'w'), stderr=sub.STDOUT)

def integrateToolInPomFile(tool, project, example_number, version, \
                    integrate_bash_script=INTEGRATE_BASH_SCRIPT, downloads_dir=_DOWNLOADS_DIR):
    project_dir = downloads_dir + '/' + project + '/' + project + '-' + example_number
    sub.run('git checkout -- .', shell=True) # stash any previous changes on pom
    sub.run(integrate_bash_script + ' ' + project_dir + ' ' + tool, shell=True, \
            stdout=open(os.devnull, 'w'), stderr=sub.STDOUT)

def runRTSTool(tool, project, example_number, version, results_dir=_RESULTS_DIR):
    example_logs_dir = results_dir + '/' + project + '/' + project + '-' + example_number + \
                       '/' + version
    if not os.path.isdir(example_logs_dir):
        os.makedirs(example_logs_dir)
    if tool == 'notool':
        notool_log = example_logs_dir + '/notool.log'
        sub.run('mvn -Pnotoolp test -fn', shell=True, \
                stdout=open(notool_log, 'w'), stderr=sub.STDOUT)
    elif tool == 'ekstazi':
        ekstazi_log = example_logs_dir + '/ekstazi.log'
        sub.run('mvn -Pekstazip test -fn', shell=True, \
                stdout=open(ekstazi_log, 'w'), stderr=sub.STDOUT)
    elif tool == 'clover':
        clover_log = example_logs_dir + '/clover.log'
        sub.run('mvn -Pcloverp test -fn', shell=True, \
                stdout=open(clover_log, 'w'), stderr=sub.STDOUT)
    elif tool == 'starts':
        starts_log = example_logs_dir + '/starts.log'
        sub.run('mvn -Pstartsp starts:starts -fn', shell=True, \
                stdout=open(starts_log, 'w'), stderr=sub.STDOUT)
    elif tool == 'hyrts':
        hyrts_log = example_logs_dir + '/hyrts.log'
        sub.run('mvn -Phyrtsp hyrts:HyRTS -fn', shell=True, \
                stdout=open(hyrts_log, 'w'), stderr=sub.STDOUT)

# exclude some flaky tests
def excludeFlakyTestsFromTime_CommentSuite(example, flaky_tests, downloads_dir=_DOWNLOADS_DIR):
    project = example.split('-')[0]
    example_number = int(example.split('-')[1])
    repo_dir = downloads_dir + '/' + project + '/' + example
    for ft in flaky_tests:
        if ft == 'TestDateTimeZone' or ft == 'TestPeriodType':
            suite_file = repo_dir + '/src/test/java/org/joda/time/TestAll.java'
        else:
            suite_file = repo_dir + '/src/test/java/org/joda/time/format/TestAll.java'
        if not os.path.isfile(suite_file):
            continue
        fr = open(suite_file, 'r')
        lines = fr.readlines()
        fr.close()
        for i in range(len(lines)):
            if 'suite.addTest(' + ft + '.suite' in lines[i]:
                lines[i] = '//' + lines[i]
        fw = open(suite_file, 'w')
        fw.write(''.join(lines))
        fw.close()

# exclude some flaky tests
def excludeFlakyTestsFromLang_CommentSuite(example, flaky_tests, downloads_dir=_DOWNLOADS_DIR):
    project = example.split('-')[0]
    example_number = int(example.split('-')[1])
    repo_dir = downloads_dir + '/' + project + '/' + example
    for ft in flaky_tests:
        if ft == 'ToStringBuilderTest':
            suite_file = repo_dir + \
                         '/src/test/org/apache/commons/lang/builder/BuilderTestSuite.java'
        if not os.path.isfile(suite_file):
            continue
        fr = open(suite_file, 'r')
        lines = fr.readlines()
        fr.close()
        for i in range(len(lines)):
            if 'suite.addTestSuite(' + ft + '.class' in lines[i]:
                lines[i] = '//' + lines[i]
        fw = open(suite_file, 'w')
        fw.write(''.join(lines))
        fw.close()

# exclude some flaky tests
def excludeFlakyTests_DeleteFile(example, flaky_tests, downloads_dir=_DOWNLOADS_DIR):
    project = example.split('-')[0]
    example_number = int(example.split('-')[1])
    repo_dir = downloads_dir + '/' + project + '/' + example
    for ft in flaky_tests:
        ft_file = searchFile(repo_dir, ft + '.java')
        if ft_file:
            os.remove(ft_file)

# exclude some flaky tests
def excludeProjectSpecificFlakyTests(example, flaky_tests):
    # example is like: lang-20
    project = example.split('-')[0]
    example_number = int(example.split('-')[1])
    if project == 'time':
        excludeFlakyTestsFromTime_CommentSuite(example, flaky_tests)
    elif project == 'lang':
        if example_number in range(28, 42):
            excludeFlakyTests_DeleteFile(example, flaky_tests)
        elif example_number in range(42, 54):
            excludeFlakyTestsFromLang_CommentSuite(example, flaky_tests)
    elif project == 'math':
        excludeFlakyTests_DeleteFile(example, flaky_tests)

# one tool, one example
def runOneRTSToolOnOneExample(example, tool, flaky_tests, downloads_dir=_DOWNLOADS_DIR):
    # example is like: lang-20
    project = example.split('-')[0]
    example_number = example.split('-')[1]
    # clone project
    cloneProject(project, example_number)
    os.chdir(downloads_dir + '/' + project + '/' + project + '-' + example_number)
    # checkout to fixed version
    checkoutToFixedVer(project, example_number)
    # change pom file according to tool
    integrateToolInPomFile(tool, project, example_number, 'fixed')
    # exclude flaky tests
    excludeProjectSpecificFlakyTests(example, flaky_tests)
    # run rts tool, save logs
    runRTSTool(tool, project, example_number, 'fixed')
    # restore the removed test files
    sub.run('git checkout -- .', shell=True, stdout=open(os.devnull, 'w'), stderr=sub.STDOUT)
    # checkout to buggy version
    checkoutToBuggyVer(project, example_number)
    # change pom file according to tool
    integrateToolInPomFile(tool, project, example_number, 'buggy')
    # exclude flaky tests
    excludeProjectSpecificFlakyTests(example, flaky_tests)
    # run rts tool, save logs
    runRTSTool(tool, project, example_number, 'buggy')

# all tools, one example
def runAllToolsOnOneExample(example, flaky_tests=[], tools=TOOLS, \
                            lang_flaky_tests=LANG_FLAKY_TESTS, \
                            math_flaky_tests=MATH_FLAKY_TESTS, \
                            time_flaky_tests=TIME_FLAKY_TESTS, \
                            results_dir=_RESULTS_DIR):
    # example is like: lang-20
    project = example.split('-')[0]
    example_number = example.split('-')[1]
    if example.startswith('lang-'):
        flaky_tests = lang_flaky_tests
    elif example.startswith('math-'):
        flaky_tests = math_flaky_tests
    elif example.startswith('time-'):
        flaky_tests = time_flaky_tests
    # run all tools each one time
    for tool in tools:
        print ('[RTSCheck] Running ' + tool)
        runOneRTSToolOnOneExample(example, tool, flaky_tests)

# all tools, all examples
def runAllToolsOnAllExamples(examples):
    for example in examples:
        runAllToolsOnOneExample(example)

# (for R5: twice same version exp) one tool, one example
def runOneRTSToolOnOneExampleSameVersionTwice(example, tool, flaky_tests=[], \
                                              downloads_dir=_DOWNLOADS_DIR):
    # example is like: lang-20
    project = example.split('-')[0]
    example_number = example.split('-')[1]
    # clone project
    cloneProject(project, example_number)
    os.chdir(downloads_dir + '/' + project + '/' + project + '-' + example_number)
    # checkout to buggy version
    checkoutToFixedVer(project, example_number)
    # change pom file according to tool
    integrateToolInPomFile(tool, project, example_number, 'fixed')
    # exclude flaky tests
    excludeProjectSpecificFlakyTests(example, flaky_tests)
    # run rts tool, save logs
    runRTSTool(tool, project, example_number, 'fixed-once')
    # checkout to buggy version
    checkoutToFixedVer(project, example_number)
    # change pom file according to tool
    integrateToolInPomFile(tool, project, example_number, 'fixed')
    # exclude flaky tests
    excludeProjectSpecificFlakyTests(example, flaky_tests)
    # run rts tool, save logs
    runRTSTool(tool, project, example_number, 'fixed-twice')

# (for R5: twice same version exp) all tools, one example
def runAllRTSToolsOnOneExampleSameVersionTwice(example, flaky_tests=[], tools=TOOLS, \
                                               lang_flaky_tests=LANG_FLAKY_TESTS, \
                                               math_flaky_tests=MATH_FLAKY_TESTS, \
                                               time_flaky_tests=TIME_FLAKY_TESTS, \
                                               results_dir=_RESULTS_DIR):
    # example is like: lang-20
    project = example.split('-')[0]
    example_number = example.split('-')[1]
    if example.startswith('lang-'):
        flaky_tests = lang_flaky_tests
    elif example.startswith('math-'):
        flaky_tests = math_flaky_tests
    elif example.startswith('time-'):
        flaky_tests = time_flaky_tests
    for tool in tools:
        print ('[RTSCheck] Running ' + tool)
        runOneRTSToolOnOneExampleSameVersionTwice(example, tool, flaky_tests)

# (for R5: twice same version exp) all tools, all examples
def runAllRTSToolsOnAllExamplesSameVersionTwice(examples):
    for example in examples:
        runAllRTSToolsOnOneExampleSameVersionTwice(example)

if __name__ == '__main__':
    opts = parseArgs(sys.argv[1:])
    if opts.enable_math:
        enable_math = True
    else:
        enable_math = False
    if opts.run:
        examples = setD4JExamples(enable_math)
        runAllToolsOnAllExamples(examples)
        exit(0)
    elif opts.run_one:
        example = opts.run_one
        runAllToolsOnOneExample(example)
        exit(0)
    # for same version twice exp
    elif opts.same_version_twice:
        examples = setD4JExamples(enable_math)
        runAllRTSToolsOnAllExamplesSameVersionTwice(examples)
        exit(0)
    # for same version twice exp
    elif opts.same_version_twice_one:
        example = opts.same_version_twice_one
        runAllRTSToolsOnOneExampleSameVersionTwice(example)
        exit(0)
