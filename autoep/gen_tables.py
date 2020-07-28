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
_RESULTS_DIR = SCRIPT_DIR + '/_results'
TABLES_DIR = SCRIPT_DIR + '/tables'
GEN_EVO_NUMBERS_TEX_FILE = TABLES_DIR + '/all-examples-numbers.tex'
ALL_EXAMPLES_NUMBERS_TXT_FILE = TABLES_DIR + '/all-examples-numbers.txt'
ALL_EXAMPLES_LIST_TXT_FILE = TABLES_DIR + '/all-examples-list.txt'
GEN_EVO_TABLE_TEX_FILE = TABLES_DIR + '/gen-evo-table.tex'
ALL_EXAMPLES_TABLE_TEX_FILE = TABLES_DIR + '/all-examples-table.tex'

GENERATION_CONSTRAINTS = ['default', 'pullupmethod', 'pushdownmethod', 'pullupfield', \
                          'movemethod', 'renameclass', 'renamemethod', 'renamefield', \
                          'addparameter', 'encapsulatefield']
EVOLUTIONS = ['add-extends', 'copy-field', 'copy-field-and-replace', 'copy-method', \
              'copy-method-and-replace', 'next-program-in-order', 'increase-constants', \
              'remove-extends', 'remove-method']

GENERATION_MAP = collections.OrderedDict({'default': 'JD1',
                                          'pullupmethod': 'JD2',
                                          'pushdownmethod': 'JD3',
                                          'pullupfield': 'JD4',
                                          'movemethod': 'JD5',
                                          'renameclass': 'JD6',
                                          'renamemethod': 'JD7',
                                          'renamefield': 'JD8',
                                          'addparameter': 'JD9',
                                          'encapsulatefield': 'JD10'})

EVOLUTION_MAP = collections.OrderedDict({'add-extends': 'E1',
                                         'copy-field': 'E2',
                                         'copy-field-and-replace': 'E3',
                                         'copy-method': 'E4',
                                         'copy-method-and-replace': 'E5',
                                         'next-program-in-order': 'E6',
                                         'increase-constants': 'E7',
                                         'remove-extends': 'E8',
                                         'remove-method': 'E9'})

TOOLS = ['notool', 'ekstazi', 'clover', 'starts']

def parseArgs(argv):
    '''
    Parse the args of the script.
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('--all', help='Generate all tables', \
                        action='store_true', required=False)
    if (len(argv) == 0):
        parser.print_help()
        exit(1)
    opts = parser.parse_args(argv)
    return opts

# Extract the number of tests run from a log file
def extractNumOfTestRuns(log):
    f = open(log, 'r')
    lines = f.readlines()
    f.close()
    num_of_test_runs = '0'
    for i in range(len(lines)):
        if lines[i].startswith('Tests run:') and \
           'Time elapsed:' not in lines[i]:
            num_of_test_runs = lines[i].split(',')[0].split(' ')[-1]
    return num_of_test_runs

# get the list of failed tests in terms of assertion failures, from a log file
def extractListOfAssertionFailingTestsFromLog(log):
    f = open(log, 'r')
    lines = f.readlines()
    f.close()
    failing_tests_list = []
    for i in range(len(lines)):
        if lines[i].startswith('Running Package_0.TestGroup'):
            test_name = lines[i].strip().split('.')[1]
            for j in range(i+1, len(lines)):
                if lines[j].startswith('Assert: null'):
                    actual_value = lines[j].strip().split(' ')[-1]
                    if actual_value == 'null':
                        pass
                    else:
                        failing_tests_list.append(test_name)
                        break
                elif lines[j].startswith('Assert: not null'):
                    actual_value = lines[j].strip().split(' ')[-1]
                    if not actual_value == 'null':
                        pass
                    else:
                        failing_tests_list.append(test_name)
                        break
                elif lines[j].startswith('Assert: ') and '==' in lines[j]:
                    actual_value = lines[j].strip().split(' ')[-2]
                    expected_value = lines[j].strip().split(' ')[-1]
                    if expected_value == actual_value:
                        pass
                    else:
                        failing_tests_list.append(test_name)
                        break
                else:
                    break
    return failing_tests_list

# Extract the dict {test_name: state_obj_list} from a log file
def extractDictOfObjectStates(log, exclude_clover_sniffer=True):
    f = open(log, 'r')
    lines = f.readlines()
    f.close()
    objects_dict = collections.OrderedDict({})
    for i in range(len(lines)):
        if lines[i].startswith('===== Package_0.TestGroup'):
            test_name = lines[i].strip().split('.')[1]
            objects_dict[test_name] = []
            j = i-1
            while j >= 0:
                if lines[j].startswith('OBJECT:'):
                    obj = lines[j].strip()
                    if exclude_clover_sniffer:
                        # prevent clover sniffer from disturbing comparing states
                        if '__CLR4_2_0_TEST_NAME_SNIFFER=UNK:com_atlassian_clover.TestNameSniffer' in lines[j]:
                            num_of_objects = int(lines[j].strip().split('#')[1].split(' ')[0])
                            old_num_of_objects = str(num_of_objects)
                            new_num_of_objects = str(num_of_objects - 1)
                            obj = obj.replace('#' + old_num_of_objects, '#' + new_num_of_objects)
                            obj = obj.replace('__CLR4_2_0_TEST_NAME_SNIFFER=UNK:com_atlassian_clover.TestNameSniffer, ', '').replace('__CLR4_2_0_TEST_NAME_SNIFFER=UNK:com_atlassian_clover.TestNameSniffer', '')
                    objects_dict[test_name].append(obj)
                    j -= 1
                else:
                    break
    return objects_dict

# get the list of tests whose states change between two versions from two versions' log files
def extractStateChangingTestsFromTwoVersion(tool, gen, evo, example, results_dir=_RESULTS_DIR):
    states_changing_tests_list = []
    # Read version 0 and version 1 logs.
    v0_log = results_dir + '/' + gen + '-' + evo + '/' + example + '/0/' + tool + '.log'
    v1_log = results_dir + '/' + gen + '-' + evo + '/' + example + '/1/' + tool + '.log'
    v0_states_dict = extractDictOfObjectStates(v0_log)
    v1_states_dict = extractDictOfObjectStates(v1_log)
    for test_name in v0_states_dict.keys():
        if not test_name in v1_states_dict: # the tool does not select this test in version 1
            continue
        if not v0_states_dict[test_name] == v1_states_dict[test_name]:
            states_changing_tests_list.append(test_name)
    return states_changing_tests_list

def extractStateDiffFromNotoolTests_V0(tool, gen, evo, example, results_dir=_RESULTS_DIR):
    state_diff_tests_list = []
    tool_log = results_dir + '/' + gen + '-' + evo + '/' + example + '/0/' + \
               tool + '.log'
    notool_log = results_dir + '/' + gen + '-' + evo + '/' + example + '/0/' + \
                 'notool.log'
    tool_obj_dict = extractDictOfObjectStates(tool_log)
    notool_obj_dict = extractDictOfObjectStates(notool_log)
    for test_name in notool_obj_dict:
        if tool_obj_dict[test_name] != notool_obj_dict[test_name]:
            state_diff_tests_list.append(test_name)
    return state_diff_tests_list

def extractStateDiffFromNotoolTests_V1(tool, gen, evo, example, results_dir=_RESULTS_DIR):
    state_diff_tests_list = []
    notool_state_changing_tests_list = extractStateChangingTestsFromTwoVersion('notool', gen, \
                                                                               evo, example)
    tool_log = results_dir + '/' + gen + '-' + evo + '/' + example + '/1/' + \
               tool + '.log'
    notool_log = results_dir + '/' + gen + '-' + evo + '/' + example + '/1/' + \
                 'notool.log'
    tool_obj_dict = extractDictOfObjectStates(tool_log)
    notool_obj_dict = extractDictOfObjectStates(notool_log)
    for test_name in notool_state_changing_tests_list:
        if test_name not in tool_obj_dict:
            tool_obj_dict[test_name] = 'Not Run'
        if tool_obj_dict[test_name] != notool_obj_dict[test_name]:
            state_diff_tests_list.append(test_name)
    return state_diff_tests_list

def isLineInV0V1SameFile(line):
    fr = open(SCRIPT_DIR + '/v0_v1_same_list.txt', 'r')
    prog_lines = fr.readlines()
    for i in range(len(prog_lines)):
        if line in prog_lines[i]:
            return True
    return False

def genAllExamplesNumbers(gens=GENERATION_CONSTRAINTS, evos=EVOLUTIONS, tools=TOOLS, \
                          results_dir=_RESULTS_DIR, \
                          gen_evo_numbers_tex_file=GEN_EVO_NUMBERS_TEX_FILE, \
                          all_examples_list_txt_file=ALL_EXAMPLES_LIST_TXT_FILE, \
                          all_examples_numbers_txt_file=ALL_EXAMPLES_NUMBERS_TXT_FILE, \
                          generation_map=GENERATION_MAP, evolution_map=EVOLUTION_MAP):
    lines = ''
    numbers_txt_lines = ''
    list_txt_lines = ''
    for gen in gens:
        for evo in evos:
            if not os.path.isdir(results_dir + '/' + gen + '-' + evo): # no valid base programs
                lines += '\\DefMacro{' + gen + evo + 'NumOfEvolvedPrograms}{0}\n'
                lines += '\\DefMacro{' + gen + evo + 'NumOfValidEvolvedPrograms}{0}\n'
                lines += '\\DefMacro{' + generation_map[gen] + evolution_map[evo] + \
                         'NumOfEvolvedPrograms}{0}\n'
                lines += '\\DefMacro{' + generation_map[gen] + evolution_map[evo] + \
                         'NumOfValidEvolvedPrograms}{0}\n'
                if evo == 'next-program-in-order':
                    lines += '\\DefMacro{' + generation_map[gen] + 'NumOfBasePrograms}{0}\n'
                continue
            examples = sorted(os.listdir(results_dir + '/' + gen + '-' + evo))
            if evo == 'next-program-in-order':
                base_programs = set()
                for example in examples:
                    base_programs.add(example.split('-')[0])
                lines += '\\DefMacro{' + gen + 'NumOfBasePrograms}{' + \
                         str(len(base_programs)) + '}\n'
                lines += '\\DefMacro{' + generation_map[gen] + 'NumOfBasePrograms}{' + \
                         str(len(base_programs)) + '}\n'
            lines += '\\DefMacro{' + gen + evo + 'NumOfEvolvedPrograms}{' + \
                         str(len(examples)) + '}\n'
            lines += '\\DefMacro{' + generation_map[gen] + evolution_map[evo] + \
                         'NumOfEvolvedPrograms}{' + str(len(examples)) + '}\n'
            invalid_examples = []
            for example in examples:
                # --------- just for a test
                # prog_line = gen + '-' + evo + '/program0/' + example
                # if not isLineInV0V1SameFile(prog_line):
                #     continue
                # print ('Match: ' + prog_line)
                # ---------
                # if gen != 'renameclass' or evo != 'next-program-in-order':
                #    continue
                # ---------
                list_txt_lines += gen + '-' + evo + ' ' + example + '\n'
                for version in ['0', '1']:
                    for tool in tools:
                        log_file = results_dir + '/' + gen + '-' + evo + '/' + example + '/' + \
                                   version + '/' + tool + '.log'
                        if version == '1' and tool == 'notool' and \
                           extractNumOfTestRuns(log_file) == '0':
                            invalid_examples.append(example)
                        num_of_tests_run = extractNumOfTestRuns(log_file)
                        num_of_assertion_failing_tests = \
                                        len(extractListOfAssertionFailingTestsFromLog(log_file))
                        num_of_state_changing_tests = \
                            len(extractStateChangingTestsFromTwoVersion(tool, gen, evo, example))
                        if version == '0':
                            v0_num_of_state_diff_tests = \
                                len(extractStateDiffFromNotoolTests_V0(tool, gen, evo, example))
                            numbers_txt_lines += '\\DefMacro{' + gen + '-' + evo + example + \
                                    'V' + str(version) + tool + 'NumOfStateDiffTests}{' + \
                                    str(v0_num_of_state_diff_tests) + '}\n'
                        if version == '1':
                            v1_num_of_state_diff_tests = \
                                len(extractStateDiffFromNotoolTests_V1(tool, gen, evo, example))
                            numbers_txt_lines += '\\DefMacro{' + gen + '-' + evo + example + \
                                    'V' + str(version) + tool + 'NumOfStateDiffTests}{' + \
                                    str(v1_num_of_state_diff_tests) + '}\n'
                        numbers_txt_lines += '\\DefMacro{' + gen + '-' + evo + example + 'V' + \
                          str(version) + tool + 'NumOfRunTests}{' + str(num_of_tests_run) + '}\n'
                        numbers_txt_lines += '\\DefMacro{' + gen + '-' + evo + example + 'V' + \
                          str(version) + tool + 'NumOfAssertionFailTests}{' + \
                                         str(num_of_assertion_failing_tests) + '}\n'
                        numbers_txt_lines += '\\DefMacro{' + gen + '-' + evo + example + 'V' + \
                                         str(version) + tool + 'NumOfStateChangeTests}{' + \
                                         str(num_of_state_changing_tests) + '}\n'
                
            lines += '\\DefMacro{' + gen + evo + 'NumOfInvalidEvolvedPrograms}{' + \
                     str(len(invalid_examples)) + '}\n'
            lines += '\\DefMacro{' + gen + evo + 'NumOfValidEvolvedPrograms}{' + \
                     str(len(examples) - len(invalid_examples)) + '}\n'
            lines += '\\DefMacro{' + generation_map[gen] + evolution_map[evo] + \
                     'NumOfInvalidEvolvedPrograms}{' + str(len(invalid_examples)) + '}\n'
            lines += '\\DefMacro{' + generation_map[gen] + evolution_map[evo] + \
                     'NumOfValidEvolvedPrograms}{' + \
                     str(len(examples) - len(invalid_examples)) + '}\n'
    fw = open(gen_evo_numbers_tex_file, 'w')
    fw.write(lines)
    fw.close()
    fw = open(all_examples_numbers_txt_file, 'w')
    fw.write(numbers_txt_lines)
    fw.close()
    fw = open(all_examples_list_txt_file, 'w')
    fw.write(list_txt_lines)
    fw.close()

def genAutoEPGenEvoTable(gens=GENERATION_CONSTRAINTS, evos=EVOLUTIONS, \
                         generation_map=GENERATION_MAP, evolution_map=EVOLUTION_MAP, \
                         gen_evo_table_tex_file=GEN_EVO_TABLE_TEX_FILE):
    lines = ''
    lines += "% Auto generated by gen_tables.py\n"
    lines += "\\begin{table*}\n"
    lines += "\\begin{center}\n"
    lines += "\\caption{\\TCaptionGenEvoMatrix}\n"
    lines += "\\vspace{-5pt}\n"
    lines += "\\begin{tabular}{lr|rr|rr|rr|rr|rr|rr|rr|rr|rr}\n"
    lines += "\\toprule\n"
    lines += "\\multirow{2}{*}{} & "
    lines += "\\multirow{2}{*}{\TBaseNumOfPrograms} & "
    for i in range(len(evos)):
        evo = evos[i]
        if i < len(evos) - 1:
            lines += "\\multicolumn{2}{c}{\\textbf{" + evolution_map[evo] + "}} & "
        else:
            lines += "\\multicolumn{2}{c}{\\textbf{" + evolution_map[evo] + "}} \\\\\n"
    lines += "\\cmidrule(rr){3-4} \\cmidrule(rr){5-6} \\cmidrule(rr){7-8} \\cmidrule(rr){9-10} \\cmidrule(rr){11-12} \\cmidrule(rr){13-14} \\cmidrule(rr){15-16} \\cmidrule(rr){17-18} \\cmidrule(rr){19-20}\n"
    lines += " & "
    lines += " & "
    for i in range(len(evos)):
        evo = evos[i]
        if i < len(evos) - 1:
            lines += "\\sGenEvolProgs & \\sGenEvolProgsCompl & "
        else:
            lines += "\\sGenEvolProgs & \\sGenEvolProgsCompl \\\\\n"
    lines += "\\midrule\n"
    for i in range(len(gens)):
        gen = gens[i]
        lines += "\\textbf{" + generation_map[gen] + "} & "
        lines += "\\UseMacro{" + generation_map[gen] + "NumOfBasePrograms} & "
        for j in range(len(evos)):
            evo = evos[j]
            if j < len(evos) - 1:
                lines += "\\UseMacro{" + generation_map[gen] + evolution_map[evo] + \
                         "NumOfEvolvedPrograms} & \\UseMacro{" + generation_map[gen] + \
                         evolution_map[evo] + "NumOfValidEvolvedPrograms} &"
            else:
                lines += "\\UseMacro{" + generation_map[gen] + evolution_map[evo] + \
                      "NumOfEvolvedPrograms} & \\UseMacro{" + generation_map[gen] + \
                      evolution_map[evo] + "NumOfValidEvolvedPrograms} \\\\\n"
    lines += "\\bottomrule\n"
    lines += "\\end{tabular}\n"
    lines += "\\end{center}\n"
    lines += "\\end{table*}\n"
    fw = open(gen_evo_table_tex_file, 'w')
    fw.write(lines)
    fw.close()

if __name__ == '__main__':
    opts = parseArgs(sys.argv[1:])
    if opts.all:
        sub.run('mkdir -p ' + TABLES_DIR, shell=True)
        genAllExamplesNumbers()
        exit(0)

