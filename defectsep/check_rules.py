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
RUN_FIXED_THEN_BUGGY_TABLE = SCRIPT_DIR + '/tables/defectsep-fixed-buggy-table.tex'
RUN_FIXED_THEN_BUGGY_NUMBERS = SCRIPT_DIR + '/tables/defectsep-fixed-buggy-numbers.tex'
RUN_FIXED_TWICE_TABLE = SCRIPT_DIR + '/tables/defectsep-fixed-version-twice-table.tex'
RUN_FIXED_TWICE_NUMBERS = SCRIPT_DIR + '/tables/defectsep-fixed-version-twice-numbers.tex'

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
    parser.add_argument('--R5', help='Check all rule R5', action='store_true', required=False)
    parser.add_argument('--R6', help='Check all rule R6', action='store_true', required=False)
    parser.add_argument('--R7', help='Check all rule R7', action='store_true', required=False)

    if (len(argv) == 0):
        parser.print_help()
        exit(1)
    opts = parser.parse_args(argv)
    return opts

def extractMacroValue(macro, numbers_tex_file):
    fr = open(numbers_tex_file, 'r')
    lines = fr.readlines()
    fr.close()
    for i in range(len(lines)):
        if lines[i].startswith('\\DefMacro{' + macro):
            value = lines[i].split('{')[2].split('}')[0]
    return value

def checkRuleR1(violation_list, tools=TOOLS):
    checkRuleR1OnFixedVersion(violation_list, tools=TOOLS)
    checkRuleR1OnBuggyVersion(violation_list, tools=TOOLS)

def checkRuleR1OnBuggyVersion(violation_list, tools=TOOLS, \
                              numbers_tex_file=RUN_FIXED_THEN_BUGGY_NUMBERS, \
                              table_tex_file=RUN_FIXED_THEN_BUGGY_TABLE):
    fr = open(table_tex_file, 'r')
    lines = fr.readlines()
    fr.close()
    for i in range(len(lines)):
        if ' & ' in lines[i] and '\\UseMacro{' in lines[i] and lines[i].strip().endswith('\\'):
            example_id = lines[i].split(' & ')[0]
            retestall_macro = example_id.replace('-', '') + 'notoolNumOfFailedTestsExcludeFlaky'
            retestall_num_of_failed_tests = extractMacroValue(retestall_macro, numbers_tex_file)
            for tool in tools:
                tool_macro = example_id.replace('-', '') + tool + 'NumOfFailedTestsExcludeFlaky'
                tool_num_of_failed_tests = extractMacroValue(tool_macro, numbers_tex_file)
                if int(tool_num_of_failed_tests) < int(retestall_num_of_failed_tests):
                    reportViolation('R1', tool, example_id, violation_list)

def checkRuleR1OnFixedVersion(violation_list, tools=TOOLS, \
                              numbers_tex_file=RUN_FIXED_THEN_BUGGY_NUMBERS, \
                              table_tex_file=RUN_FIXED_THEN_BUGGY_TABLE):
    fr = open(table_tex_file, 'r')
    lines = fr.readlines()
    fr.close()
    for i in range(len(lines)):
        if ' & ' in lines[i] and '\\UseMacro{' in lines[i] and lines[i].strip().endswith('\\'):
            example_id = lines[i].split(' & ')[0]
            retestall_macro = example_id.replace('-', '') + \
                              'notoolNumOfFailedTestsFixedExcludeFlaky'
            retestall_num_of_failed_tests = extractMacroValue(retestall_macro, numbers_tex_file)
            for tool in tools:
                tool_macro = example_id.replace('-', '') + tool + \
                             'NumOfFailedTestsFixedExcludeFlaky'
                tool_num_of_failed_tests = extractMacroValue(tool_macro, numbers_tex_file)
                if int(tool_num_of_failed_tests) < int(retestall_num_of_failed_tests):
                    reportViolation('R1', tool, example_id, violation_list)

def checkRuleR2(violation_list, tools=TOOLS):
    checkRuleR2OnFixedVersion(violation_list, tools)
    checkRuleR2OnBuggyVersion(violation_list, tools)

def checkRuleR2OnFixedVersion(violation_list, tools, numbers_tex_file=RUN_FIXED_TWICE_NUMBERS, \
                              table_tex_file=RUN_FIXED_TWICE_TABLE):
    fr = open(table_tex_file, 'r')
    lines = fr.readlines()
    fr.close()
    for i in range(len(lines)):
        if ' & ' in lines[i] and '\\UseMacro{' in lines[i] and lines[i].strip().endswith('\\'):
            example_id = lines[i].split(' & ')[0]
            retestall_macro = example_id.replace('-', '') + 'notoolonceNumOfRunTests'
            num_of_all_tests = int(extractMacroValue(retestall_macro, numbers_tex_file))
            num_of_run_tests_map = {}
            for tool in tools:
                tool_macro = example_id.replace('-', '') + tool + 'onceNumOfRunTests'
                tool_num_of_run_tests = int(extractMacroValue(tool_macro, numbers_tex_file))
                num_of_run_tests_map[tool] = tool_num_of_run_tests
            if list(num_of_run_tests_map.values()).count(0) == 1 and \
               list(num_of_run_tests_map.values()).count(num_of_all_tests) == len(tools) - 1:
                for tool in num_of_run_tests_map:
                    if num_of_run_tests_map[tool] == 0:
                        reportViolation('R2', tool, example_id, violation_list)

def checkRuleR2OnBuggyVersion(violation_list, tools, \
                              numbers_tex_file=RUN_FIXED_THEN_BUGGY_NUMBERS, \
                              table_tex_file=RUN_FIXED_THEN_BUGGY_TABLE):
    fr = open(table_tex_file, 'r')
    lines = fr.readlines()
    fr.close()
    for i in range(len(lines)):
        if ' & ' in lines[i] and '\\UseMacro{' in lines[i] and lines[i].strip().endswith('\\'):
            example_id = lines[i].split(' & ')[0]
            retestall_macro = example_id.replace('-', '') + 'notoolNumOfRunTestsExcludeFlaky'
            num_of_all_tests = int(extractMacroValue(retestall_macro, numbers_tex_file))
            num_of_run_tests_map = {}
            for tool in tools:
                tool_macro = example_id.replace('-', '') + tool + 'NumOfRunTestsExcludeFlaky'
                tool_num_of_run_tests = int(extractMacroValue(tool_macro, numbers_tex_file))
                num_of_run_tests_map[tool] = tool_num_of_run_tests
            if list(num_of_run_tests_map.values()).count(0) == 1 and \
               list(num_of_run_tests_map.values()).count(num_of_all_tests) == len(tools) - 1:
                for tool in num_of_run_tests_map:
                    if num_of_run_tests_map[tool] == 0:
                        reportViolation('R2', tool, example_id, violation_list)

def checkRuleR3(violation_list, tools=TOOLS, numbers_tex_file=RUN_FIXED_THEN_BUGGY_NUMBERS, \
                table_tex_file=RUN_FIXED_THEN_BUGGY_TABLE):
    fr = open(table_tex_file, 'r')
    lines = fr.readlines()
    fr.close()
    for i in range(len(lines)):
        if ' & ' in lines[i] and '\\UseMacro{' in lines[i] and lines[i].strip().endswith('\\'):
            example_id = lines[i].split(' & ')[0]
            retestall_macro = example_id.replace('-', '') + \
                              'notoolNumOfRunTestsFixedExcludeFlaky'
            num_of_all_tests = int(extractMacroValue(retestall_macro, numbers_tex_file))
            for tool in tools:
                tool_fixed_macro = example_id.replace('-', '') + tool + \
                                   'NumOfRunTestsFixedExcludeFlaky'
                tool_buggy_macro = example_id.replace('-', '') + tool + \
                                   'NumOfRunTestsExcludeFlaky'
                tool_num_of_run_tests_on_fixed_version = \
                                int(extractMacroValue(tool_fixed_macro, numbers_tex_file))
                tool_num_of_run_tests_on_buggy_version = \
                                int(extractMacroValue(tool_buggy_macro, numbers_tex_file))
                if tool_num_of_run_tests_on_fixed_version == num_of_all_tests and \
                   tool_num_of_run_tests_on_buggy_version == num_of_all_tests:
                    reportViolation('R3', tool, example_id, violation_list)

def checkRuleR4(violation_list, tools=TOOLS):
    checkRuleR4OnFixedVersion(violation_list, tools)
    checkRuleR4OnBuggyVersion(violation_list, tools)

def checkRuleR4OnFixedVersion(violation_list, tools, numbers_tex_file=RUN_FIXED_TWICE_NUMBERS, \
                              table_tex_file=RUN_FIXED_TWICE_TABLE):
    fr = open(table_tex_file, 'r')
    lines = fr.readlines()
    fr.close()
    for i in range(len(lines)):
        if ' & ' in lines[i] and '\\UseMacro{' in lines[i] and lines[i].strip().endswith('\\'):
            example_id = lines[i].split(' & ')[0]
            retestall_macro = example_id.replace('-', '') + 'notoolonceNumOfRunTests'
            num_of_all_tests = int(extractMacroValue(retestall_macro, numbers_tex_file))
            num_of_run_tests_map = {}
            for tool in tools:
                tool_macro = example_id.replace('-', '') + tool + 'onceNumOfRunTests'
                tool_num_of_run_tests = int(extractMacroValue(tool_macro, numbers_tex_file))
                num_of_run_tests_map[tool] = tool_num_of_run_tests
            if list(num_of_run_tests_map.values()).count(0) == len(tools) - 1 and \
               list(num_of_run_tests_map.values()).count(num_of_all_tests) == 1:
                for tool in num_of_run_tests_map:
                    if num_of_run_tests_map[tool] != 0:
                        reportViolation('R4', tool, example_id, violation_list)

def checkRuleR4OnBuggyVersion(violation_list, tools, \
                              numbers_tex_file=RUN_FIXED_THEN_BUGGY_NUMBERS, \
                              table_tex_file=RUN_FIXED_THEN_BUGGY_TABLE):
    fr = open(table_tex_file, 'r')
    lines = fr.readlines()
    fr.close()
    for i in range(len(lines)):
        if ' & ' in lines[i] and '\\UseMacro{' in lines[i] and lines[i].strip().endswith('\\'):
            example_id = lines[i].split(' & ')[0]
            retestall_macro = example_id.replace('-', '') + 'notoolNumOfRunTestsExcludeFlaky'
            num_of_all_tests = int(extractMacroValue(retestall_macro, numbers_tex_file))
            num_of_run_tests_map = {}
            for tool in tools:
                tool_macro = example_id.replace('-', '') + tool + 'NumOfRunTestsExcludeFlaky'
                tool_num_of_run_tests = int(extractMacroValue(tool_macro, numbers_tex_file))
                num_of_run_tests_map[tool] = tool_num_of_run_tests
            if list(num_of_run_tests_map.values()).count(0) == len(tools) - 1 and \
               list(num_of_run_tests_map.values()).count(num_of_all_tests) == 1:
                for tool in num_of_run_tests_map:
                    if num_of_run_tests_map[tool] != 0:
                        reportViolation('R4', tool, example_id, violation_list)

def checkRuleR5(violation_list, tools=TOOLS, numbers_tex_file=RUN_FIXED_TWICE_NUMBERS, \
                table_tex_file=RUN_FIXED_TWICE_TABLE):
    fr = open(table_tex_file, 'r')
    lines = fr.readlines()
    fr.close()
    for i in range(len(lines)):
        if ' & ' in lines[i] and '\\UseMacro{' in lines[i] and lines[i].strip().endswith('\\'):
            example_id = lines[i].split(' & ')[0]
            num_of_run_tests_map = {}
            for tool in tools:
                tool_macro = example_id.replace('-', '') + tool + 'twiceNumOfRunTests'
                tool_num_of_run_tests = int(extractMacroValue(tool_macro, numbers_tex_file))
                if tool_num_of_run_tests != 0:
                    reportViolation('R5', tool, example_id, violation_list)

def checkRuleR6(violation_list, tools=TOOLS, numbers_tex_file=RUN_FIXED_THEN_BUGGY_NUMBERS, \
                table_tex_file=RUN_FIXED_THEN_BUGGY_TABLE):
    fr = open(table_tex_file, 'r')
    lines = fr.readlines()
    fr.close()
    for i in range(len(lines)):
        if ' & ' in lines[i] and '\\UseMacro{' in lines[i] and lines[i].strip().endswith('\\'):
            example_id = lines[i].split(' & ')[0]
            retestall_macro = example_id.replace('-', '') + \
                              'notoolNumOfRunTestsFixedExcludeFlaky'
            retestall_num_of_run_tests = extractMacroValue(retestall_macro, numbers_tex_file)
            for tool in tools:
                tool_macro = example_id.replace('-', '') + tool + \
                             'NumOfRunTestsFixedExcludeFlaky'
                tool_num_of_run_tests = extractMacroValue(tool_macro, numbers_tex_file)
                if int(tool_num_of_run_tests) != int(retestall_num_of_run_tests):
                    reportViolation('R6', tool, example_id, violation_list)

def checkRuleR7(violation_list, tools=TOOLS):
    checkRuleR7OnFixedVersion(violation_list, tools)
    checkRuleR7OnBuggyVersion(violation_list, tools)

def checkRuleR7OnBuggyVersion(violation_list, tools=TOOLS, \
                              numbers_tex_file=RUN_FIXED_THEN_BUGGY_NUMBERS, \
                              table_tex_file=RUN_FIXED_THEN_BUGGY_TABLE):
    fr = open(table_tex_file, 'r')
    lines = fr.readlines()
    fr.close()
    for i in range(len(lines)):
        if ' & ' in lines[i] and '\\UseMacro{' in lines[i] and lines[i].strip().endswith('\\'):
            example_id = lines[i].split(' & ')[0]
            retestall_macro = example_id.replace('-', '') + 'notoolNumOfFailedTestsExcludeFlaky'
            retestall_num_of_failed_tests = extractMacroValue(retestall_macro, numbers_tex_file)
            for tool in tools:
                tool_macro = example_id.replace('-', '') + tool + 'NumOfFailedTestsExcludeFlaky'
                tool_num_of_failed_tests = extractMacroValue(tool_macro, numbers_tex_file)
                if int(tool_num_of_failed_tests) > int(retestall_num_of_failed_tests):
                    reportViolation('R7', tool, example_id, violation_list)

def checkRuleR7OnFixedVersion(violation_list, tools=TOOLS, \
                              numbers_tex_file=RUN_FIXED_THEN_BUGGY_NUMBERS, \
                              table_tex_file=RUN_FIXED_THEN_BUGGY_TABLE):
    fr = open(table_tex_file, 'r')
    lines = fr.readlines()
    fr.close()
    for i in range(len(lines)):
        if ' & ' in lines[i] and '\\UseMacro{' in lines[i] and lines[i].strip().endswith('\\'):
            example_id = lines[i].split(' & ')[0]
            retestall_macro = example_id.replace('-', '') + \
                              'notoolNumOfFailedTestsFixedExcludeFlaky'
            retestall_num_of_failed_tests = extractMacroValue(retestall_macro, numbers_tex_file)
            for tool in tools:
                tool_macro = example_id.replace('-', '') + tool + \
                             'NumOfFailedTestsFixedExcludeFlaky'
                tool_num_of_failed_tests = extractMacroValue(tool_macro, numbers_tex_file)
                if int(tool_num_of_failed_tests) > int(retestall_num_of_failed_tests):
                    reportViolation('R7', tool, example_id, violation_list)

def reportViolation(rule, tool, example_id, violation_list):
    # print (rule, tool, example_id)
    violation_list.append((rule, tool, example_id))

def groupViolations(violation_list, buggy_numbers_tex_file=RUN_FIXED_THEN_BUGGY_NUMBERS, \
                    fixed_numbers_tex_file=RUN_FIXED_TWICE_NUMBERS):
    violations_grouping_dict = collections.OrderedDict({})
    for i in range(len(violation_list)):
        # each group must have same rule, same tool, and same project
        violation = violation_list[i]
        rule = violation[0]
        if rule not in violations_grouping_dict:
            violations_grouping_dict[rule] = collections.OrderedDict({})
        tool = violation[1]
        if tool not in violations_grouping_dict[rule]:
            violations_grouping_dict[rule][tool] = collections.OrderedDict({})
        example_id = violation[2]
        project = example_id.split('-')[0]
        if project not in violations_grouping_dict[rule][tool]:
            violations_grouping_dict[rule][tool][project] = []
        violations_grouping_dict[rule][tool][project].append(example_id)
        #print (violations_grouping_dict)
    for rule in violations_grouping_dict:
        for tool in violations_grouping_dict[rule]:
            for project in violations_grouping_dict[rule][tool]:
                if rule == 'R1':
                    matchGroupingRule2(rule, tool, project, violations_grouping_dict)
                    matchGroupingRule4(rule, tool, project, violations_grouping_dict)
                elif rule == 'R2':
                    matchGroupingRule6(rule, tool, project, violations_grouping_dict)
                    matchGroupingRule5(rule, tool, project, violations_grouping_dict)
                elif rule == 'R3':
                    matchGroupingRule1(rule, tool, project, violations_grouping_dict)
                elif rule == 'R4':
                    matchGroupingRule1(rule, tool, project, violations_grouping_dict)
                elif rule == 'R5':
                    matchGroupingRule1_V0EqualsV1(rule, tool, project, violations_grouping_dict)
                    matchGroupingRule5_V0EqualsV1(rule, tool, project, violations_grouping_dict)
                elif rule == 'R6':
                    matchGroupingRule6(rule, tool, project, violations_grouping_dict)
                    matchGroupingRule5(rule, tool, project, violations_grouping_dict)
                elif rule == 'R7':
                    matchGroupingRule3(rule, tool, project, violations_grouping_dict)
                    matchGroupingRule4(rule, tool, project, violations_grouping_dict)
    # for rule in violations_grouping_dict:
    #     for tool in violations_grouping_dict[rule]:
    #         for project in violations_grouping_dict[rule][tool]:
    #             for example in violations_grouping_dict[rule][tool][project]:
    #                 print (rule, tool, project, example)
    groups_dict = collections.OrderedDict({})
    for rule in violations_grouping_dict:
        for tool in violations_grouping_dict[rule]:
            for project in violations_grouping_dict[rule][tool]:
                for example in violations_grouping_dict[rule][tool][project]:
                    example_id = example[0]
                    group_name = example[1]
                    if group_name not in groups_dict:
                        groups_dict[group_name] = []
                    groups_dict[group_name].append((example_id, rule, tool, project))
    for group_name in groups_dict:
        print ('\nGROUP: ' + group_name)
        for example in groups_dict[group_name]:
            print ('On ' + example[0] + ', ' + example[2] + ' violates ' + example[1])

# GR1: run same as retestall in V1
def matchGroupingRule1(rule, tool, project, violations_grouping_dict, \
                       numbers_tex_file=RUN_FIXED_THEN_BUGGY_NUMBERS):
    examples = violations_grouping_dict[rule][tool][project]
    for i in range(len(examples)):
        example = examples[i]
        if type(example) is tuple:
            continue
        example_id = example
        retestall_macro = example_id.replace('-', '') + 'notoolNumOfRunTestsExcludeFlaky'
        retestall_num_of_run_tests = int(extractMacroValue(retestall_macro, numbers_tex_file))
        tool_macro = example_id.replace('-', '') + tool + 'NumOfRunTestsExcludeFlaky'
        tool_num_of_run_tests = int(extractMacroValue(tool_macro, numbers_tex_file))
        if retestall_num_of_run_tests == tool_num_of_run_tests:
            examples[i] = (examples[i], rule + '-' + tool + '-' + project + '-GR1')

# GR1: run same number of tests as retestall in V1 when V0 = V1
def matchGroupingRule1_V0EqualsV1(rule, tool, project, violations_grouping_dict, \
                                  numbers_tex_file=RUN_FIXED_TWICE_NUMBERS):
    examples = violations_grouping_dict[rule][tool][project]
    for i in range(len(examples)):
        example = examples[i]
        if type(example) is tuple:
            continue
        example_id = example
        retestall_macro = example_id.replace('-', '') + 'notooltwiceNumOfRunTests'
        retestall_num_of_run_tests = int(extractMacroValue(retestall_macro, numbers_tex_file))
        tool_macro = example_id.replace('-', '') + tool + 'twiceNumOfRunTests'
        tool_num_of_run_tests = int(extractMacroValue(tool_macro, numbers_tex_file))
        if retestall_num_of_run_tests == tool_num_of_run_tests:
            examples[i] = (examples[i], rule + '-' + tool + '-' + project + '-GR1')

# GR2: fail X less than retestall in V1
def matchGroupingRule2(rule, tool, project, violations_grouping_dict, \
                       numbers_tex_file=RUN_FIXED_THEN_BUGGY_NUMBERS):
    if rule != 'R1':
        return False
    examples = violations_grouping_dict[rule][tool][project]
    failed_less_map = collections.OrderedDict({})
    for i in range(len(examples)):
        example = examples[i]
        if type(example) is tuple:
            continue
        example_id = example
        retestall_macro = example_id.replace('-', '') + 'notoolNumOfFailedTestsExcludeFlaky'
        retestall_num_of_failed_tests = int(extractMacroValue(retestall_macro, numbers_tex_file))
        tool_macro = example_id.replace('-', '') + tool + 'NumOfFailedTestsExcludeFlaky'
        tool_num_of_failed_tests = int(extractMacroValue(tool_macro, numbers_tex_file))
        num_of_less_failed_tests = tool_num_of_failed_tests - retestall_num_of_failed_tests
        if num_of_less_failed_tests not in failed_less_map:
            failed_less_map[num_of_less_failed_tests] = []
        failed_less_map[num_of_less_failed_tests].append(i)
    for num_of_less_failed_tests in failed_less_map:
        for i in failed_less_map[num_of_less_failed_tests]:
            examples[i] = (examples[i], rule + '-' + tool + '-' + project + '-GR2-fail-' + \
                           str(num_of_less_failed_tests) + '-less')

# GR3: fail X more than retestall in V1
def matchGroupingRule3(rule, tool, project, violations_grouping_dict, \
                       numbers_tex_file=RUN_FIXED_THEN_BUGGY_NUMBERS):
    if rule != 'R7':
        return False
    examples = violations_grouping_dict[rule][tool][project]
    failed_more_map = collections.OrderedDict({})
    for i in range(len(examples)):
        example = examples[i]
        if type(example) is tuple:
            continue
        example_id = example
        retestall_macro = example_id.replace('-', '') + 'notoolNumOfFailedTestsExcludeFlaky'
        retestall_num_of_failed_tests = int(extractMacroValue(retestall_macro, numbers_tex_file))
        tool_macro = example_id.replace('-', '') + tool + 'NumOfFailedTestsExcludeFlaky'
        tool_num_of_failed_tests = int(extractMacroValue(tool_macro, numbers_tex_file))
        num_of_more_failed_tests = tool_num_of_failed_tests - retestall_num_of_failed_tests
        if num_of_more_failed_tests not in failed_more_map:
            failed_more_map[num_of_more_failed_tests] = []
        failed_more_map[num_of_more_failed_tests].append(i)
    for num_of_more_failed_tests in failed_more_map:
        for i in failed_more_map[num_of_more_failed_tests]:
            examples[i] = (examples[i], rule + '-' + tool + '-' + project + '-GR3-fail-' + \
                           str(num_of_more_failed_tests) + '-more')

# GR4: fail same number of tests in V1
def matchGroupingRule4(rule, tool, project, violations_grouping_dict, \
                       numbers_tex_file=RUN_FIXED_THEN_BUGGY_NUMBERS):
    examples = violations_grouping_dict[rule][tool][project]
    failed_map = collections.OrderedDict({})
    for i in range(len(examples)):
        example = examples[i]
        if type(example) is tuple:
            continue
        example_id = example
        tool_macro = example_id.replace('-', '') + tool + 'NumOfFailedTestsExcludeFlaky'
        tool_num_of_failed_tests = int(extractMacroValue(tool_macro, numbers_tex_file))
        if tool_num_of_failed_tests not in failed_map:
            failed_map[tool_num_of_failed_tests] = []
        failed_map[tool_num_of_failed_tests].append(i)
    for tool_num_of_failed_tests in failed_map:
        for i in failed_map[tool_num_of_failed_tests]:
            examples[i] = (examples[i], rule + '-' + tool + '-' + project + '-GR4-fail-' + \
                           str(tool_num_of_failed_tests))

# GR5: run same number of tests in V1
def matchGroupingRule5(rule, tool, project, violations_grouping_dict, \
                       numbers_tex_file=RUN_FIXED_THEN_BUGGY_NUMBERS):
    examples = violations_grouping_dict[rule][tool][project]
    run_map = collections.OrderedDict({})
    for i in range(len(examples)):
        example = examples[i]
        if type(example) is tuple:
            continue
        example_id = example
        retestall_macro = example_id.replace('-', '') + 'notoolNumOfRunTestsExcludeFlaky'
        retestall_num_of_run_tests = int(extractMacroValue(retestall_macro, numbers_tex_file))
        tool_macro = example_id.replace('-', '') + tool + 'NumOfRunTestsExcludeFlaky'
        tool_num_of_run_tests = int(extractMacroValue(tool_macro, numbers_tex_file))
        tool_run_tests_percentage = tool_num_of_run_tests / retestall_num_of_run_tests
        if 0 <= tool_run_tests_percentage and tool_run_tests_percentage < 0.1:
            bucket = "0-10%"
        elif 0.1 <= tool_run_tests_percentage and tool_run_tests_percentage < 0.2:
            bucket = "10-20%"
        elif 0.2 <= tool_run_tests_percentage and tool_run_tests_percentage < 0.3:
            bucket = "20-30%"
        elif 0.3 <= tool_run_tests_percentage and tool_run_tests_percentage < 0.4:
            bucket = "30-40%"
        elif 0.4 <= tool_run_tests_percentage and tool_run_tests_percentage < 0.5:
            bucket = "40-50%"
        elif 0.5 <= tool_run_tests_percentage and tool_run_tests_percentage < 0.6:
            bucket = "50-60%"
        elif 0.6 <= tool_run_tests_percentage and tool_run_tests_percentage < 0.7:
            bucket = "60-70%"
        elif 0.7 <= tool_run_tests_percentage and tool_run_tests_percentage < 0.8:
            bucket = "70-80%"
        elif 0.8 <= tool_run_tests_percentage and tool_run_tests_percentage < 0.9:
            bucket = "80-90%"
        elif 0.9 <= tool_run_tests_percentage and tool_run_tests_percentage < 1.0:
            bucket = "90-100%"
        if bucket not in run_map:
            run_map[bucket] = []
        run_map[bucket].append(i)
    for bucket in run_map:
        for i in run_map[bucket]:
            examples[i] = (examples[i], rule + '-' + tool + '-' + project + '-GR5-run-' + \
                           str(bucket))

# GR5: run same number of tests in V1 when V0 = V1, only apply to R5
def matchGroupingRule5_V0EqualsV1(rule, tool, project, violations_grouping_dict, \
                                  numbers_tex_file=RUN_FIXED_TWICE_NUMBERS):
    examples = violations_grouping_dict[rule][tool][project]
    run_map = collections.OrderedDict({})
    for i in range(len(examples)):
        example = examples[i]
        if type(example) is tuple:
            continue
        example_id = example
        retestall_macro = example_id.replace('-', '') + 'notoolonceNumOfRunTests'
        retestall_num_of_run_tests = int(extractMacroValue(retestall_macro, numbers_tex_file))
        tool_macro = example_id.replace('-', '') + tool + 'twiceNumOfRunTests'
        tool_num_of_run_tests = int(extractMacroValue(tool_macro, numbers_tex_file))
        tool_run_tests_percentage = tool_num_of_run_tests / retestall_num_of_run_tests
        ### 10% span
        # if 0 <= tool_run_tests_percentage and tool_run_tests_percentage < 0.1:
        #     bucket = "0-10%"
        # elif 0.1 <= tool_run_tests_percentage and tool_run_tests_percentage < 0.2:
        #     bucket = "10-20%"
        # elif 0.2 <= tool_run_tests_percentage and tool_run_tests_percentage < 0.3:
        #     bucket = "20-30%"
        # elif 0.3 <= tool_run_tests_percentage and tool_run_tests_percentage < 0.4:
        #     bucket = "30-40%"
        # elif 0.4 <= tool_run_tests_percentage and tool_run_tests_percentage < 0.5:
        #     bucket = "40-50%"
        # elif 0.5 <= tool_run_tests_percentage and tool_run_tests_percentage < 0.6:
        #     bucket = "50-60%"
        # elif 0.6 <= tool_run_tests_percentage and tool_run_tests_percentage < 0.7:
        #     bucket = "60-70%"
        # elif 0.7 <= tool_run_tests_percentage and tool_run_tests_percentage < 0.8:
        #     bucket = "70-80%"
        # elif 0.8 <= tool_run_tests_percentage and tool_run_tests_percentage < 0.9:
        #     bucket = "80-90%"
        # elif 0.9 <= tool_run_tests_percentage and tool_run_tests_percentage <= 1.0:
        #     bucket = "90-100%"
        ### 20% span
        if 0 <= tool_run_tests_percentage and tool_run_tests_percentage < 0.2:
            bucket = "0-20%"
        elif 0.2 <= tool_run_tests_percentage and tool_run_tests_percentage < 0.4:
            bucket = "20-40%"
        elif 0.4 <= tool_run_tests_percentage and tool_run_tests_percentage < 0.6:
            bucket = "40-60%"
        elif 0.6 <= tool_run_tests_percentage and tool_run_tests_percentage < 0.8:
            bucket = "60-80%"
        elif 0.8 <= tool_run_tests_percentage and tool_run_tests_percentage <= 1.0:
            bucket = "80-100%"
        ### 50% span
        # if 0 <= tool_run_tests_percentage and tool_run_tests_percentage < 0.5:
        #     bucket = "0-50%"
        # elif 0.5 <= tool_run_tests_percentage and tool_run_tests_percentage <= 1.0:
        #     bucket = "50-100%"
        if bucket not in run_map:
            run_map[bucket] = []
        run_map[bucket].append(i)
    for bucket in run_map:
        for i in run_map[bucket]:
            examples[i] = (examples[i], rule + '-' + tool + '-' + project + '-GR5-run-' + \
                           str(bucket))

# GR6: run same number of tests in V0, only apply to R2, R4, and R6
def matchGroupingRule6(rule, tool, project, violations_grouping_dict, \
                       numbers_tex_file=RUN_FIXED_TWICE_NUMBERS):
    examples = violations_grouping_dict[rule][tool][project]
    run_map = collections.OrderedDict({})
    for i in range(len(examples)):
        example = examples[i]
        if type(example) is tuple:
            continue
        example_id = example
        tool_macro = example_id.replace('-', '') + tool + 'onceNumOfRunTests'
        tool_num_of_run_tests = int(extractMacroValue(tool_macro, numbers_tex_file))
        if tool_num_of_run_tests not in run_map:
            run_map[tool_num_of_run_tests] = []
        run_map[tool_num_of_run_tests].append(i)
    for tool_num_of_run_tests in run_map:
        for i in run_map[tool_num_of_run_tests]:
            examples[i] = (examples[i], rule + '-' + tool + '-' + project + '-GR6-run-' + \
                           str(tool_num_of_run_tests))
            
if __name__ == '__main__':
    opts = parseArgs(sys.argv[1:])
    violation_list = []
    if opts.all:
        checkRuleR1(violation_list)
        checkRuleR2(violation_list)
        checkRuleR3(violation_list)
        checkRuleR4(violation_list)
        checkRuleR5(violation_list)
        checkRuleR6(violation_list)
        checkRuleR7(violation_list)
        # for v in violation_list:
        #     print (v)
        groupViolations(violation_list)
        exit(0)
    if opts.R1:
        checkRuleR1(violation_list)
    if opts.R2:
        checkRuleR2(violation_list)
    if opts.R3:
        checkRuleR3(violation_list)
    if opts.R4:
        checkRuleR4(violation_list)
    if opts.R5:
        checkRuleR5(violation_list)
    if opts.R6:
        checkRuleR6(violation_list)
    if opts.R7:
        checkRuleR7(violation_list)
