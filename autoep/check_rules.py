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

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__)) # Dir of this script
TABLES_DIR = SCRIPT_DIR + '/tables'
ALL_EXAMPLES_NUMBERS_TXT_FILE = TABLES_DIR + '/all-examples-numbers.txt'
ALL_EXAMPLES_LIST_TXT_FILE = TABLES_DIR + '/all-examples-list.txt'

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

TOOLS = ['clover', 'ekstazi', 'starts']

def parseArgs(argv):
    '''
    Parse the args of the script.
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('--all', help='Check all the rules', action='store_true', required=False)
    parser.add_argument('--R1', help='Check all rule R1', action='store_true', required=False)
    parser.add_argument('--R2', help='Check all rule R2', action='store_true', required=False)
    parser.add_argument('--R3', help='Check all rule R2', action='store_true', required=False)
    parser.add_argument('--R4', help='Check all rule R4', action='store_true', required=False)
    parser.add_argument('--R6', help='Check all rule R6', action='store_true', required=False)
    parser.add_argument('--R7', help='Check all rule R7', action='store_true', required=False)

    if (len(argv) == 0):
        parser.print_help()
        exit(1)
    opts = parser.parse_args(argv)
    return opts

# def extractMacroValue(macro, numbers_tex_file):
#     fr = open(numbers_tex_file, 'r')
#     lines = fr.readlines()
#     fr.close()
#     for i in range(len(lines)):
#         if lines[i].startswith('\\DefMacro{' + macro):
#             value = lines[i].split('{')[2].split('}')[0]
#     return value

# def extractMacroValueFromLineList(macro, lines):
#     for i in range(len(lines)):
#         if lines[i].startswith('\\DefMacro{' + macro):
#             value = lines[i].split('{')[2].split('}')[0]
#             return value

def extractMacroValueFromLineList(macro, macro_dict):
    return macro_dict[macro]

def checkRuleR1(macro_lines, violation_list, tools=TOOLS, \
                numbers_tex_file=ALL_EXAMPLES_NUMBERS_TXT_FILE, \
                list_tex_file=ALL_EXAMPLES_LIST_TXT_FILE):
    fr = open(list_tex_file, 'r')
    lines = fr.readlines()
    fr.close()
    for i in range(len(lines)):
        config = lines[i].split()[0]
        example_id = lines[i].strip().split()[1]
        # assertion fail
        retestall_macro = config + example_id + 'V1' + 'notoolNumOfAssertionFailTests'
        retestall_num_of_failed_tests = \
                            extractMacroValueFromLineList(retestall_macro, macro_lines)
        for tool in tools:
            tool_macro = config + example_id + 'V1' + tool + 'NumOfAssertionFailTests'
            tool_num_of_failed_tests = \
                            extractMacroValueFromLineList(tool_macro, macro_lines)
            if int(tool_num_of_failed_tests) < int(retestall_num_of_failed_tests):
                reportViolation('R1', tool, config, example_id, violation_list, 'Assertion')
        # state changes
        retestall_macro = config + example_id + 'V1' + 'notoolNumOfStateChangeTests'
        retestall_num_of_failed_tests = \
                            extractMacroValueFromLineList(retestall_macro, macro_lines)
        for tool in tools:
            tool_macro = config + example_id + 'V1' + tool + 'NumOfStateChangeTests'
            tool_num_of_failed_tests = \
                            extractMacroValueFromLineList(tool_macro, macro_lines)
            if int(tool_num_of_failed_tests) < int(retestall_num_of_failed_tests):
                reportViolation('R1', tool, config, example_id, violation_list, 'State')

def checkRuleR2(macro_lines, violation_list, tools=TOOLS, \
                numbers_tex_file=ALL_EXAMPLES_NUMBERS_TXT_FILE, \
                list_tex_file=ALL_EXAMPLES_LIST_TXT_FILE):
    fr = open(list_tex_file, 'r')
    lines = fr.readlines()
    fr.close()
    for i in range(len(lines)):
        config = lines[i].split()[0]
        example_id = lines[i].strip().split()[1]
        for version in ['V0', 'V1']:
            retestall_macro = config + example_id + version + 'notoolNumOfRunTests'
            num_of_all_tests = int(extractMacroValueFromLineList(retestall_macro, macro_lines))
            num_of_run_tests_map = {}
            for tool in tools:
                tool_macro = config + example_id + version + tool + 'NumOfRunTests'
                tool_num_of_run_tests = int(extractMacroValueFromLineList(tool_macro, \
                                                                          macro_lines))
                num_of_run_tests_map[tool] = tool_num_of_run_tests
            if list(num_of_run_tests_map.values()).count(0) == 1 and \
               list(num_of_run_tests_map.values()).count(num_of_all_tests) == len(tools) - 1:
                for tool in num_of_run_tests_map:
                    if num_of_run_tests_map[tool] == 0:
                        reportViolation('R2', tool, config, example_id, violation_list, 'Run')

def checkRuleR3(macro_lines, violation_list, tools=TOOLS, \
                numbers_tex_file=ALL_EXAMPLES_NUMBERS_TXT_FILE, \
                list_tex_file=ALL_EXAMPLES_LIST_TXT_FILE):
    fr = open(list_tex_file, 'r')
    lines = fr.readlines()
    fr.close()
    for i in range(len(lines)):
        config = lines[i].split()[0]
        example_id = lines[i].strip().split()[1]
        retestall_v0_macro = config + example_id + 'V0' + 'notoolNumOfRunTests'
        v0_num_of_all_tests = int(extractMacroValueFromLineList(retestall_v0_macro, macro_lines))
        retestall_v1_macro = config + example_id + 'V1' + 'notoolNumOfRunTests'
        v1_num_of_all_tests = int(extractMacroValueFromLineList(retestall_v1_macro, macro_lines))
        for tool in tools:
            tool_v0_macro = config + example_id + 'V0' + tool + 'NumOfRunTests'
            tool_v1_macro = config + example_id + 'V1' + tool + 'NumOfRunTests'
            tool_num_of_run_tests_on_v0_version = \
                                int(extractMacroValueFromLineList(tool_v0_macro, macro_lines))
            tool_num_of_run_tests_on_v1_version = \
                                int(extractMacroValueFromLineList(tool_v1_macro, macro_lines))
            if tool_num_of_run_tests_on_v0_version == v0_num_of_all_tests and \
               tool_num_of_run_tests_on_v1_version == v1_num_of_all_tests and \
               v1_num_of_all_tests != 0:
                reportViolation('R3', tool, config, example_id, violation_list, 'Run')

def checkRuleR4(macro_lines, violation_list, tools=TOOLS, \
                numbers_tex_file=ALL_EXAMPLES_NUMBERS_TXT_FILE, \
                list_tex_file=ALL_EXAMPLES_LIST_TXT_FILE):
    fr = open(list_tex_file, 'r')
    lines = fr.readlines()
    fr.close()
    for i in range(len(lines)):
        config = lines[i].split()[0]
        example_id = lines[i].strip().split()[1]
        for version in ['V0', 'V1']:
            retestall_macro = config + example_id + version + 'notoolNumOfRunTests'
            num_of_all_tests = int(extractMacroValueFromLineList(retestall_macro, macro_lines))
            num_of_run_tests_map = {}
            for tool in tools:
                tool_macro = config + example_id + version + tool + 'NumOfRunTests'
                tool_num_of_run_tests = int(extractMacroValueFromLineList(tool_macro, \
                                                                          macro_lines))
                num_of_run_tests_map[tool] = tool_num_of_run_tests
            if list(num_of_run_tests_map.values()).count(0) == len(tools) - 1 and \
               list(num_of_run_tests_map.values()).count(num_of_all_tests) == 1:
                for tool in num_of_run_tests_map:
                    if num_of_run_tests_map[tool] == num_of_all_tests:
                        reportViolation('R4', tool, config, example_id, violation_list, 'Run')

def checkRuleR6(macro_lines, violation_list, tools=TOOLS, \
                numbers_tex_file=ALL_EXAMPLES_NUMBERS_TXT_FILE, \
                list_tex_file=ALL_EXAMPLES_LIST_TXT_FILE):
    fr = open(list_tex_file, 'r')
    lines = fr.readlines()
    fr.close()
    for i in range(len(lines)):
        config = lines[i].split()[0]
        example_id = lines[i].strip().split()[1]
        retestall_macro = config + example_id + 'V0' + 'notoolNumOfRunTests'
        retestall_num_of_run_tests = extractMacroValueFromLineList(retestall_macro, macro_lines)
        for tool in tools:
            tool_macro = config + example_id + 'V0' + tool + 'NumOfRunTests'
            tool_num_of_run_tests = extractMacroValueFromLineList(tool_macro, macro_lines)
            if int(tool_num_of_run_tests) != int(retestall_num_of_run_tests):
                reportViolation('R6', tool, config, example_id, violation_list, 'Run')

def checkRuleR7(macro_lines, violation_list, tools=TOOLS, \
                numbers_tex_file=ALL_EXAMPLES_NUMBERS_TXT_FILE, \
                list_tex_file=ALL_EXAMPLES_LIST_TXT_FILE):
    fr = open(list_tex_file, 'r')
    lines = fr.readlines()
    fr.close()
    for i in range(len(lines)):
        config = lines[i].split()[0]
        example_id = lines[i].strip().split()[1]
        # assertion fail
        retestall_macro = config + example_id + 'V1' + 'notoolNumOfAssertionFailTests'
        retestall_num_of_failed_tests = extractMacroValueFromLineList(retestall_macro, \
                                                                      macro_lines)
        for tool in tools:
            tool_macro = config + example_id + 'V1' + tool + 'NumOfAssertionFailTests'
            tool_num_of_failed_tests = extractMacroValueFromLineList(tool_macro, macro_lines)
            if int(tool_num_of_failed_tests) > int(retestall_num_of_failed_tests):
                reportViolation('R7', tool, config, example_id, violation_list, 'Assertion')
        # state changes
        # retestall_macro = config + example_id + 'V1' + 'notoolNumOfStateChangeTests'
        # retestall_num_of_failed_tests = extractMacroValueFromLineList(retestall_macro, \
        #    macro_lines)
        # for tool in tools:
        #     tool_macro = config + example_id + 'V1' + tool + 'NumOfStateChangeTests'
        #     tool_num_of_failed_tests = extractMacroValueFromLineList(tool_macro, \
        #    macro_lines)
        #     if int(tool_num_of_failed_tests) > int(retestall_num_of_failed_tests):
        #         reportViolation('R7', tool, config, example_id, violation_list, 'State')
        # state diff than notool at version 0
        for tool in tools:
            tool_macro = config + example_id + 'V0' + tool + 'NumOfStateDiffTests'
            tool_num_of_state_diff_tests = extractMacroValueFromLineList(tool_macro, macro_lines)
            if int (tool_num_of_state_diff_tests) > 0:
                reportViolation('R7', tool, config, example_id, violation_list, 'State')

def reportViolation(rule, tool, config, example_id, violation_list, fail_type, \
                    generation_map=GENERATION_MAP, evolution_map=EVOLUTION_MAP):
    # print (rule, tool, example_id)
    gen = config.split('-')[0]
    evo = '-'.join(config.split('-')[1:])
    gen_id = generation_map[gen]
    evo_id = evolution_map[evo]
    v = (rule, gen_id, evo_id, tool, example_id, fail_type)
    for reported_v in violation_list:
        if reported_v[0] == v[0] and reported_v[1] == v[1] and reported_v[2] == v[2] and \
           reported_v[3] == v[3] and reported_v[4] == v[4]:
            return
    violation_list.append(v)
    msg = 'On configration ' + v[1] + '+' + v[2] + ', example ' + v[4] + ', ' + v[3] + \
          ' violates rule ' + v[0]
    if v[0] == 'R1' or v[0] == 'R7':
        msg += ', detected by ' + v[5] + ' diff.'
    print (msg)

if __name__ == '__main__':
    opts = parseArgs(sys.argv[1:])
    violation_list = []
    fr = open(ALL_EXAMPLES_NUMBERS_TXT_FILE, 'r')
    macro_lines = fr.readlines()
    fr.close()
    macro_dict ={}
    for i in range(len(macro_lines)):
        key = macro_lines[i].split('{')[1].split('}')[0]
        value = macro_lines[i].split('{')[2].split('}')[0]
        macro_dict[key] = value
    macro_lines = macro_dict
    if opts.all:
        checkRuleR1(macro_lines, violation_list)
        checkRuleR2(macro_lines, violation_list)
        checkRuleR3(macro_lines, violation_list)
        checkRuleR4(macro_lines, violation_list)
        checkRuleR6(macro_lines, violation_list)
        checkRuleR7(macro_lines, violation_list)
    if opts.R1:
        checkRuleR1(macro_lines, violation_list)
        exit(0)
    if opts.R2:
        checkRuleR2(macro_lines, violation_list)
        exit(0)
    if opts.R3:
        checkRuleR3(macro_lines, violation_list)
        exit(0)
    if opts.R4:
        checkRuleR4(macro_lines, violation_list)
        exit(0)
    if opts.R6:
        checkRuleR6(macro_lines, violation_list)
        exit(0)
    if opts.R7:
        checkRuleR7(macro_lines, violation_list)
        exit(0)

    if len(violation_list) == 0:
        print ('No violations detected')

    # for v in violation_list:
    #     msg = 'On configration ' + v[1] + '+' + v[2] + ', example ' + v[4] + ', ' + v[3] + \
    #           ' violates rule ' + v[0]
    #     if v[0] == 'R1' or v[0] == 'R7':
    #         msg += ', detected by ' + v[5] + ' diff.'
    #     print (msg)


