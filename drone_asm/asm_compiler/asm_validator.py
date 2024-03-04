# File: asm_validator.py
# Author: Michael Huelsman
# Copyright: Dr. Michael Andrew Huelsman 2024
# License: GNU GPLv3
# Created On: 02 Mar 2024
# Purpose:
#   Contains functions for validating lines of DroneASM
# Notes:

from .asm_tokenizer import Token
from .asm_constants import ARGS_DICT, ValidationErrorException


# Slight simplification through method calls.
def _test_numerical(token: Token):
    return token.token_type in ["IntNumber", "FloatNumber"]


def _test_num_register(token: Token):
    return token.token_type == "NumReg"


def _test_pic_register(token: Token):
    return token.token_type == "PicReg"


def _test_identifier(token: Token):
    return token.token_type == "Identifier"


def _test_label(token: Token):
    return token.token_type == "Label"


def _test_command(token: Token):
    return token.token_type == "Command"


def _test_string(token: Token):
    return token.token_type == "String"


# Precond:
#   tokens is a list of tokens representing a tokenized line of DroneASM
#
# Postcond:
#   Returns None
#   Raises a ValidationErrorException if the given tokens do not form a valid line.
def validate_line(tokens: [Token, ...]):
    # Check for a beginning label
    label_offset = 0
    if tokens[0].token_type == "Label":
        label_offset += 1
    # Make sure we start with a command
    if tokens[label_offset].token_type != "Command":
        raise ValidationErrorException("Line does not start with a command.")
    # Check Arguments (number)
    if tokens[label_offset].value not in ARGS_DICT[len(tokens) - (label_offset + 1)]:
        raise ValidationErrorException("Invalid number of arguments for specified command.")
    # Check Arguments (type)
    args = tokens[label_offset + 1:]
    arg_type_exception = ValidationErrorException("Invalid argument type(s) for specified command.")
    match tokens[label_offset].value:
        # Single Argument Cases
        case "PUSH_NUM" | "FORWARD" | "BACKWARD" | "LEFT" | "RIGHT" | "UP" | "DOWN" | "ROTATE_CW" | "ROTATE_CCW":
            if not (_test_num_register(args[0]) or _test_numerical(args[0])):
                raise arg_type_exception
        case "PUSH_RETURN" | "JUMP":
            if not _test_identifier(args[0]):
                raise arg_type_exception
        case "PUSH_PIC", "POP_PIC", "TAKE_PIC":
            if not _test_pic_register(args[0]):
                raise arg_type_exception
        case "POP_NUM":
            if not _test_num_register(args[0]):
                raise arg_type_exception
        case "DISPLAY":
            if not (_test_string(args[0]) or _test_num_register(args[0]) or _test_numerical(args[0]) or
                    _test_pic_register(args[0])):
                raise arg_type_exception
        # Double Argument Cases
        case "STORE":
            if not (_test_numerical(args[0]) and _test_num_register(args[1])):
                raise arg_type_exception
        case "COPY":
            if not (_test_num_register(args[0]) and _test_num_register(args[1])):
                raise arg_type_exception
        case "COPY_PIC":
            if not (_test_pic_register(args[0]) and _test_pic_register(args[1])):
                raise arg_type_exception
        # Triple Argument Cases
        case "BRANCH_EQ" | "BRANCH_NE" | "BRANCH_GT" | "BRANCH_LT" | "BRANCH_GE" | "BRANCH_LE":
            if not (_test_num_register(args[0]) or _test_numerical(args[0])):
                raise arg_type_exception
            if not (_test_num_register(args[1]) or _test_numerical(args[1])):
                raise arg_type_exception
            if not _test_identifier(args[2]):
                raise arg_type_exception
        case "ADD" | "SUB" | "MULT" | "DIV" | "IDIV" | "RDIV":
            if not (_test_num_register(args[0]) or _test_numerical(args[0])):
                raise arg_type_exception
            if not (_test_num_register(args[1]) or _test_numerical(args[1])):
                raise arg_type_exception
            if not _test_num_register(args[2]):
                raise arg_type_exception
