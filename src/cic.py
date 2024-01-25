
import argparse
import json
import os
import pathlib
import re
import sys

CURRENT_FILE_NAME = os.path.basename(__file__)
WORKING_DIR = pathlib.Path(__file__).parent.resolve()
PROGRAM_DESC = "C Identifiers Checker, a utility to check if an identifier is valid for use, according to the C Standard"
IN_USE_FILE_NAME = 'in_use.json'
KEYWORDS_FILE_NAME = 'keywords.json'
RESERVED_FILE_NAME = 'reserved.json'
STANDARD_FILE_NAME = 'standard.json'
STANDARDS = ['knr', '89', '99', '11', '23']
STANDARD_ALL = 'all'
C_IDENTIFIER_REGEX = '[a-zA-Z_][a-zA-Z0-9_]*'

SHORT_STANDARD_TO_FULL_NAME_MAP = {
    'knr': 'K&R-C (1978)',
    '89': 'C89',
    '99': 'C99',
    '11': 'C11',
    '23': 'C23',
}

def run():
    args = parse_arguments()
    print(f'Checking the identifier {args.identifier}')
    check(args)

def parse_arguments():
    parser = argparse.ArgumentParser(
        prog=CURRENT_FILE_NAME,
        description=PROGRAM_DESC
    )
    parser.add_argument(
        '-i',
        '--identifier',
        action='store',
        help="The identifier to check",
        required=True
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
    if is_in_use(standard, identifier):
        return
    if is_keyword(standard, identifier):
        return
    if is_reserved(standard, identifier):
        return

    print(f'The identifier {identifier} is free for use')

def standard_dir_path(standard):
    return os.path.join(WORKING_DIR, standard)

def load_from_json(json_file_path):
    with open(os.path.join(json_file_path)) as json_file:
        json_file_content = json_file.read()
    return json.loads(json_file_content)

def is_in_use(standard, identifier):
    in_use_dict = load_from_json(os.path.join(standard_dir_path(standard), IN_USE_FILE_NAME))

    # if identifier in in_use_dict:
    #     print(f'The identifier {identifier} is in use by the standard-library:')
    #     print(f'Reference: {SHORT_STANDARD_TO_FULL_NAME_MAP[standard]}, §{in_use_dict[identifier]}')
    #     return True
    # return False
    for pattern in in_use_dict:
        if re.fullmatch(pattern, identifier):
            print(f'The identifier {identifier} is in use by the standard-library:')
            print(f'Reference: {SHORT_STANDARD_TO_FULL_NAME_MAP[standard]}, §{in_use_dict[pattern]}')
            return True
    return False

def is_keyword(standard, identifier):
    keywords_dict = load_from_json(os.path.join(standard_dir_path(standard), KEYWORDS_FILE_NAME))

    if identifier in keywords_dict['keywords']:
        print(f'The identifier {identifier} is a keyword:')
        print(f'Reference: {SHORT_STANDARD_TO_FULL_NAME_MAP[standard]}, §{keywords_dict["reference"]}')
        return True
    return False

def is_reserved(standard, identifier):
    reserved_dict = load_from_json(os.path.join(standard_dir_path(standard), RESERVED_FILE_NAME))

    for pattern in reserved_dict:
        if re.fullmatch(pattern, identifier):
            print(f'The identifier {identifier} is reserved by the Standard, as it matches the pattern: {pattern}')
            print(f'Reference: {SHORT_STANDARD_TO_FULL_NAME_MAP[standard]}, §{reserved_dict[pattern]}')
            return True
    return False

if __name__ == "__main__":
    run()
