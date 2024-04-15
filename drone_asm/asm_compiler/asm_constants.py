# File: asm_constants.py
# Author: Michael Huelsman
# Copyright: Dr. Michael Andrew Huelsman 2024
# License: GNU GPLv3
# Created On: 03 Mar 2024
# Purpose:
# Notes:

from itertools import chain


class TokenizerErrorException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class ValidationErrorException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


# Label Map Error Exception
class LabelNotFoundException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


ARGS_DICT = {
    0: ["NOP", "HALT", "JUMP_RETURN", "POP_RETURN", "TAKEOFF", "LAND"],
    1: ["PUSH_NUM", "PUSH_RETURN", "PUSH_PIC", "POP_NUM", "POP_PIC", "JUMP",
        "FORWARD", "BACKWARD", "LEFT", "RIGHT", "UP", "DOWN", "ROTATE_CW", "ROTATE_CCW",
        "DISPLAY", "TAKE_PIC"],
    2: ["STORE", "COPY", "COPY_PIC", "LOAD_PIC"],
    3: ["BRANCH_EQ", "BRANCH_NE", "BRANCH_GT", "BRANCH_LT", "BRANCH_GE", "BRANCH_LE",
        "ADD", "SUB", "MULT", "DIV", "IDIV", "RDIV", "DETECT_FACE", "MATCH_FACE"]
}

COMMAND_LIST = list(chain.from_iterable(ARGS_DICT.values()))

TOKEN_TYPES = [
    "PicReg",
    "NumReg",
    "String",
    "IntNumber",
    "FloatNumber",
    "Identifier",
    "Label",
    "Command"
]


# Data class for holding a token
class Token:
    def __init__(self, token_type: str, value: str):
        self.token_type = token_type
        self.value = value
    
    def __str__(self):
        return f"Token {self.value}, Type {self.token_type}"


_NOP_TOKEN = Token("Command", "NOP")


class Program:
    def __init__(self):
        self.label_map = {}
        self.tokenized_lines = []
    
    def add_line(self, line: [Token, ...]):
        # Handle empty lines
        if len(line) == 0:
            line.append(_NOP_TOKEN)
        # Log and remove labels
        elif line[0].token_type == "Label":
            self.label_map[line[0].value] = len(self.tokenized_lines)
            if len(line) == 1:
                line.append(_NOP_TOKEN)
            line = line[1:]
        self.tokenized_lines.append(line)
    
    def get_line(self, line_num: int) -> [Token]:
        return self.tokenized_lines[line_num]
    
    def line_count(self) -> int:
        return len(self.tokenized_lines)
    
    def label_lookup(self, label: str) -> str:
        if label in self.label_map:
            return self.label_map[label]
        raise LabelNotFoundException(f"Cannot find label {label}.")
    
    def __str__(self):
        result = []
        for line in self.tokenized_lines:
            for token in line:
                result.append(str(token) + " ")
            result.append("\n")
        return "".join(result)
