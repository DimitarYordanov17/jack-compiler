# A library file to include the machine language and dictionariy specifications of the Hack language. @DimitarYordanov17

class AssemblerLibrary:
  '''
  Main class to map the Hack syntax to internal machine language bytecode
  '''

  def get_jump(jump: str):
    '''
    Return bytecode of jump commands
    '''
    bytecode =  {
      ''   : '000',
      'JGT': '001',
      'JEQ': '010',
      'JGE': '011',
      'JLT': '100',
      'JNE': '101',
      'JLE': '110',
      'JMP': '111',
    }

    return bytecode[jump]

  def get_destination(destination: str):
    '''
    Return bytecode of destination commands
    '''
    bytecode = {
      ''   : '000',
      'M'  : '001',
      'D'  : '010',
      'MD' : '011',
      'A'  : '100',
      'AM' : '101',
      'AD' : '110',
      'AMD': '111',
    }

    return bytecode[destination]

  def get_computation(computation):
    '''
    Return bytecode of computation commands
    '''
    bytecode = {
      '0'  : '0101010',
      '1'  : '0111111',
      '-1' : '0111010',
      'D'  : '0001100',
      'A'  : '0110000',
      '!D' : '0001101',
      '!A' : '0110001',
      '-D' : '0001111',
      '-A' : '0110011',
      'D+1': '0011111',
      'A+1': '0110111',
      'D-1': '0001110',
      'A-1': '0110010',
      'D+A': '0000010',
      'D-A': '0010011',
      'A-D': '0000111',
      'D&A': '0000000',
      'D|A': '0010101',
      'M'  : '1110000',
      '!M' : '1110001',
      '-M' : '1110011',
      'M+1': '1110111',
      'M-1': '1110010',
      'D+M': '1000010',
      'D-M': '1010011',
      'M-D': '1000111',
      'D&M': '1000000',
      'D|M': '1010101',
    }
    
    try: # Handle differences, e.g. 'M+D'=='D+M'
        return bytecode[computation]
    except:
        return bytecode[computation[::-1]]

  def get_register(register):
    '''
    Return bytecode of built-in registers
    '''
    bytecode_mnemonics = {
      'SP'    : 0,
      'LCL'   : 1,
      'ARG'   : 2,
      'THIS'  : 3,
      'THAT'  : 4,
      'SCREEN': 0x4000,
      'KBD'   : 0x6000,
    }
    
    if register in ['R' + str(n) for n in range(0, 16)]:
      if len(register) == 2:
        return int(register[1])
      
      return int(register[1] + register[2])

    elif register in bytecode_mnemonics.keys():
      return bytecode_mnemonics[register]

    else:
      return "VARIABLE"
