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
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__)) # Dir of this script
TABLES_DIR = SCRIPT_DIR + '/tables'
RUN_FIXED_THEN_BUGGY_NUMBERS_TEX_FILE = TABLES_DIR + '/defectsep-fixed-buggy-numbers.tex'
RUN_FIXED_THEN_BUGGY_TABLE_TEX_FILE = TABLES_DIR + '/defectsep-fixed-buggy-table.tex'
RUN_FIXED_TWICE_NUMBERS_TEX_FILE = TABLES_DIR + '/defectsep-fixed-version-twice-numbers.tex'
RUN_FIXED_TWICE_TABLE_TEX_FILE = TABLES_DIR + '/defectsep-fixed-version-twice-table.tex'

_RESULTS_DIR = SCRIPT_DIR + '/_results'
#_RESULTS_DIR = SCRIPT_DIR + '/../../run-defects4j/_results'
PLOTS_DIR = SCRIPT_DIR + '/plots'

PROJECTS = ['lang', 'time', 'math']
TOOLS = ['notool', 'ekstazi', 'clover', 'starts'] # 'notool' means RetestAll

def parseArgs(argv):
    '''
    Parse the args of the script.
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('--all', help='Generate all tables', \
                        action='store_true', required=False)
    parser.add_argument('--plot', help='Plot efficiency report', \
                        action='store_true', required=False)

    if (len(argv) == 0):
        parser.print_help()
        exit(1)
    opts = parser.parse_args(argv)
    return opts

def setD4JExamples():
    examples = []
    # lang-1 to lang-27 do not compile with Java 8
    # lang-54 to lang-59 do not compile with Java 8 : enum keyword
    for i in range(28, 54):
        examples.append('lang-' + str(i))
    # time-27 does not build: 1.5
    for i in range(1, 27):
        examples.append('time-' + str(i))
    # math-1 to math-4 do not build: -javaagent fail
    for i in range(5, 105):
        examples.append('math-' + str(i))
    return examples

def extractNumOfRunAndFailedTests(log):
    fr = open(log, 'r')
    lines = fr.readlines()
    fr.close()
    num_of_run_tests = 0
    num_of_failed_tests = 0
    num_of_error_tests = 0
    for i in range(len(lines)):
        if lines[i].startswith('Tests run: ') and 'Time elapsed:' not in lines[i]:
            num_of_run_tests = int(lines[i].split(',')[0].split()[-1])
            num_of_failed_tests = int(lines[i].split(',')[1].split()[-1])
            num_of_error_tests = int(lines[i].split(',')[2].split()[-1])
    return num_of_run_tests, num_of_failed_tests + num_of_error_tests

def extractExecTime(log):
    fr = open(log, 'r')
    lines = fr.readlines()
    fr.close()
    for i in range(len(lines)):
        if lines[i].startswith('[INFO] Total time: '):
            if lines[i].strip().endswith('s'):
                exec_time = float(lines[i].split()[-2])
            elif lines[i].strip().endswith('min'):
                exec_time = float(lines[i].split()[-2].split(':')[0]) * 60 + \
                            float(lines[i].split()[-2].split(':')[1])
    return round(exec_time, 2)

def genFixedThenBuggyNumbers(examples, projects=PROJECTS, tools=TOOLS, \
                             results_dir=_RESULTS_DIR, \
                             numbers_tex_file=RUN_FIXED_THEN_BUGGY_NUMBERS_TEX_FILE):
    lines = ''
    defectcheck_total_time = 0
    acc_time_dict = {}
    for project in projects:
        if not os.path.isdir(results_dir + '/' + project):
            continue
        acc_time_dict[project] = {}
        for tool in tools:
            acc_time_dict[project][tool] = 0
    defectcheck_total_number_of_tests = 0
    for ex in examples:
        project = ex.split('-')[0]
        example_number = ex.split('-')[1]
        example_id = project + example_number # 'lang1'
        example_dir = results_dir + '/' + project + '/' + ex
        if not os.path.isdir(example_dir):
            continue
        # num of run and failed tests
        for tool in tools:
            buggy_dir = example_dir + '/buggy'
            if not os.path.isdir(buggy_dir):
                continue
            log = buggy_dir + '/' + tool + '.log'
            num_of_run_tests, num_of_failed_tests = extractNumOfRunAndFailedTests(log)
            exec_time = extractExecTime(log)
            acc_time_dict[project][tool] += exec_time
            lines += '\\DefMacro{' + example_id + tool + 'NumOfRunTestsExcludeFlaky}{' \
                     + str(num_of_run_tests) + '}\n'
            lines += '\\DefMacro{' + example_id + tool + 'NumOfFailedTestsExcludeFlaky}{' \
                     + str(num_of_failed_tests) + '}\n'
            # fixed version
            fixed_dir = example_dir + '/fixed'
            if not os.path.isdir(fixed_dir):
                continue
            log = fixed_dir + '/' + tool + '.log'
            num_of_run_tests, num_of_failed_tests = extractNumOfRunAndFailedTests(log)
            lines += '\\DefMacro{' + example_id + tool + 'NumOfRunTestsFixedExcludeFlaky}{' \
                     + str(num_of_run_tests) + '}\n'
            lines += '\\DefMacro{' + example_id + tool + 'NumOfFailedTestsFixedExcludeFlaky}{' \
                     + str(num_of_failed_tests) + '}\n'
            # count DefectCheck num of tests
            if tool == 'notool':
                defectcheck_total_number_of_tests += num_of_run_tests
            exec_time = extractExecTime(log)
            acc_time_dict[project][tool] += exec_time
    for project in projects:
        if not os.path.isdir(results_dir + '/' + project):
            continue
        for tool in tools:
            defectcheck_total_time += acc_time_dict[project][tool]
            lines += '\\DefMacro{' + project + tool + 'AccExecTime}{' + \
                     '{0:.2f}'.format(acc_time_dict[project][tool]) + '}\n'
    lines += '\\DefMacro{DefectCheckTotalTime}{' + str(defectcheck_total_time) + '}\n'
    lines += '\\DefMacro{DefectCheckTotalNumOfTests}{' + \
             str(defectcheck_total_number_of_tests) + '}\n'
    fw = open(numbers_tex_file, 'w')
    fw.write(lines)
    fw.close()

def genFixedThenBuggyTable(examples, tools=TOOLS, results_dir=_RESULTS_DIR, \
                           table_tex_file=RUN_FIXED_THEN_BUGGY_TABLE_TEX_FILE):
    table_lines = ''
    table_lines += "%% Automatically generated by gen_tables.py\n"
    table_lines += "\\onecolumn\n"
    table_lines += "\\begin{small}\n"
    table_lines += "\\begin{longtable}{l|rr|rr|rr|rr}\n"
    table_lines += "\\caption{\\TableCaptionDForJExperimentExcludeFlaky} \\\\\n"
    table_lines += "\\toprule\n"
    table_lines += "\\multirow{2}{*}{\\TableHeadExampleId} & \\multicolumn{2}{c}{\\TableHeadNotool} & \\multicolumn{2}{c}{\\TableHeadEkstazi} & \\multicolumn{2}{c}{\\TableHeadClover} & \\multicolumn{2}{c}{\\TableHeadStarts} \\\\\n"
    table_lines += " & \\TableHeadNumOfRunTests & \\TableHeadNumOfFailedTests & \\TableHeadNumOfRunTests & \\TableHeadNumOfFailedTests & \\TableHeadNumOfRunTests & \\TableHeadNumOfFailedTests & \\TableHeadNumOfRunTests & \\TableHeadNumOfFailedTests \\\\\n"
    table_lines += "\\midrule\n"
    total_num_of_pass_fail_violations = 0
    for example in examples:
        project = example.split('-')[0]
        example_dir = results_dir + '/' + project + '/' + example
        if not os.path.isdir(example_dir):
            continue
        buggy_dir = example_dir + '/buggy'
        if not os.path.isdir(buggy_dir):
            continue
        example_id = example.replace('-', '')
        table_lines +=  example
        for tool in tools:
            table_lines += ' & \\UseMacro{' + example_id + tool + 'NumOfRunTestsExcludeFlaky}'
            table_lines += ' & \\UseMacro{' + example_id + tool + 'NumOfFailedTestsExcludeFlaky}'
        table_lines += ' \\\\\n'
    table_lines += "\\bottomrule\n"
    table_lines += "\\end{longtable}\n"
    table_lines += "\\end{small}\n"
    fw = open(table_tex_file, 'w')
    fw.write(table_lines)
    fw.close()

# (for R5: same version twice experiment)
def genFixedTwiceNumbers(examples, tools=TOOLS, results_dir=_RESULTS_DIR, \
                         numbers_tex_file=RUN_FIXED_TWICE_NUMBERS_TEX_FILE):
    lines = ''
    for ex in examples:
        project = ex.split('-')[0]
        example_number = ex.split('-')[1]
        example_id = project + example_number # 'lang1'
        example_dir = results_dir + '/' + project + '/' + ex
        if not os.path.isdir(example_dir):
            continue
        for version in ['fixed-once', 'fixed-twice']:
            version_dir = example_dir + '/' + version
            if not os.path.isdir(version_dir):
                continue
            for tool in tools:
                log = version_dir + '/' + tool + '.log'
                num_of_run_tests, num_of_failed_tests = extractNumOfRunAndFailedTests(log)
                lines += '\\DefMacro{' + example_id + tool + version.split('-')[1] \
                         + 'NumOfRunTests}{' + str(num_of_run_tests) + '}\n'
    fw = open(numbers_tex_file, 'w')
    fw.write(lines)
    fw.close()

# (for R5: same version twice experiment)
def genFixedTwiceTable(examples, tools=TOOLS, results_dir=_RESULTS_DIR, \
                       table_tex_file=RUN_FIXED_TWICE_TABLE_TEX_FILE):
    table_lines = ''
    table_lines += "%% Automatically generated by gen_tables.py\n"
    table_lines += "\\onecolumn\n"
    table_lines += "\\begin{small}\n"
    table_lines += "\\begin{longtable}{l|rr|rr|rr|rr}\n"
    table_lines += "\\caption{\\TableCaptionDForJExperimentSameVersionTwice} \\\\\n"
    table_lines += "\\toprule\n"
    table_lines += "\\multirow{2}{*}{\\TableHeadExampleId} & \\multicolumn{2}{c}{\\TableHeadNotool} & \\multicolumn{2}{c}{\\TableHeadEkstazi} & \\multicolumn{2}{c}{\\TableHeadClover} & \\multicolumn{2}{c}{\\TableHeadStarts} \\\\\n"
    table_lines += " & \\TableHeadNumOfRunTestsOnce & \\TableHeadNumOfRunTestsTwice & \\TableHeadNumOfRunTestsOnce & \\TableHeadNumOfRunTestsTwice & \\TableHeadNumOfRunTestsOnce & \\TableHeadNumOfRunTestsTwice & \\TableHeadNumOfRunTestsOnce & \\TableHeadNumOfRunTestsTwice \\\\\n"
    table_lines += "\\midrule\n"
    total_num_of_precision_violations = 0
    for example in examples:
        project = example.split('-')[0]
        example_dir = results_dir + '/' + project + '/' + example
        if not os.path.isdir(example_dir):
            continue
        fixed_once_dir = example_dir + '/fixed-once'
        if not os.path.isdir(fixed_once_dir):
            continue
        example_id = example.replace('-', '')
        table_lines +=  example
        for tool in tools:
            table_lines += ' & \\UseMacro{' + example_id + tool + 'onceNumOfRunTests}' + \
                           ' & \\UseMacro{' + example_id + tool + 'twiceNumOfRunTests}'
        table_lines += ' \\\\\n'
    table_lines += "\\bottomrule\n"
    table_lines += "\\end{longtable}\n"
    table_lines += "\\end{small}\n"
    fw = open(table_tex_file, 'w')
    fw.write(table_lines)
    fw.close()

# for efficiency plot
def extractExecTimeFromNumbersTexFile(project, tool, \
                                      numbers_tex_file=RUN_FIXED_THEN_BUGGY_NUMBERS_TEX_FILE):
    fr = open(numbers_tex_file, 'r')
    lines = fr.readlines()
    fr.close()
    for i in range(len(lines)):
        if lines[i].startswith('\\DefMacro{' + project + tool + 'AccExecTime}'):
            exec_time = float(lines[i].split('{')[-1].split('}')[0])
            break
    return exec_time

# for efficiency plot
def plotAccExecTime(plots_dir=PLOTS_DIR):
    colors = ['black', 'mediumblue', 'dodgerblue', 'skyblue']
    tools = ['notool', 'clover', 'ekstazi', 'starts']
    # Construct data frame
    projects = ['lang', 'math', 'time']
    matrix = []
    for project in projects:
        row = []
        for tool in tools:
            exec_time = extractExecTimeFromNumbersTexFile(project, tool)
            row.append(exec_time)
        matrix.append(row)
    row_names = [p.title() for p in projects]
    column_names = ['RetestAll', 'Clover', 'Ekstazi', 'STARTS']
    df = pd.DataFrame(matrix, index=row_names, columns=column_names)
    # Plot
    matplotlib.rcParams.update({'font.size': 15})
    #params = {'legend.fontsize': 15}
    #plt.rcParams.update(params)
    f, axis = plt.subplots(2, 1, sharex=True)
    df.plot(kind='bar', ax=axis[0], width=0.5, color=colors, label=tool)
    df.plot(kind='bar', ax=axis[1], width=0.5, color=colors, label=tool)
    axis[0].set_ylim(25000, 45000)
    axis[1].set_ylim(0, 6000)
    axis[0].set_ylabel('Time (s)')
    #axis[0].legend().set_visible(False)
    axis[1].legend().set_visible(False)
    axis[0].spines['bottom'].set_visible(False)
    axis[1].spines['top'].set_visible(False)
    axis[0].xaxis.tick_top()
    axis[0].tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
    axis[1].xaxis.tick_bottom()
    for tick in axis[1].get_xticklabels():
        tick.set_rotation(15)
    d = .015
    kwargs = dict(transform=axis[0].transAxes, color='k', clip_on=False)
    # breaking slashes
    axis[0].plot((-d,+d),(-d,+d), **kwargs)
    axis[0].plot((1-d,1+d),(-d,+d), **kwargs)
    kwargs.update(transform=axis[1].transAxes)
    axis[1].plot((-d,+d),(1-d,1+d), **kwargs)
    axis[1].plot((1-d,1+d),(1-d,1+d), **kwargs)
    # adjust layout
    plt.subplots_adjust(top=0.95, bottom=0.12, left=0.18)
    #plt.xlabel('projects')
    fig = plt.gcf()
    fig.savefig(plots_dir + '/defect-time-plot.eps')
    #plt.show()
    plt.clf() # MUST CLEAN

if __name__ == '__main__':
    opts = parseArgs(sys.argv[1:])
    if opts.all:
        examples = setD4JExamples()
        sub.run('mkdir -p ' + TABLES_DIR, shell=True)
        genFixedThenBuggyNumbers(examples)
        genFixedThenBuggyTable(examples)
        genFixedTwiceNumbers(examples)
        genFixedTwiceTable(examples)
        exit(0)
    elif opts.plot:
        sub.run('mkdir -p ' + PLOTS_DIR, shell=True)
        plotAccExecTime()
        exit(0)

