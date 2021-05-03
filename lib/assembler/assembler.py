# A Python assembler for the Hack machine language. @DimitarYordanov17
# To run: python3 assembler.py {your .asm file}

from lib.assembler.assemblerLibrary import AssemblerLibrary
import os
import sys

class Assembler:
  '''
  Main assembler class, several functions available, note that the input file should first be cleaned, symbolically preprocessed and finally translated
  '''

  def assemble(path: str):
    '''
    Clean, apply symbolic preprocessing and translate a file
    '''
    
    intermediate_file = "program_intermediate.asm"
    os.system(f"cp {path} {intermediate_file}")

    output_file = path.split('.')[0] + ".hack"

    Assembler.clean(intermediate_file)

    Assembler.symbolic_preprocessor(intermediate_file)
    
    Assembler.translate(intermediate_file, output_file)

    os.system(f"rm {intermediate_file}")

  def symbolic_preprocessor(input_file):
    '''
    1. Construct a jump and variables symbolic table
    2. Translate via the symbolic table
    '''
    symbolic_table = dict()
    variables = 0

    with open(input_file, "r+") as f:
      lines = f.readlines()
      
      # Build jump symbolic table part
      for index, line in enumerate(lines):
        if line[0] == "(":
          symbolic_table[line[1:-2]] = index - len(symbolic_table.keys())

      # Build registers symbolic table part
      for line in lines:
        if "@" in line:
          address = line[1:].strip()

          if (not address.isnumeric()) and (address not in symbolic_table.keys()):
            address_request = AssemblerLibrary.get_register(address)

            if address_request == "VARIABLE":
              symbolic_table[address] = 16 + variables
              variables += 1
      
      f.seek(0)
        
      for line in lines:
        if line[0] == "@" and not line[1:].strip().isnumeric():
          address = line[1:].strip()

          if address in symbolic_table.keys():
            bytecode = symbolic_table[address]
          else:
            bytecode = AssemblerLibrary.get_register(address)
          
          f.write("@" + str(bytecode) + "\n")

        elif line[0] != "(":
          f.write(line)

      f.truncate()

  def clean(input_file):
    '''
    Remove unnecesary whitespaces and comments
    '''

    with open(input_file, "r+") as f:
      lines = f.readlines()
      f.seek(0)
      for line in lines:
        spaceless_line = line.replace(" ", "").lstrip()

        if line != '\n':
            if "/" in spaceless_line:
              divided_line = spaceless_line.split("/")
              if divided_line[0] and divided_line[0] != "*":
                f.write(divided_line[0] + '\n')

            elif "*" not in spaceless_line:
              f.write(spaceless_line)
              
      f.truncate()

  def translate(input_file, output_file):
    '''
    Translate a prepared file
    '''

    with open(input_file, "r+") as f, open(output_file, 'w') as of:
      lines = f.readlines()
      
      of.seek(0)
      
      for line in lines:
        line = line.strip()
         
        instruction_type = '0' if "@" in line else '1'

        if instruction_type == '0':
          address = line[1:]
          binary_code = f"{int(address):015b}"
          machine_code = instruction_type + binary_code

        else:
          if "=" in line:
            splitted_instruction = line.split('=')
            destination = splitted_instruction[0]
            computation = splitted_instruction[1]
            jump = ""
          else:
            splitted_instruction = line.split(';')
            computation = splitted_instruction[0]
            jump = splitted_instruction[1]
            destination = ""

          machine_code_destination = AssemblerLibrary.get_destination(destination)
          machine_code_jump = AssemblerLibrary.get_jump(jump)
          machine_code_computation = AssemblerLibrary.get_computation(computation)

          machine_code = instruction_type + "11" + machine_code_computation + machine_code_destination + machine_code_jump 
        
        of.write(machine_code + '\n')
