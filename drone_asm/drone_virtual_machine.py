# File: drone_virtual_machine.py
# Author: Michael Huelsman
# Copyright: Dr. Michael Andrew Huelsman 2024
# License: GNU GPLv3
# Created On: 03 Mar 2024
# Purpose:
#   A simple "nice" machine for handling DroneASM programs
# Notes:
import cv2

from drone_asm.drone import TelloDrone, SimulatedDrone
from drone_asm.asm_compiler import Program
from drone_asm.facial_recognition import find_faces, encode_face, face_similarity


class RuntimeSoftwareErrorException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class RuntimeHardwareErrorException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class DroneVM:
    __NUMERICAL_REGISTERS = 16
    __PICTURE_REGISTERS = 8
    __FACE_REGISTERS = 8
    
    def __init__(self):
        # Register setup
        self.num_reg = [0 for i in range(DroneVM.__NUMERICAL_REGISTERS)]
        self.pic_reg = [None for i in range(DroneVM.__PICTURE_REGISTERS)]
        self.face_reg = [(None, None) for i in range(DroneVM.__FACE_REGISTERS)]
        self.return_reg = 0
        # Stack setup
        self.num_stack = []
        self.pic_stack = []
        self.return_stack = []
        # Setup drone
        self.drone_tracking = SimulatedDrone()
        self.drone = SimulatedDrone()
        self.drone_path = [self.drone_tracking.get_state()['loc'][:]]
        
    def reset(self):
        # Register setup
        self.num_reg = [0 for i in range(DroneVM.__NUMERICAL_REGISTERS)]
        self.pic_reg = [None for i in range(DroneVM.__PICTURE_REGISTERS)]
        self.face_reg = [(None, None) for i in range(DroneVM.__FACE_REGISTERS)]
        self.return_reg = 0
        # Stack setup
        self.num_stack = []
        self.pic_stack = []
        self.return_stack = []
        # Setup drone
        self.drone_tracking = SimulatedDrone()
        self.drone = SimulatedDrone()
        self.drone_path = [self.drone_tracking.get_state()['loc'][:]]
        self.running = False
    
    def run_program(self, program: Program, simulated: bool = True):
        program_counter = 0
        self.running = True
        if not simulated:
            self.drone = TelloDrone()
        if not self.drone.connect():
            self.drone.shutdown()
            raise RuntimeHardwareErrorException("Unable to connect to drone.")
        # Main Execution Look
        while self.running:
            yield None
            if program_counter >= program.line_count():
                self.running = False
                continue
            current_line = program.get_line(program_counter)
            jumped = False
            # Execute commands
            match current_line[0].value:
                case "NOP":
                    pass
                case "HALT":
                    self.running = False
                    continue
                # Variable operations
                case "STORE":
                    val = current_line[1].value
                    if current_line[1].token_type == "IntNumber":
                        val = int(val)
                    elif current_line[1].token_type == "FloatNumber":
                        val = float(val)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    reg = int(current_line[2].value)
                    if 0 <= reg < len(self.num_reg):
                        self.num_reg[reg] = val
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                case "COPY":
                    reg1 = int(current_line[1].value)
                    reg2 = int(current_line[2].value)
                    if 0 <= reg1 < len(self.num_reg) and 0 <= reg2 < len(self.num_reg):
                        self.num_reg[reg2] = self.num_reg[reg1]
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                case "COPY_PIC":
                    reg1 = int(current_line[1].value)
                    reg2 = int(current_line[2].value)
                    if 0 <= reg1 < len(self.pic_reg) and 0 <= reg2 < len(self.pic_reg):
                        self.pic_reg[reg2] = self.pic_reg[reg1]
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                case "PUSH_NUM":
                    if current_line[1].token_type == "NumReg":
                        reg = int(current_line[1].value)
                        if 0 <= reg < len(self.num_reg):
                            self.num_stack.append(self.num_reg[reg])
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    else:
                        val = current_line[1].value
                        if current_line[1].token_type == "IntNumber":
                            val = int(val)
                        elif current_line[1].token_type == "FloatNumber":
                            val = float(val)
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Unknown value type.")
                        self.num_stack.append(val)
                case "PUSH_RETURN":
                    line_num = program.label_lookup(current_line[1].value)
                    self.return_stack.append(line_num)
                case "PUSH_PIC":
                    reg = int(current_line[1].value)
                    if 0 <= reg < len(self.pic_reg):
                        self.num_stack.append(self.pic_reg[reg])
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                case "POP_NUM":
                    reg = int(current_line[1].value)
                    if 0 <= reg < len(self.num_reg):
                        self.num_reg[reg] = self.num_stack.pop()
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                case "POP_PIC":
                    reg = int(current_line[1].value)
                    if 0 <= reg < len(self.pic_reg):
                        self.pic_reg[reg] = self.pic_stack.pop()
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                case "POP_NUM":
                    self.return_reg = self.return_stack.pop()
                # Flow Control
                case "BRANCH_EQ":
                    val1 = current_line[1].value
                    if current_line[1].token_type == "NumReg":
                        val1 = int(val1)
                        if 0 <= val1 < len(self.num_reg):
                            val1 = self.num_reg[val1]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[1].token_type == "IntNumber":
                        val1 = int(val1)
                    elif current_line[1].token_type == "FloatNumber":
                        val1 = float(val1)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    val2 = current_line[2].value
                    if current_line[2].token_type == "NumReg":
                        val2 = int(val2)
                        if 0 <= val2 < len(self.num_reg):
                            val2 = self.num_reg[val2]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[2].token_type == "IntNumber":
                        val2 = int(val2)
                    elif current_line[2].token_type == "FloatNumber":
                        val2 = float(val2)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    if val1 == val2:
                        jumped = True
                        program_counter = program.label_lookup(current_line[3].value)
                case "BRANCH_NE":
                    val1 = current_line[1].value
                    if current_line[1].token_type == "NumReg":
                        val1 = int(val1)
                        if 0 <= val1 < len(self.num_reg):
                            val1 = self.num_reg[val1]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[1].token_type == "IntNumber":
                        val1 = int(val1)
                    elif current_line[1].token_type == "FloatNumber":
                        val1 = float(val1)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    val2 = current_line[2].value
                    if current_line[2].token_type == "NumReg":
                        val2 = int(val2)
                        if 0 <= val2 < len(self.num_reg):
                            val2 = self.num_reg[val2]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[2].token_type == "IntNumber":
                        val2 = int(val2)
                    elif current_line[2].token_type == "FloatNumber":
                        val2 = float(val2)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    if val1 != val2:
                        jumped = True
                        program_counter = program.label_lookup(current_line[3].value)
                case "BRANCH_GT":
                    val1 = current_line[1].value
                    if current_line[1].token_type == "NumReg":
                        val1 = int(val1)
                        if 0 <= val1 < len(self.num_reg):
                            val1 = self.num_reg[val1]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[1].token_type == "IntNumber":
                        val1 = int(val1)
                    elif current_line[1].token_type == "FloatNumber":
                        val1 = float(val1)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    val2 = current_line[2].value
                    if current_line[2].token_type == "NumReg":
                        val2 = int(val2)
                        if 0 <= val2 < len(self.num_reg):
                            val2 = self.num_reg[val2]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[2].token_type == "IntNumber":
                        val2 = int(val2)
                    elif current_line[2].token_type == "FloatNumber":
                        val2 = float(val2)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    if val1 > val2:
                        jumped = True
                        program_counter = program.label_lookup(current_line[3].value)
                case "BRANCH_LT":
                    val1 = current_line[1].value
                    if current_line[1].token_type == "NumReg":
                        val1 = int(val1)
                        if 0 <= val1 < len(self.num_reg):
                            val1 = self.num_reg[val1]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[1].token_type == "IntNumber":
                        val1 = int(val1)
                    elif current_line[1].token_type == "FloatNumber":
                        val1 = float(val1)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    val2 = current_line[2].value
                    if current_line[2].token_type == "NumReg":
                        val2 = int(val2)
                        if 0 <= val2 < len(self.num_reg):
                            val2 = self.num_reg[val2]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[2].token_type == "IntNumber":
                        val2 = int(val2)
                    elif current_line[2].token_type == "FloatNumber":
                        val2 = float(val2)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    if val1 < val2:
                        jumped = True
                        program_counter = program.label_lookup(current_line[3].value)
                case "BRANCH_GE":
                    val1 = current_line[1].value
                    if current_line[1].token_type == "NumReg":
                        val1 = int(val1)
                        if 0 <= val1 < len(self.num_reg):
                            val1 = self.num_reg[val1]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[1].token_type == "IntNumber":
                        val1 = int(val1)
                    elif current_line[1].token_type == "FloatNumber":
                        val1 = float(val1)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    val2 = current_line[2].value
                    if current_line[2].token_type == "NumReg":
                        val2 = int(val2)
                        if 0 <= val2 < len(self.num_reg):
                            val2 = self.num_reg[val2]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[2].token_type == "IntNumber":
                        val2 = int(val2)
                    elif current_line[2].token_type == "FloatNumber":
                        val2 = float(val2)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    if val1 >= val2:
                        jumped = True
                        program_counter = program.label_lookup(current_line[3].value)
                case "BRANCH_LE":
                    val1 = current_line[1].value
                    if current_line[1].token_type == "NumReg":
                        val1 = int(val1)
                        if 0 <= val1 < len(self.num_reg):
                            val1 = self.num_reg[val1]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[1].token_type == "IntNumber":
                        val1 = int(val1)
                    elif current_line[1].token_type == "FloatNumber":
                        val1 = float(val1)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    val2 = current_line[2].value
                    if current_line[2].token_type == "NumReg":
                        val2 = int(val2)
                        if 0 <= val2 < len(self.num_reg):
                            val2 = self.num_reg[val2]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[2].token_type == "IntNumber":
                        val2 = int(val2)
                    elif current_line[2].token_type == "FloatNumber":
                        val2 = float(val2)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    if val1 <= val2:
                        jumped = True
                        program_counter = program.label_lookup(current_line[3].value)
                case "JUMP":
                    jumped = True
                    program_counter = program.label_lookup(current_line[1].value)
                case "JUMP_RETURN":
                    jumped = True
                    program_counter = self.return_reg
                # Math Operations
                case "ADD":
                    val1 = current_line[1].value
                    if current_line[1].token_type == "NumReg":
                        val1 = int(val1)
                        if 0 <= val1 < len(self.num_reg):
                            val1 = self.num_reg[val1]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[1].token_type == "IntNumber":
                        val1 = int(val1)
                    elif current_line[1].token_type == "FloatNumber":
                        val1 = float(val1)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    val2 = current_line[2].value
                    if current_line[2].token_type == "NumReg":
                        val2 = int(val2)
                        if 0 <= val2 < len(self.num_reg):
                            val2 = self.num_reg[val2]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[2].token_type == "IntNumber":
                        val2 = int(val2)
                    elif current_line[2].token_type == "FloatNumber":
                        val2 = float(val2)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    store_reg = int(current_line[3].value)
                    if 0 <= store_reg < len(self.num_reg):
                        self.num_reg[store_reg] = val1 + val2
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                case "SUB":
                    val1 = current_line[1].value
                    if current_line[1].token_type == "NumReg":
                        val1 = int(val1)
                        if 0 <= val1 < len(self.num_reg):
                            val1 = self.num_reg[val1]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[1].token_type == "IntNumber":
                        val1 = int(val1)
                    elif current_line[1].token_type == "FloatNumber":
                        val1 = float(val1)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    val2 = current_line[2].value
                    if current_line[2].token_type == "NumReg":
                        val2 = int(val2)
                        if 0 <= val2 < len(self.num_reg):
                            val2 = self.num_reg[val2]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[2].token_type == "IntNumber":
                        val2 = int(val2)
                    elif current_line[2].token_type == "FloatNumber":
                        val2 = float(val2)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    store_reg = int(current_line[3].value)
                    if 0 <= store_reg < len(self.num_reg):
                        self.num_reg[store_reg] = val1 - val2
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                case "MULT":
                    val1 = current_line[1].value
                    if current_line[1].token_type == "NumReg":
                        val1 = int(val1)
                        if 0 <= val1 < len(self.num_reg):
                            val1 = self.num_reg[val1]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[1].token_type == "IntNumber":
                        val1 = int(val1)
                    elif current_line[1].token_type == "FloatNumber":
                        val1 = float(val1)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    val2 = current_line[2].value
                    if current_line[2].token_type == "NumReg":
                        val2 = int(val2)
                        if 0 <= val2 < len(self.num_reg):
                            val2 = self.num_reg[val2]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[2].token_type == "IntNumber":
                        val2 = int(val2)
                    elif current_line[2].token_type == "FloatNumber":
                        val2 = float(val2)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    store_reg = int(current_line[3].value)
                    if 0 <= store_reg < len(self.num_reg):
                        self.num_reg[store_reg] = val1 * val2
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                case "DIV":
                    val1 = current_line[1].value
                    if current_line[1].token_type == "NumReg":
                        val1 = int(val1)
                        if 0 <= val1 < len(self.num_reg):
                            val1 = self.num_reg[val1]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[1].token_type == "IntNumber":
                        val1 = int(val1)
                    elif current_line[1].token_type == "FloatNumber":
                        val1 = float(val1)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    val2 = current_line[2].value
                    if current_line[2].token_type == "NumReg":
                        val2 = int(val2)
                        if 0 <= val2 < len(self.num_reg):
                            val2 = self.num_reg[val2]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[2].token_type == "IntNumber":
                        val2 = int(val2)
                    elif current_line[2].token_type == "FloatNumber":
                        val2 = float(val2)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    store_reg = int(current_line[3].value)
                    if 0 <= store_reg < len(self.num_reg):
                        if val2 != 0:
                            self.num_reg[store_reg] = val1 / val2
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException("Attempted to divide by zero.")
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                case "IDIV":
                    val1 = current_line[1].value
                    if current_line[1].token_type == "NumReg":
                        val1 = int(val1)
                        if 0 <= val1 < len(self.num_reg):
                            val1 = self.num_reg[val1]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[1].token_type == "IntNumber":
                        val1 = int(val1)
                    elif current_line[1].token_type == "FloatNumber":
                        val1 = float(val1)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    val2 = current_line[2].value
                    if current_line[2].token_type == "NumReg":
                        val2 = int(val2)
                        if 0 <= val2 < len(self.num_reg):
                            val2 = self.num_reg[val2]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[2].token_type == "IntNumber":
                        val2 = int(val2)
                    elif current_line[2].token_type == "FloatNumber":
                        val2 = float(val2)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    store_reg = int(current_line[3].value)
                    if 0 <= store_reg < len(self.num_reg):
                        self.num_reg[store_reg] = val1 // val2
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                case "RDIV":
                    val1 = current_line[1].value
                    if current_line[1].token_type == "NumReg":
                        val1 = int(val1)
                        if 0 <= val1 < len(self.num_reg):
                            val1 = self.num_reg[val1]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[1].token_type == "IntNumber":
                        val1 = int(val1)
                    elif current_line[1].token_type == "FloatNumber":
                        val1 = float(val1)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    val2 = current_line[2].value
                    if current_line[2].token_type == "NumReg":
                        val2 = int(val2)
                        if 0 <= val2 < len(self.num_reg):
                            val2 = self.num_reg[val2]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[2].token_type == "IntNumber":
                        val2 = int(val2)
                    elif current_line[2].token_type == "FloatNumber":
                        val2 = float(val2)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    store_reg = int(current_line[3].value)
                    if 0 <= store_reg < len(self.num_reg):
                        self.num_reg[store_reg] = val1 % val2
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                # Drone Operations
                case "TAKEOFF":
                    if not self.drone.takeoff():
                        self.drone.shutdown()
                        raise RuntimeHardwareErrorException(f"Could not complete maneuver")
                case "LAND":
                    if not self.drone.land():
                        self.drone.shutdown()
                        raise RuntimeHardwareErrorException(f"Could not complete maneuver")
                case "FORWARD":
                    val = current_line[1].value
                    if current_line[1].token_type == "NumReg":
                        val = int(val)
                        if 0 <= val < len(self.num_reg):
                            val = self.num_reg[val]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[1].token_type == "IntNumber":
                        val = int(val)
                    elif current_line[1].token_type == "FloatNumber":
                        val = float(val)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    val = int(val)
                    if not self.drone.forward(val):
                        self.drone.shutdown()
                        raise RuntimeHardwareErrorException(f"Could not complete maneuver")
                    self.drone_tracking.forward(val)
                    self.drone_path.append(self.drone_tracking.get_state()['loc'][:])
                case "BACKWARD":
                    val = current_line[1].value
                    if current_line[1].token_type == "NumReg":
                        val = int(val)
                        if 0 <= val < len(self.num_reg):
                            val = self.num_reg[val]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[1].token_type == "IntNumber":
                        val = int(val)
                    elif current_line[1].token_type == "FloatNumber":
                        val = float(val)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    val = int(val)
                    if not self.drone.backward(val):
                        self.drone.shutdown()
                        raise RuntimeHardwareErrorException(f"Could not complete maneuver")
                    self.drone_tracking.backward(val)
                    self.drone_path.append(self.drone_tracking.get_state()['loc'][:])
                case "LEFT":
                    val = current_line[1].value
                    if current_line[1].token_type == "NumReg":
                        val = int(val)
                        if 0 <= val < len(self.num_reg):
                            val = self.num_reg[val]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[1].token_type == "IntNumber":
                        val = int(val)
                    elif current_line[1].token_type == "FloatNumber":
                        val = float(val)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    val = int(val)
                    if not self.drone.left(val):
                        self.drone.shutdown()
                        raise RuntimeHardwareErrorException(f"Could not complete maneuver")
                    self.drone_tracking.left(val)
                    self.drone_path.append(self.drone_tracking.get_state()['loc'][:])
                case "RIGHT":
                    val = current_line[1].value
                    if current_line[1].token_type == "NumReg":
                        val = int(val)
                        if 0 <= val < len(self.num_reg):
                            val = self.num_reg[val]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[1].token_type == "IntNumber":
                        val = int(val)
                    elif current_line[1].token_type == "FloatNumber":
                        val = float(val)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    val = int(val)
                    if not self.drone.right(val):
                        self.drone.shutdown()
                        raise RuntimeHardwareErrorException(f"Could not complete maneuver")
                    self.drone_tracking.right(val)
                    self.drone_path.append(self.drone_tracking.get_state()['loc'][:])
                case "UP":
                    val = current_line[1].value
                    if current_line[1].token_type == "NumReg":
                        val = int(val)
                        if 0 <= val < len(self.num_reg):
                            val = self.num_reg[val]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[1].token_type == "IntNumber":
                        val = int(val)
                    elif current_line[1].token_type == "FloatNumber":
                        val = float(val)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    val = int(val)
                    if not self.drone.up(val):
                        self.drone.shutdown()
                        raise RuntimeHardwareErrorException(f"Could not complete maneuver")
                    self.drone_tracking.up(val)
                    self.drone_path.append(self.drone_tracking.get_state()['loc'][:])
                case "DOWN":
                    val = current_line[1].value
                    if current_line[1].token_type == "NumReg":
                        val = int(val)
                        if 0 <= val < len(self.num_reg):
                            val = self.num_reg[val]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[1].token_type == "IntNumber":
                        val = int(val)
                    elif current_line[1].token_type == "FloatNumber":
                        val = float(val)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    val = int(val)
                    if not self.drone.down(val):
                        self.drone.shutdown()
                        raise RuntimeHardwareErrorException(f"Could not complete maneuver")
                    self.drone_tracking.down(val)
                    self.drone_path.append(self.drone_tracking.get_state()['loc'][:])
                case "ROTATE_CW":
                    val = current_line[1].value
                    if current_line[1].token_type == "NumReg":
                        val = int(val)
                        if 0 <= val < len(self.num_reg):
                            val = self.num_reg[val]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[1].token_type == "IntNumber":
                        val = int(val)
                    elif current_line[1].token_type == "FloatNumber":
                        val = float(val)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    val = int(val)
                    if not self.drone.rotate_cw(val):
                        self.drone.shutdown()
                        raise RuntimeHardwareErrorException(f"Could not complete maneuver")
                    self.drone_tracking.rotate_cw(val)
                    self.drone_path.append(self.drone_tracking.get_state()['loc'][:])
                case "ROTATE_CCW":
                    val = current_line[1].value
                    if current_line[1].token_type == "NumReg":
                        val = int(val)
                        if 0 <= val < len(self.num_reg):
                            val = self.num_reg[val]
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[1].token_type == "IntNumber":
                        val = int(val)
                    elif current_line[1].token_type == "FloatNumber":
                        val = float(val)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Unknown value type.")
                    val = int(val)
                    if not self.drone.rotate_ccw(val):
                        self.drone.shutdown()
                        raise RuntimeHardwareErrorException(f"Could not complete maneuver")
                    self.drone_tracking.rotate_ccw(val)
                    self.drone_path.append(self.drone_tracking.get_state()['loc'][:])
                # Eval/Debug Operations
                case "DISPLAY":
                    if current_line[1].token_type == "NumReg":
                        reg = int(current_line[1].value)
                        if 0 <= reg < len(self.num_reg):
                            val = self.num_reg[reg]
                            print(val)
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[1].token_type == "PicReg":
                        reg = int(current_line[1].value)
                        if 0 <= reg < len(self.pic_reg):
                            val = self.pic_reg[reg]
                            cv2.imshow("DroneASM", val)
                            cv2.waitKey(1)
                        else:
                            self.drone.shutdown()
                            raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    elif current_line[1].token_type == "IntNumber":
                        val = int(current_line[1].value)
                        print(val)
                    elif current_line[1].token_type == "FloatNumber":
                        val = float(current_line[1].value)
                        print(val)
                    elif current_line[1].token_type == "String":
                        print(current_line[1].value)
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Attempted display of unknown value.")
                # Camera Operations
                case "TAKE_PIC":
                    reg = int(current_line[1].value)
                    if 0 <= reg < len(self.pic_reg):
                        while self.drone.last_frame is None:
                            pass
                        self.pic_reg[reg] = self.drone.get_frame()
                    else:
                        self.drone.shutdown()
                        raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                # Computer vision operations
                # LOAD_PIC <filename> <pic_reg>
                # DETECT_FACE <pic_reg> <num_reg> <num_reg> <num_reg> <num_reg>
                # ENCODE_FACE <pic_reg> <name> <num_reg> <num_reg> <num_reg> <num_reg>
                # DETECT_PERSON <pic_reg> <name> <num_reg> <num_reg> <num_reg> <num_reg>
                case "LOAD_PIC":
                    filename = current_line[1].value
                    reg = int(current_line[2].value)
                    if 0 <= reg < len(self.pic_reg):
                        try:
                            self.pic_reg[reg] = cv2.imread(filename)
                        except:
                            raise RuntimeSoftwareErrorException(f"Attempted open non-existent or non-image file.")
                    else:
                        raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                case "DETECT_FACE":
                    p_reg = int(current_line[1].value)
                    f_reg = int(current_line[2].value)
                    ret_reg = int(current_line[3].value)
                    if not (0 <= p_reg < len(self.pic_reg)):
                        raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    if not (0 <= f_reg < len(self.face_reg)):
                        raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    if not (0 <= ret_reg < len(self.num_reg)):
                        raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    faces = find_faces(self.pic_reg[p_reg])
                    if len(faces) > 0:
                        self.num_reg[ret_reg] = 1
                        self.face_reg[f_reg] = (faces[0], encode_face(self.pic_reg[p_reg], faces[0]))
                    else:
                        self.num_reg[ret_reg] = 0
                case "MATCH_FACE":
                    f_reg1 = int(current_line[1].value)
                    f_reg2 = int(current_line[2].value)
                    ret_reg = int(current_line[3].value)
                    if not (0 <= f_reg1 < len(self.face_reg)):
                        raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    if not (0 <= f_reg2 < len(self.face_reg)):
                        raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    if not (0 <= ret_reg < len(self.num_reg)):
                        raise RuntimeSoftwareErrorException(f"Attempted use of non-existent register.")
                    if self.face_reg[f_reg1][1] is None or self.face_reg[f_reg2][1] is None:
                        raise RuntimeSoftwareErrorException(f"Attempted to use empty face register.")
                    self.num_reg[ret_reg] = face_similarity(self.face_reg[f_reg1][1], self.face_reg[f_reg2][1])
                # By default, close the drone down and stop.
                case _:
                    self.drone.shutdown()
                    raise RuntimeSoftwareErrorException(f"Unknown command.")
            if not jumped:
                program_counter += 1
        self.drone.shutdown()
        cv2.destroyAllWindows()
        return self.drone_path
