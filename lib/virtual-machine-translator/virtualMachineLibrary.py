# An assembly library for the VM code > Hack machine language translation. @DimitarYordanov17

class VirtualMachineLibrary:
    """
    Main class to map the Virtual Machine intermediate language to Hack machine language
    """

    def _get_primary(operation, a=None, b=None, treat_a_as_pointer=True, treat_b_as_pointer=True):
        """
        Define primary operations, which are going to be main building "blocks" of higher instructions
        """

        bytecode_dictionary = {
            "sp++": ["@SP", "M=M+1"],
            "sp--": ["@SP", "M=M-1"],
        }

        if operation == "*a=*b":
            load_b_into_d = [f"@{b}", "D=M"]

            if treat_b_as_pointer:
                load_b_into_d.insert(1, "A=M")

            load_d_into_a = [f"@{a}", "M=D"]

            if treat_a_as_pointer:
                load_d_into_a.insert(1, "A=M")

            load_b_into_a = load_b_into_d + load_d_into_a

            return load_b_into_a

        else:
            return bytecode_dictionary[operation]

    def get_arithmetic(instruction, function_block, file_name, total_instructions):
        """
        Returns bytecode for arithmetic instructions
        add | x + y
        sub | x - y
        neg | - y
        eq  | x == y
        gt  | x > y
        lt  | y < x
        and | x && y
        or  | x || y
        not | !y
        """

        direct_arithmetic_commands = {"add": "+", "sub": "-", "and": "&", "or": "|"}
        conditional_arithmetic_commands = {"eq": "JEQ", "gt": "JGT", "lt": "JLT"}  # I can just preppend "J" to the type and .upper(), because they match, but the symmetry would be ruined
        unary_commands = ["neg", "not"]

        final_bytecode = []

        if instruction in direct_arithmetic_commands:
            final_bytecode.extend(VirtualMachineLibrary._get_primary("sp--"))  # sp--
            final_bytecode.extend(["@SP", "A=M", "D=M"])  # D=*sp

            final_bytecode.extend(VirtualMachineLibrary._get_primary("sp--"))  # sp--
            final_bytecode.extend(
                ["@SP", "A=M", f"D=M{direct_arithmetic_commands[instruction]}D"])  # D=*sp (operand)  D

            final_bytecode.extend(["@SP", "A=M", "M=D"])  # *sp = D
            final_bytecode.extend(VirtualMachineLibrary._get_primary("sp++"))  # sp++

        elif instruction in conditional_arithmetic_commands:
            final_bytecode.extend(VirtualMachineLibrary._get_primary("sp--"))  # sp--
            final_bytecode.extend(["@SP", "A=M", "D=M"])  # D=*sp

            final_bytecode.extend(VirtualMachineLibrary._get_primary("sp--"))  # sp--
            final_bytecode.extend(["@SP", "A=M", "D=M-D"])  # D=*sp -  D

            write_none_label = ":".join([file_name, function_block, str(total_instructions + 17), "WRITENONE"])
            increment_sp_label = ":".join([file_name, function_block, str(total_instructions + 20), "INCREMENTSP"])

            final_bytecode.extend([f"@{write_none_label}",
                                   f"D;{conditional_arithmetic_commands[instruction]}"])  # @WRITENONE, jump if the corresponding condition matches with D"s (x-y) value

            final_bytecode.extend(["@SP", "A=M", "M=0"])  # (WRITEZERO) block, *sp=0 (false)
            final_bytecode.extend(
                [f"@{increment_sp_label}", "0;JMP"])  # Jump instantly to sp++ part, skipping write -1

            final_bytecode.extend([f"({write_none_label})", "@SP", "A=M", "M=-1"])  # (WRITENONE) block, *sp=-1 (true)
            
            final_bytecode.extend([f"({increment_sp_label})"])
            final_bytecode.extend(VirtualMachineLibrary._get_primary("sp++"))  # sp++

        else:  # unary command
            final_bytecode.extend(VirtualMachineLibrary._get_primary("sp--"))  # sp--

            final_bytecode.extend(["@SP", "A=M", "D=M"])  # D=*sp

            if instruction == "not":
                final_bytecode.extend(["@SP", "A=M", "M=!D"])  # *sp = !D
            else:
                final_bytecode.extend(["@SP", "A=M", "M=-D"])

            final_bytecode.extend(VirtualMachineLibrary._get_primary("sp++"))  # sp++

        return final_bytecode

    def get_memory(instruction, file_name):
        """
        Returns the full memory access bytecode, which consists of:
        1. Loading address calculation in R13
        2. Decrementing SP, if pop else saving R13"s content into current SP available location
        3. Saving SP value in R13, if pop else incrementing SP
        """

        instruction_structure = instruction.split()
        instruction_type = instruction_structure[0]
        segment = instruction_structure[1]
       
        index = instruction_structure[2]
       

        calculated_address_bytecode = VirtualMachineLibrary._get_address_calculation(segment, index, file_name)

        if instruction_type == "push":
            treat_b_as_pointer = segment != "constant"  # If we don"t have a constant segment, then b (R13 in this case) must be treated as a pointer

            save_R13_into_stack_bytecode = VirtualMachineLibrary._get_primary("*a=*b", a="SP", b="R13",
                                                                              treat_b_as_pointer=treat_b_as_pointer)
            increment_sp = VirtualMachineLibrary._get_primary("sp++")

            return calculated_address_bytecode + save_R13_into_stack_bytecode + increment_sp

        else:
            decrement_sp = VirtualMachineLibrary._get_primary("sp--")
            save_stack_into_R13 = VirtualMachineLibrary._get_primary("*a=*b", a="R13", b="SP")

            return calculated_address_bytecode + decrement_sp + save_stack_into_R13

    def _get_address_calculation(segment, index, file_name):
        """
        Returns bytecode that loads address calculation (segment base address + index) in R13
        """

        if segment == "constant":  # Temp starts at 5
            load_bytecode = [f"@{index}", "D=A"]

        elif segment == "temp":
            load_bytecode = [f"@{int(index) + 5}", "D=A"]

        elif segment == "static":
            variable_name = file_name + "." + index
            load_bytecode = [f"@{variable_name}", "D=A"]

        elif segment == "pointer":
            if index == "0":
                register = "THIS"
            else:
                register = "THAT"

            load_bytecode = [f"@{register}", "D=A"]

        else:
            load_bytecode = [f"@{VirtualMachineLibrary._get_symbolic_symbol(segment)}", "D=M", f"@{index}", "D=D+A"]

        full_address_bytecode = load_bytecode + ["@R13", "M=D"]
        return full_address_bytecode

    def _get_symbolic_symbol(segment):
        """
        Returns Hack symbolic symbol equivalents
        """

        bytecode_dictionary = {
            "local": "LCL",
            "argument": "ARG",
            "this": "THIS",
            "that": "THAT",
        }

        try:
            return bytecode_dictionary[segment]
        except:  # If the segment is not available, it is most likely a variable, so just return it
            return segment

    def get_program_flow(instruction, label, function_block):
        """
        Returns full program flow instruction bytecode
        1. goto label
        2. label
        3. if-goto label
        """

        if instruction == "label":  # Set a label
            bytecode = [f"({function_block}{'$' if function_block else ''}{label})"]
        elif instruction == "goto": # Unconditional jumping
            bytecode = [f"@{label}", "0;JMP"]
        else: # Conditional jumping
            bytecode = []

            # Pop into D
            bytecode.extend(VirtualMachineLibrary._get_primary("sp--"))
            bytecode.extend(["@SP", "A=M", "D=M"])

            # Jump if D is not 0
            bytecode.extend([f"@{function_block}{('$' if function_block else '')}{label}", "D;JNE"])

        return bytecode

    def get_function(instruction_structure, total_instructions, file_name):
        """
        Returns full function instruction bytecode
        function function_name lVars
        call function_name nArgs
        return
        """

        state = ["LCL", "ARG", "THIS", "THAT"]
        instruction = instruction_structure[0]

        if instruction == "function":
            function_name = instruction_structure[1]
            vars_count = int(instruction_structure[2])
            
            bytecode = []
            
            # Start a function block
            bytecode.extend([f"({function_name})"])

            for _ in range(vars_count):
                bytecode.extend(VirtualMachineLibrary.get_memory("push constant 0", file_name)) 

        elif instruction == "call": 
            function_name = instruction_structure[1]
            args_count = instruction_structure[2]
            
            bytecode = []
            
            return_label = ":".join([file_name, function_name, str(total_instructions), "RETURN"])

            # Push return address
            bytecode.extend([f"@{return_label}"])
            bytecode.extend(["D=A", "@SP", "A=M", "M=D"])
            bytecode.extend(VirtualMachineLibrary._get_primary("sp++"))

            # Save state
            for address in state:
                bytecode.extend([f"@{address}", "D=M", "@R13", "M=D"])
                bytecode.extend(VirtualMachineLibrary._get_primary("*a=*b", a="SP", b="R13", treat_b_as_pointer=False))
                bytecode.extend(VirtualMachineLibrary._get_primary("sp++"))

            # Set ARG to point to new base address (sp - 5 - args_count)
            bytecode.extend(["@SP", "D=M", "@5", "D=D-A", f"@{args_count}", "D=D-A", "@ARG", "M=D"])
            
            # Set LCL to point to current SP
            bytecode.extend(["@SP", "D=M", "@LCL", "M=D"])
            
            # Jump to function_name
            bytecode.extend([f"@{function_name}", "0;JMP"])
            
            # Set return label
            bytecode.extend([f"({return_label})"])

            bytecode = bytecode

        else:
            bytecode = []

            # Set R13 to point to callee"s LCL
            bytecode.extend(["@LCL", "D=M", "@R13", "M=D"])

            # Set R14 to return address
            bytecode.extend(["@R13", "D=M", "@5", "D=D-A", "A=D", "D=M", "@R14", "M=D"])

            # Set first callee"s argument to be return value
            bytecode.extend(VirtualMachineLibrary._get_primary("sp--"))
            bytecode.extend(VirtualMachineLibrary._get_primary("*a=*b", a="ARG", b="SP"))

            # Reposition SP to be after first callee"s argument
            bytecode.extend(["@ARG", "D=M+1", "@SP", "M=D"])
            
            # Restore registers
            for index, address in enumerate(reversed(state)):
                bytecode.extend(["@R13", "D=M", f"@{int(index) + 1}", "D=D-A", "A=D", "D=M", f"@{address}", "M=D"])
            
            # Return jump
            bytecode.extend(["@R14", "A=M", "0;JMP"])
        
        return bytecode
