Welcome to DroneASM!
====================
DroneASM is an assembly-style language for controlling drones, in particular DJI Tello drones.
----------------------------------------------------------------------------------------------

Why DroneASM?
=============
DroneASM is designed to be easy to pick up for first-time programmers, while being powerful enough for those that
already know how to program. While I recommend that programmers use a more sophisticated language like Python or Java
for heavy duty Tello automation DroneASM hides a lot of that complexity and gets you up and flying fast.

The primary reason behind the development of DroneASM is for educational use. By using an assembly language paradigm
DroneASM hides much of the complexity of a "real" programming langauge (such as variable declaration, naming, etc.)
and gives a more simplistic domain for program creation. THe hop is that this simplification can reduce the required
instruction time to get students thinking about and solving basic drone automation tasks.

How does DroneASM work?
=======================
DroneASM works by compiling DroneASM code into a series of tokenized lines which are then processed on an ideal virtual
machine. In practice, this virtual machine is a lot nicer than most virtual machines (like the JVM) and provides a
robust set of features. At its base this virtual machine acts as a controller for the Tello drone and a place to perform
mathematical, recognition, and automation operations.

Like any other programming language DroneASM processes code files line by line, starting at the top and going to the
bottom (barring any programmed jumps.) DroneASM is a (relatively) small language consisting of the following (??)
commands (see command manual for more):

Variable Operations:
STORE
COPY
COPY_PIC
PUSH_NUM
PUSH_RETURN
PUSH_PIC
POP_NUM
POP_PIC
POP_RETURN

Flow Control Operations:
BRANCH_EQ
BRANCH_NE
BRANCH_GT
BRANCH_LT
BRANCH_GE
BRANCH_LE
JUMP
JUMP_RETURN
NOP
HALT

Math Operations:
ADD
SUB
MULT
DIV
IDIV
RDIV

Drone Operations:
FORWARD
BACKWARD
LEFT
RIGHT
UP
DOWN
ROTATE_CW
ROTATE_CCW

Evaluation/Debug Operations:
DISPLAY

Camera Operations:
TAKE_PIC

Computer Vision Operations:
LOAD_PIC
DETECT_FACE
MATCH_FACE


Comments are denoted by #, all characters after the # on a line are ignored.
NOTE: As of now a # in a string will be counted as the start of a comment
No multiline commenting is available

How big is the DroneASM virtual machine?
========================================
The DroneASM virtual machine consists of the following:
16 general purpose numerical registers ($R1 - $R16)
8 picture registers ($P1 - $P8)
8 face registers ($F1 - $F8)
1 Return address register (Not directly settable)
1 general purpose numerical value stack
1 picture stack
1 return address stack

These values are somewhat configurable, if you wish to modify the DroneASM virtual machine source code.
