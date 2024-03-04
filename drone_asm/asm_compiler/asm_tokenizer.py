# File: asm_tokenizer.py
# Author: Michael Huelsman
# Copyright: Dr. Michael Andrew Huelsman 2024
# License: GNU GPLv3
# Created On: 02 Mar 2024
# Purpose:
#   A file for tokenizing a Drone assembly line during the compilation process
# Notes:
#   Whitespace causes check for token completion (if not in Str state)
#   Basic FSM Description:
#       S -$-> Reg
#       S -"-> Str1
#       S -[+-#]-> Num1
#       S -[A-Z]-> Id
#
#       Reg -P-> PicReg1
#       Reg -R-> NumReg1
#       PicReg1 -#-> PicReg2
#       NumReg1 -#-> NumReg2
#       PicReg2 -#-> PicReg2
#       NumReg2 -#-> NumReg2
#
#       Str1 -*-> Str1
#       Str1 -"-> Str2
#
#       Num1 -#-> Num1
#       Num1 -.-> Num2
#       Num2 -#-> Num2
#
#       Id -[A-Z]_#-> Id
#       Id -:-> Lbl
#
#   Accepting States:
#       PicReg2
#       NumReg2
#       Str2
#       Num1
#       Num2
#       Id
#       Lbl


from .asm_constants import COMMAND_LIST, Token, TokenizerErrorException


def detect_command(token: Token):
    if token.token_type == "Identifier":
        if token.value in COMMAND_LIST:
            token.token_type = "Command"
    return token


def tokenize(line: str):
    line = line.strip()
    if not line:
        return []
    # Remove case
    line = line.upper()
    # Setup final storage
    result = []
    # Setup FSM for tokenizing
    state = "S"
    type_dict = {
        "PicReg2": "PicReg",
        "NumReg2": "NumReg",
        "Str2": "String",
        "Num1": "IntNumber",
        "Num2": "FloatNumber",
        "Id": "Identifier",
        "Lbl": "Label"
    }
    current_token = []
    # Loop Through the line char-by-char
    for char in line:
        # Check token end
        if char.isspace() and state != "Str1":
            if state in type_dict.keys():
                result.append(Token(type_dict[state], "".join(current_token)))
                current_token = []
                state = "S"
            continue
        # Update state
        match state:
            case "S":
                if char == "$":
                    state = "Reg"
                elif char == '"':
                    state = "Str1"
                elif char.isdigit() or char in ["+", "-"]:
                    state = "Num1"
                    current_token.append(char)
                elif char.isalpha():
                    state = "Id"
                    current_token.append(char)
                else:
                    raise TokenizerErrorException("Unknown/incorrect symbol in token.")
            # Register States
            case "Reg":
                if char == "P":
                    state = "PicReg1"
                elif char == "R":
                    state = "NumReg1"
                else:
                    raise TokenizerErrorException("Unknown/incorrect symbol in register token.")
            case "PicReg1":
                if char.isdigit():
                    state = "PicReg2"
                    current_token.append(char)
                else:
                    raise TokenizerErrorException("Unknown/incorrect symbol picture in register token.")
            case "PicReg2":
                if char.isdigit():
                    state = "PicReg2"
                    current_token.append(char)
                else:
                    raise TokenizerErrorException("Unknown/incorrect symbol in picture register token.")
            case "NumReg1":
                if char.isdigit():
                    state = "NumReg2"
                    current_token.append(char)
                else:
                    raise TokenizerErrorException("Unknown/incorrect symbol in register token.")
            case "NumReg2":
                if char.isdigit():
                    current_token.append(char)
                else:
                    raise TokenizerErrorException("Unknown/incorrect symbol in register token.")
            # String States
            case "Str1":
                if char == '"':
                    state = "Str2"
                else:
                    current_token.append(char)
            # Number States
            case "Num1":
                if char == ".":
                    state = "Num2"
                    current_token.append(char)
                elif char.isdigit():
                    state = "Num1"
                    current_token.append(char)
                else:
                    raise TokenizerErrorException("Unknown/incorrect symbol in number token.")
            case "Num2":
                if char.isdigit():
                    state = "Num2"
                    current_token.append(char)
                else:
                    raise TokenizerErrorException("Unknown/incorrect symbol in number token.")
            # Identifier States
            case "Id":
                if char.isalnum() or char == "_":
                    state = "Id"
                    current_token.append(char)
                elif char == ":":
                    state = "Lbl"
                else:
                    raise TokenizerErrorException("Unknown/incorrect symbol in identifier token.")
            case _:
                raise TokenizerErrorException("Unknown state.")
    if state in type_dict.keys():
        result.append(Token(type_dict[state], "".join(current_token)))
    else:
        raise TokenizerErrorException("Unknown/incomplete token.")
    # Detect and label commands
    for token in result:
        detect_command(token)
    return result


# Testing
if __name__ == '__main__':
    def main():
        tokens = tokenize("Mark1: JUMP 12.3 -3.4 +3.14 MARK2 -13 +16 $R6 $P6 \"Hello, World!\"")
        for token in tokens:
            print(token)
        tokenize("")
    
    
    main()
