# A virtual machine translator. Intermediate code, supplied by front-end compiler, to Hack machine language. @DimitarYordanov7

# To run: python3 virtualMachine.py {your .vm file} {yes/no, should distinct .asm files be kept} {yes/no, should bootstrap code be added}

from virtualMachineLibrary import VirtualMachineLibrary
import os
import sys


class VirtualMachineTranslator:
    """
    Main class, capable of processing a full directory, with .vm files resulting in one .asm file
    """

    BOOTSTRAP_CODE = ["@256", "D=A", "@SP", "M=D"]

    def translate(path, keep_disctint_files, add_bootstrap_code):
        """
        Translate a path - create out.asm, add? bootstrap code, add? translated Sys.vm, add remaining translated .vm files
        """

        vm_files = []

        for root, dirs, files in os.walk(path):
            for file_name in files:
                if ".vm" in file_name:
                    vm_files.append(file_name)
            break

        with open("out.asm", "w") as output_file:
            if add_bootstrap_code:
                output_file.write("// bootstrap code \n")
                for instruction in VirtualMachineTranslator.BOOTSTRAP_CODE:
                    output_file.write(instruction + "\n")

            if "Sys.vm" in vm_files:
                VirtualMachineTranslator.translate_file("Sys.vm")
                sys_file = open("Sys.asm", "r")
                output_file.write(sys_file.read())
                vm_files.remove("Sys.vm")
                if not keep_disctint_files:
                    os.system("rm Sys.asm")

            for vm_file_name in vm_files:
                VirtualMachineTranslator.translate_file(vm_file_name)
                vm_file = open(vm_file_name.split(".")[0] + ".asm", "r")
                output_file.write(vm_file.read())
        
        if not keep_disctint_files:
            for file_name in vm_files:
                asm_file_name = file_name.split(".")[0] + ".asm"
                os.system(f"rm {asm_file_name}")

    def translate_file(input_file_name):
        """
        Fully translate a file
        """

        output_file_name = input_file_name.split(".")[0] + ".asm"
        os.system(f"cp {input_file_name} {output_file_name}")
        VirtualMachineTranslator.clean(output_file_name)
        VirtualMachineTranslator.parse_file(output_file_name) 

    def parse_file(input_file_name):
        """
        Parse every instruction and write the requested and further translated equivalent
        """

        with open(input_file_name, "r+") as input_file:
            last_function = ""
            instructions = input_file.readlines()
            input_file.seek(0)
            total_instructions = 0

            for line in instructions: 
                instruction_structure = line.split()
                instruction = instruction_structure[0]

                bytecode_instruction = []
                
                if len(instruction_structure) == 1 and instruction != "return":  # Stack arithmetic
                    bytecode_instruction = VirtualMachineLibrary.get_arithmetic(instruction, last_function, input_file_name.split(".")[0], total_instructions)

                elif instruction in ["pop", "push"]:  # Memory access
                    bytecode_instruction = VirtualMachineLibrary.get_memory(line, input_file_name.split(".")[0])

                elif len(instruction_structure) == 2:  # Program flow
                    label = instruction_structure[1]
                    bytecode_instruction = VirtualMachineLibrary.get_program_flow(instruction, label, last_function)

                else:  # Function calling
                    if instruction == "function":
                        last_instruction = instruction_structure[1]

                    bytecode_instruction = VirtualMachineLibrary.get_function(instruction_structure, total_instructions, input_file_name.split(".")[0])

                input_file.write(f"// {line}")

                for instruction in bytecode_instruction:
                    total_instructions += 1
                    input_file.write(instruction + "\n")

            input_file.truncate()

    def clean(input_file):
        """
        Remove unnecesary whitespaces and comments
        """

        with open(input_file, "r+") as f:
            lines = f.readlines()
            f.seek(0)
            for line in lines:
                if line != "\n":
                    if "//" in line:
                        line_elements = line.lstrip().split("//")
                        if line_elements[0]:
                            f.write(line_elements[0].rstrip() + "\n")
                    else:
                        f.write(line)
            f.truncate()

VirtualMachineTranslator.translate(sys.argv[1], True if sys.argv[2] == "yes" else False, True if sys.argv[3] == "yes" else False)
