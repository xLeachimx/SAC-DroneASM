# File: asm_compile.py
# Author: Michael Huelsman
# Copyright: Dr. Michael Andrew Huelsman 2024
# License: GNU GPLv3
# Created On: 03 Mar 2024
# Purpose:
# Notes:
import sys

from .asm_constants import TokenizerErrorException, ValidationErrorException, Program
from .asm_tokenizer import tokenize
from .asm_validator import validate_line


# Removes comments and strips the line of whitespace.
def preprocess(line: str):
    comment_location = line.find('#')
    if comment_location >= 0:
        line = line[:comment_location]
    line = line.upper()
    line = line.strip()
    return line


def compile(lines: [str, ...]):
    program = Program()
    line_num = 0
    for line in lines:
        line_num += 1
        line = preprocess(line)
        try:
            tokens = tokenize(line)
            validate_line(tokens)
            program.add_line(tokens)
        except TokenizerErrorException as exp:
            exp.message = f"Line {line_num}: " + exp.message
            raise exp
        except ValidationErrorException as exp:
            exp.message = f"Line {line_num}: " + exp.message
            raise exp
    return program
