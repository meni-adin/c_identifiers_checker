
import argparse
from dataclasses import dataclass
from enum import Enum, auto
import json
import os
import pathlib
import re

CURRENT_FILE_NAME = os.path.basename(__file__)
WORKING_DIR = pathlib.Path(__file__).parent.resolve()
PROGRAM_DESC = 'C Identifiers Checker, a utility to check if an identifier is valid for use, according to the C Standard.'
PROGRAM_DISCLAIMER = 'Disclaimer: The distinction between "used by the library" and "reserved" is somewhat blurry, since some identifier are optional but defined in most implementations.'
IN_USE_FILE_NAME = 'in_use.json'
KEYWORDS_FILE_NAME = 'keywords.json'
RESERVED_FILE_NAME = 'reserved.json'
PARTICULAR_IDENTIFIERS_FILE_NAME = 'particular_identifiers.json'
RESERVED_PATTERNS_MATCHING_FILE_NAME = 'reserved_patterns_matching.json'
RESERVED_PATTERNS_FILE_NAME = 'reserved_patterns.json'
STANDARDS = ['knr', '89', '99', '11', '23']
STANDARD_ALL = 'all'
C_IDENTIFIER_REGEX = '[a-zA-Z_][a-zA-Z0-9_]*'

FilesFormat = Enum('FilesFormat',
    [
        'CHAPTER_REFERENCE',
        'LIST_REFERENCE',
    ]
)

@dataclass
class StandardConfigurations:
    name: str
    files_format: FilesFormat

STANDARD_CONFIGURATIONS = {
    'knr': StandardConfigurations(name='K&R-C (1978)', files_format=FilesFormat.CHAPTER_REFERENCE),
    '89':  StandardConfigurations(name='C89'         , files_format=FilesFormat.CHAPTER_REFERENCE),
    '99':  StandardConfigurations(name='C99)'        , files_format=FilesFormat.CHAPTER_REFERENCE),
    '11':  StandardConfigurations(name='C11'         , files_format=FilesFormat.CHAPTER_REFERENCE),
    '23':  StandardConfigurations(name='C23'         , files_format=FilesFormat.LIST_REFERENCE   ),
}

def exit_error(msg=''):
    if msg != '':
        print(msg)
    print('Terminating program')
    exit(1)

def run():
    args = parse_arguments()
    check(args)

def parse_arguments():
    parser = argparse.ArgumentParser(
        prog=CURRENT_FILE_NAME,
        description=PROGRAM_DESC + '\n' + PROGRAM_DISCLAIMER,
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '-i',
        '--identifier',
        action='store',
        required=True,
        help='The identifier to check'
    )
    standard_choices = [STANDARD_ALL] + STANDARDS
    standard_default = standard_choices[0]
    parser.add_argument(
        '-s',
        '--standard',
        action='store',
        choices=standard_choices,
        default=standard_default,
        help=f"The Standard to check for. Default is '{standard_default}'"
    )

    args = parser.parse_args()
    return args

def check(args):
    print(f'Checking the identifier {args.identifier}')
    if not is_valid_c_identifier(args.identifier):
        return
    if args.standard == STANDARD_ALL:
        for standard in STANDARDS:
            check_for_standard(standard, args.identifier)
    else:
        check_for_standard(args.standard, args.identifier)

def is_valid_c_identifier(identifier):
    if not re.fullmatch(C_IDENTIFIER_REGEX, identifier):
        print(f'The identifier {identifier} is invalid:')
        print(f'C identifiers must match the pattern: {C_IDENTIFIER_REGEX}')
        return False
    return True

def check_for_standard(standard, identifier):
    print(f'According to {STANDARD_CONFIGURATIONS[standard].name}:')
    if STANDARD_CONFIGURATIONS[standard].files_format == FilesFormat.CHAPTER_REFERENCE:
        if check_format_chapter_reference(standard, identifier):
            return
    elif STANDARD_CONFIGURATIONS[standard].files_format == FilesFormat.LIST_REFERENCE:
        if check_format_list_reference(standard, identifier):
            return
    else:
        exit_error(f'Unknown file-format is set for the current Standard ({standard}).')

    print(f'The identifier {identifier} is free for use')

def check_format_chapter_reference(standard, identifier):
    if is_in_use(standard, identifier):
        return True
    if is_keyword(standard, identifier):
        return True
    if is_reserved(standard, identifier):
        return True

def standard_dir_path(standard):
    return os.path.join(WORKING_DIR, standard)

def load_from_json(json_file_path):
    with open(os.path.join(json_file_path)) as json_file:
        json_file_content = json_file.read()
    return json.loads(json_file_content)

def is_in_use(standard, identifier):
    in_use_dict = load_from_json(os.path.join(standard_dir_path(standard), IN_USE_FILE_NAME))

    for pattern in in_use_dict:
        if re.fullmatch(pattern, identifier):
            print(f'The identifier {identifier} is in use by the standard-library:')
            print(f'Reference: {STANDARD_CONFIGURATIONS[standard].name}, §{in_use_dict[pattern]}')
            return True
    return False

def is_keyword(standard, identifier):
    keywords_dict = load_from_json(os.path.join(standard_dir_path(standard), KEYWORDS_FILE_NAME))

    if identifier in keywords_dict['keywords']:
        print(f'The identifier {identifier} is a keyword:')
        print(f'Reference: {STANDARD_CONFIGURATIONS[standard].name}, §{keywords_dict["reference"]}')
        return True
    return False

def is_reserved(standard, identifier):
    reserved_dict = load_from_json(os.path.join(standard_dir_path(standard), RESERVED_FILE_NAME))

    for pattern in reserved_dict:
        if re.fullmatch(pattern, identifier):
            print(f'The identifier {identifier} is reserved by the Standard, as it matches the pattern: {pattern}')
            print(f'Reference: {STANDARD_CONFIGURATIONS[standard].name}, §{reserved_dict[pattern]}')
            return True
    return False

def check_format_list_reference(standard, identifier):
    if check_in_file(standard, PARTICULAR_IDENTIFIERS_FILE_NAME, identifier):
        return True
    if check_in_file(standard, RESERVED_PATTERNS_MATCHING_FILE_NAME, identifier):
        return True
    if check_in_file(standard, RESERVED_PATTERNS_FILE_NAME, identifier):
        return True

def check_in_file(standard, file_name, identifier):
    root_dict = load_from_json(os.path.join(standard_dir_path(standard), file_name))

    if root_dict['list_type'] == 'regex':
        for pattern in root_dict['list']:
            if re.fullmatch(pattern, identifier):
                print(root_dict['description'], end=' ')
                print(pattern)
                return True
    elif root_dict['list_type'] == 'plain':
        for plain_string in root_dict['list']:
            if identifier == plain_string:
                print(root_dict['description'])
                return True
    else:
        exit_error('Unknown list_type')

    return False

if __name__ == "__main__":
    run()
