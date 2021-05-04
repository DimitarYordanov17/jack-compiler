# Jack -> Machine code compiler. @DimitarYordanov17

# To use: python3 compiler.py {-add_bootstrap_code} {-keep_xml} {-keep_vm} {-keep_asm}
# - compiles the current directory

# Parameters:
# add_bootstrap_code: add binary code which initializes the stack pointer to 256. (yes by default) WARNING: If this is not initialized manually and the argument is False, the program might not work
# keep_xml: keep medium .xml files, which were used in the compilation proccess. (no by default)
# keep_vm: keep medium .vm files, which were used in the compilation proccess. (no by default)
# keep_asm: if the path is a dir, a .asm file will be kept for every .jack file (no by default)


import sys
import time
import os

from lib.front_end_translator.jackTranslator import JackTranslator
from lib.virtual_machine_translator.virtualMachine import VirtualMachineTranslator
from lib.assembler.assembler import Assembler

def compile(add_bootstrap_code, keep_xml, keep_vm, keep_asm):
    """
    Compile a file/dir. Keeping of medium files and addition of bootstrap code is optional.
    """
    starting_time = time.time()
    file_names = []

    for root, dirs, files in os.walk('.'):
        for file_name in files:
            if file_name.endswith(".jack"):
                file_names.append(file_name.split('.')[0])
        break 

    # Jack -> VM (+ XML optionally)
    JackTranslator.translate('.', generate_xml=keep_xml)

    # VM -> Hack
    VirtualMachineTranslator.translate('.', keep_asm, add_bootstrap_code)

    if not keep_vm:
        for file_name in file_names:
            os.system(f"rm {file_name}.vm")

    # Hack -> Machine code
    Assembler.assemble("out.asm")
    
    if not keep_asm:
        os.system("rm out.asm")

    print(f"The compilation finished under {time.time() - starting_time} seconds")

def get_arguments():
    """
    Validate input arguments and prepare them for passing to compile()
    """

    optional_arguments = dict(arg.split('=') for arg in sys.argv[1:])

    optional_arguments_names = ["add_bootstrap_code", "keep_xml", "keep_vm", "keep_asm"]
    optional_arguments_values = [True, False, False, False]
    
    # Validate optional arguments
    for argument_name, argument_value in optional_arguments.items():
        argument_value = argument_value.lower()

        if argument_name not in optional_arguments_names:
            print(f"Incorrect argument name {argument_name}")
            exit()

        if "yes" not in argument_value and "no" not in argument_value:
            print(f"Incorrect value for argument {argument_name}")
            exit()

        argument_index = optional_arguments_names.index(argument_name)
        optional_arguments_values[argument_index] = "yes" in argument_value
    
    return optional_arguments_values

optional_arguments_values = get_arguments()
compile(*optional_arguments_values)
