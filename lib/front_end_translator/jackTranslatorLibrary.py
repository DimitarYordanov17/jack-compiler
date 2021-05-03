# An intermediate code library for the Jack > Intermediate (VM) code translation. @DimitarYordanov17

from jackStandardLibrary import JackStandardLibrary
import re
import copy

class JackTranslatorLibrary:
    """
    A main library class capable of Jack language syntax analysis and VM code generation
    """


    SYNTAX_ELEMENTS = {

        "symbols": ['{', '}', '(', ')', '[', ']', '.', ',', ';', '+', '-', '*', '/', '&', '|', '<', '>', '=', '~'],

        "subroutines": ['constructor', 'function', 'method'],
        
        "primitive_types": ['var', 'static', 'field'],

        "statements": ['let', 'if', 'while', 'do', 'return'],

        "op": ['+', '-', '*', '/', '&', '~', '|', '<', '>', '='],

        "keywords": ['class', 'constructor', 'function',
                     'method', 'field', 'static', 'var',
                     'int', 'char', 'boolean', 'void', 'true',
                     'false', 'null', 'this', 'let', 'do',
                     'if', 'else', 'while', 'return'],
    }

    def translate_file(input_file_name, global_scope_subroutines):
        """
        Handle the translation of a file
        """
                
        jack_translator = JackTranslatorLibraryCodeGenerator(input_file_name, global_scope_subroutines)
        vm_code = jack_translator.translate()

        return vm_code

    def get_file_subroutines(input_file_name):
        """
        Return a classified dictionary of all subroutines in the file and their properties
        """
        subroutines_lib = {}

        jack_translator = JackTranslatorLibraryCodeGenerator(input_file_name, []) # Initialize with an empty global subroutines array

        jack_translator._strip_input_commands()
        jack_translator._get_class_info()
        jack_translator._get_subroutines()
        
        class_name = jack_translator.class_info[0]
        subroutines_lib[class_name] = {}

        for subroutine_name, subroutine_declaration in jack_translator.subroutines.items():
            properties = subroutine_declaration[0][:subroutine_declaration[0].index("<symbol> ) </symbol>") + 1]
  
            subroutine_kind, subroutine_type = JackTranslatorLibraryParser._get_tag_value("", properties[0]), JackTranslatorLibraryParser._get_tag_value("", properties[1])
            subroutine_param_list = properties[properties.index("<symbol> ( </symbol>"):] 

            subroutines_lib[class_name][subroutine_name] = [subroutine_kind, subroutine_type, subroutine_param_list]
        
        return subroutines_lib

    def parse_file(input_file_name):
        """
        Makes use of the JackTranslatorLibraryParser class to generate a .xml file from a .jack one
        """

        jack_parser = JackTranslatorLibraryParser(input_file_name)
        jack_parser.parse()


    def tokenize(input_file_name):
        """
        Tokenizes a file, spreading each keyword (token) on a newline
        """

        with open(input_file_name, 'r+') as input_file:
            input_file.seek(0)
            file_text = input_file.read()

            # Clean trailing spaces
            file_text = file_text.strip()

            # Clean all \n
            file_text = file_text.replace("\n", " ")

            # Clean spaces, without breaking the string
            # BTW I spent too much time on this but in the end I see that
            # I could use regex for the entire compiler...
            # If I find time to rework the whole thing, I might find a way
            # to do it with regexes for optimization.
            # All the added complexity is here just so I can parse strings the correct way.

            strings = re.findall(r'"[^"]*"', file_text)
            non_string_file_text = re.split(r'(?:"[^"]*")', file_text)

            refactored_text = []

            for index, non_string in enumerate(non_string_file_text):
                while "  " in non_string:
                    non_string = non_string.replace("  ", " ")

                for symbol in JackTranslatorLibrary.SYNTAX_ELEMENTS["symbols"]:
                    widened_symbol = " " + symbol + " "
                    non_string = non_string.replace(symbol, widened_symbol)

                refactored_text.extend(non_string.split())

                try:
                    refactored_text.append(strings[index])
                except:
                    break

            input_file.seek(0)

            for token in refactored_text:
                classified_token = JackTranslatorLibrary._classify_token(token)
                input_file.write(classified_token + '\n')

            input_file.truncate()

    def clean(input_file_name):
        """
        Removes all comments in a file, but keeps line spacing
        (have to be careful to not remove a line which contains
        division, signed by '/' or string, containing it)
        """

        with open(input_file_name, 'r+') as input_file:
            lines = input_file.readlines()
            input_file.seek(0)

            in_comment = False

            for line in lines:
                if "/*" in line or "//" in line:
                    comment = r"//" if "//" in line else r"/\*"
                    string_to_write, enter_comment = JackTranslatorLibrary._proccess_comment(line, comment)

                    in_comment = enter_comment

                    if string_to_write != '\n' and string_to_write != '':
                        input_file.write(string_to_write)

                elif (len(line.strip()) >= 2) and ("*/" == (line.strip()[-2] + line.strip()[-1])):
                    in_comment = False

                elif (not in_comment) and line != '\n':
                    input_file.write(line)

            input_file.truncate()


    def tabularize(input_file_name):
        """
        Indent every tag between two upper tags, keep nested depth
        """

        with open(input_file_name, 'r+') as input_file:
            lines = input_file.readlines()
            input_file.seek(0)

            depth = 0

            for line in lines:
                tabularized_line = ('\t' * depth) + line

                if " " not in line:
                    if "/" in line:
                        depth -= 1
                        tabularized_line = ('\t' * depth) + line
                    else:
                        depth += 1

                input_file.write(tabularized_line)


    def _classify_token(token):
        """
        Appends a certain type tags to a token 
        """

        token_type = ""

        if token in JackTranslatorLibrary.SYNTAX_ELEMENTS["keywords"]:
            token_type = "keyword"

        elif token in JackTranslatorLibrary.SYNTAX_ELEMENTS["symbols"]:
            token_type = "symbol"

        elif '"' in token:
            token_type = "stringConstant"

        elif token[0].isnumeric():
            token_type = "integerConstant"

        else:
            token_type = "identifier"

        classified_token = f"<{token_type}> {token} </{token_type}>"

        return classified_token


    def _proccess_comment(line, comment):
        """
        Returns a string, that should be written and a boolan to indicate if we are entering a block comment
        """

        line = line.rstrip()
        comment_occurrences = [occurence.span()[0] for occurence in re.finditer(comment, line)]

        string_to_write = line + '\n'
        enter_block_comment = False

        for comment_start_index in comment_occurrences:
            before_comment_segment = line[:comment_start_index]
            double_quotes_count = before_comment_segment.count('"')

            if double_quotes_count % 2 == 0:  # We have a comment, because all possible string are closed
                if before_comment_segment.replace(" ", ""):
                    string_to_write = before_comment_segment + '\n'

                else:
                    string_to_write = ""

                if "/*" in line:
                    last_two_chars = line[-2] + line[-1]
                    enter_block_comment = True

                    if last_two_chars == "*/":
                        enter_block_comment = False

                break

        return string_to_write, enter_block_comment


class JackTranslatorLibraryCodeGenerator:
    """
    Responsible for the VM code generation of Jack commands and other auxiliary functions (such as building symbolic table)
    XML -> VM.
    
    More information on the translating logic:
    // We have a basic initialization where each instance contains input_commands (all the XML tags) and
    // subroutines (a dictionary - subroutine_name: [subroutine_declaration, subroutine_symbolic_table, vm_code]).
    // Next, we translate all the class information (class variables...). After that we go through every
    // subroutine and we translate it into VM code, using its own symbolic table. Technically to translate a file means
    // to fill up instance's vm_code attribute
    """

    OPERATIONS = {  "+": "add", "-": "sub", "&": "and", "|": "or",
                    "*": "call Math.multiply 2", "/": "call Math.divide 2",
                    ">": "gt", "<": "lt", "=": "eq"
                }

    def __init__(self, input_file_name, global_scope_subroutines):
        # KEEP IN MIND: There is a difference in the format of the global scope subroutine param lists and standard library param lists.
        self.input_commands = open(input_file_name, 'r').readlines()
        self.symbolic_table = []
        self.vm_code = []

        self.global_subroutines = global_scope_subroutines
        self.global_identifiers = self._get_global_subroutine_identifiers()

        self.subroutines = {}
        self.class_info = []

        self.translated_statements = 0

        self.std_lib_init = JackStandardLibrary()
        self.std_lib = self.std_lib_init.standard_library_formatted
        self.std_lib_subroutines = self.std_lib_init.full_subroutine_names
        
    def translate(self):
        """
        Get class and subroutines info. Generate symbolic table for every subroutine. Start parsing every subroutine
        """
        self.not_class_subroutines_lib = self.global_subroutines
        self.not_class_subroutines_lib.update(self.std_lib)

        JackTranslatorLibraryCodeGenerator._strip_input_commands(self)
        JackTranslatorLibraryCodeGenerator._get_class_info(self)        
        JackTranslatorLibraryCodeGenerator._get_subroutines(self)

        for subroutine_name in self.subroutines.keys():
            symbolic_table = JackTranslatorLibraryCodeGenerator._generate_symbolic_table(self, subroutine_name)
            self.subroutines[subroutine_name].append(symbolic_table)
        
        for subroutine_name in self.subroutines.keys():
            subroutine_vm_code = JackTranslatorLibraryCodeGenerator._translate_subroutine(self, subroutine_name)
            self.subroutines[subroutine_name].append(subroutine_vm_code)

        vm_code = []

        for subroutine_declaration, subroutine_symbolic_table, subroutine_vm_code in self.subroutines.values():
            indented_vm_code = [vm_command + '\n' for vm_command in subroutine_vm_code]
            vm_code.extend(indented_vm_code)

        return vm_code

    def _translate_subroutine(self, subroutine_name):
        """
        Return the vm code for a subroutine
        """
        
        subroutine_declaration = self.subroutines[subroutine_name][0]
        subroutine_symbolic_table = self.subroutines[subroutine_name][1]
        class_name = self.class_info[0]

        subroutine_vm_code = []

        # Translate meta information
        subroutine_title = f"function {class_name}.{subroutine_name}"
        subroutine_kind = JackTranslatorLibraryParser._get_tag_value(self, subroutine_declaration[0])
        locals_count = [x for y in list(subroutine_symbolic_table.values()) for x in y].count("var")

        subroutine_declaration_title = subroutine_title + f" {locals_count}"
        subroutine_vm_code.append(subroutine_declaration_title)

        # Add translation bootstrap code (setting the "this" segment)
        if subroutine_kind == "method":
            subroutine_vm_code.extend(["push argument 0", "pop pointer 0"])
        
        elif subroutine_kind == "constructor":
            class_variables = [x for y in list(self.class_info[1].values()) for x in y].count("field")
            subroutine_vm_code.extend([f"push constant {class_variables}", "call Memory.alloc 1", "pop pointer 0"])

        subroutine_body = subroutine_declaration[subroutine_declaration.index("<statements>"):JackTranslatorLibraryCodeGenerator._get_all_occurrences(subroutine_declaration, "</statements>")[-1]] 
        statements_vm_code = JackTranslatorLibraryCodeGenerator._translate_statements(self, subroutine_body, subroutine_name)
        subroutine_vm_code.extend(statements_vm_code)

        return subroutine_vm_code


    def _translate_statements(self, statement_declarations, subroutine_name):
        """
        Return the vm code for every statement in a subroutine body
        """

        statements_vm_code = []

        statements = []
        current_statement = []
        stack = []

        for index, tag in enumerate(statement_declarations):
            
            if "Statement" in tag and " " not in tag:
                if "/" in tag:
                    stack.pop()
                else:
                    stack.append(1)
            
            current_statement.append(tag)

            if len(stack) == 0:
                statements.append(current_statement)
                current_statement = []

        # Translate the differentiated statements
        for statement_declaration in statements:
            self.translated_statements += 1
            statement_type = statement_declaration[0][1:-1]
            statement_vm_code = []

            if statement_type == "letStatement":
                # Get identifier notation
                identifier = JackTranslatorLibraryParser._get_tag_value(self, statement_declaration[2])
                identifier = JackTranslatorLibraryCodeGenerator._get_identifier(self, identifier, subroutine_name)

                # Get expression declaration
                expression_declaration = statement_declaration[statement_declaration.index("<symbol> = </symbol>") + 2:-3]
                
                # Translate the expression
                expression_vm_code = JackTranslatorLibraryCodeGenerator._translate_expression(self, expression_declaration, subroutine_name)

                # Check if we our identifier is an array
                array_indexing = JackTranslatorLibraryParser._get_tag_value(self, statement_declaration[3]) == "["

                # Construct statement code
                if array_indexing:
                    identifier_expression_declaration  = statement_declaration[5:statement_declaration.index("<symbol> = </symbol>") - 2]
                    identifier_vm_code = JackTranslatorLibraryCodeGenerator._translate_expression(self, identifier_expression_declaration, subroutine_name)

                    # Calculate identifier address
                    statement_vm_code.extend([f"push {identifier}"])
                    statement_vm_code.extend(identifier_vm_code)
                    statement_vm_code.append("add")

                    # Push expression value
                    statement_vm_code.extend(expression_vm_code)

                    # Pop the expression value into a temp register and the identifier address into pointer 0
                    statement_vm_code.extend(["pop temp 0", "pop pointer 1"])

                    # Pop the expression value into the desired address
                    statement_vm_code.extend(["push temp 0", "pop that 0"])

                else:
                    # Push expression value
                    statement_vm_code.extend(expression_vm_code)

                    # Pop into the desired segment
                    statement_vm_code.append(f"pop {identifier}")
                

            elif statement_type == "ifStatement":
                # Get condition evaluation
                cond_expression = statement_declaration[statement_declaration.index("<symbol> ( </symbol>") + 2:statement_declaration.index("<symbol> { </symbol>") - 2]
                cond_expression_vm_code = JackTranslatorLibraryCodeGenerator._translate_expression(self, cond_expression, subroutine_name)

                # Push condition evaluation and flip it
                statement_vm_code.extend(cond_expression_vm_code)
                statement_vm_code.append("not")


                # Differentiate into statements
                if_statement_body = statement_declaration[statement_declaration.index("<symbol> { </symbol>") + 2: -3]

                if_true_statements = []
                if_false_statements = []

                depth = 0
                differentiating_else_index = 0

                for inner_index, tag in enumerate(if_statement_body):
                    tag_value = JackTranslatorLibraryParser._get_tag_value(self, tag)

                    if " " not in tag and "Statement" in tag: # Opening/closing tag
                        if "/" in tag:
                            depth -= 1
                        else:
                            depth += 1

                    if tag_value == "else" and depth == 0:
                        differentiating_else_index = inner_index
                        break

                # Branch on different types
                if differentiating_else_index != 0: # In case we have an else
                    if_true_statements = if_statement_body[:differentiating_else_index - 2]

                    # Generate unique labels
                    end_label = f"{subroutine_name}:{statement_type}:{self.translated_statements}:END"
                    second_statement_label = f"{subroutine_name}:{statement_type}:{self.translated_statements}:EXECUTE_SECOND_STATEMENT"

                    # Translate if true statements
                    if_true_statements_vm_code = JackTranslatorLibraryCodeGenerator._translate_statements(self, if_true_statements, subroutine_name)

                    # Add condition
                    statement_vm_code.append(f"if-goto {second_statement_label}")

                    # Translate if false statement
                    if_false_statements = if_statement_body[differentiating_else_index + 3:]
                    if_false_statements_vm_code = JackTranslatorLibraryCodeGenerator._translate_statements(self, if_false_statements, subroutine_name)
    
                    statement_vm_code.extend(if_true_statements_vm_code)
    
                    # Jump to end label
                    statement_vm_code.append(f"goto {end_label}")
    
                    # Declare false statement label and add it's vm code
                    statement_vm_code.append(f"label {second_statement_label}")
                    statement_vm_code.extend(if_false_statements_vm_code)
    
                    # Declare end label
                    statement_vm_code.append(f"label {end_label}")

                else:
                    # Generate unique end label
                    end_label = f"{subroutine_name}:{statement_type}:{self.translated_statements}:END"

                    # Translate body
                    if_statement_body_vm_code = JackTranslatorLibraryCodeGenerator._translate_statements(self, if_statement_body, subroutine_name)

                    # Add if goto end
                    statement_vm_code.append(f"if-goto {end_label}")

                    # Add translated if body
                    statement_vm_code.extend(if_statement_body_vm_code)

                    # Declare ending label
                    statement_vm_code.append(f"label {end_label}")


            elif statement_type == "whileStatement":
                # Generate unique labels
                start_label = f"{subroutine_name}:{statement_type}:{self.translated_statements}:START"
                end_label = f"{subroutine_name}:{statement_type}:{self.translated_statements}:END"

                # Get translated condition evaluation
                cond_expression = statement_declaration[statement_declaration.index("<symbol> ( </symbol>") + 2:statement_declaration.index("<symbol> { </symbol>") - 2]
                cond_expression_vm_code = JackTranslatorLibraryCodeGenerator._translate_expression(self, cond_expression, subroutine_name)

                # Get translated statement body
                statement_body = statement_declaration[statement_declaration.index("<symbol> { </symbol>") + 2:-3]
                statement_body_vm_code = JackTranslatorLibraryCodeGenerator._translate_statements(self, statement_body, subroutine_name)

                # Declare starting lbel
                statement_vm_code.append(f"label {start_label}")

                # Add flipped condition evaluation
                statement_vm_code.extend(cond_expression_vm_code)
                statement_vm_code.append("not")

                # Add jump to end
                statement_vm_code.append(f"if-goto {end_label}")

                # Add statement body
                statement_vm_code.extend(statement_body_vm_code)

                # Add recursive jump
                statement_vm_code.append(f"goto {start_label}")

                # Declare ending label
                statement_vm_code.append(f"label {end_label}")

            elif statement_type == "doStatement":
                # We can use one small trick here - this statement can be just a term
                statement_body = statement_declaration[2:-2]
                statement_vm_code = JackTranslatorLibraryCodeGenerator._translate_term(self, statement_body, subroutine_name, statement='do')
                callee_return_type = statement_vm_code.pop()
      
                if callee_return_type == "void": # Discard the returned value from a void subroutine
                    statement_vm_code.append("pop temp 0")

            elif statement_type == "ReturnStatement":
                # Get return type
                return_type = JackTranslatorLibraryParser._get_tag_value(self, self.subroutines[subroutine_name][0][1])
                
                # Branch on function type
                if return_type == "void":
                    statement_vm_code.append("push constant 0")
                else:
                    # Get translated return value and add it
                    expression = statement_declaration[3:-3]

                    if expression:
                        expression_vm_code = JackTranslatorLibraryCodeGenerator._translate_expression(self, expression, subroutine_name)
                        statement_vm_code.extend(expression_vm_code)

                # Add return
                statement_vm_code.append("return")

            else:
                self.translated_statements -= 1
                continue

            statements_vm_code.extend(statement_vm_code)

        return statements_vm_code

    def _translate_expression(self, expression_declaration, subroutine_name):
        """
        Translate a sequence of terms to VM code.
        /* KEEP IN MIND: Operator priority is not defined by the language, except that expressions in parentheses are evaluated first.
        Thus an expression like 2+3*4 may yield either 20 or 14, whereas 2+(3*4) is guaranteed to yield 14.*/
        """
        expression_vm_code = []

        # Terms and operations will keep differentiated structures
        terms = []
        operations = []

        # Differentiate into terms and operations
        current_term = []
        stack = []

        for index, tag in enumerate(expression_declaration):
            
            if "term" in tag and " " not in tag:
                if "/" in tag:
                    stack.pop()
                else:
                    stack.append(1)
            
            if len(stack) > 0:
                current_term.append(tag)
            else:
                tag_value = JackTranslatorLibraryParser._get_tag_value(self, tag)
                if tag_value in JackTranslatorLibrary.SYNTAX_ELEMENTS["op"]:
                    operations.append(tag_value)
                else:
                    terms.append(current_term[1:])
                    current_term = []

        # Translate each term
        terms_vm = []

        for term in terms:
            terms_vm.append(JackTranslatorLibraryCodeGenerator._translate_term(self, term, subroutine_name))

        # Construct expression VM code

        expression_vm_code.extend(terms_vm[0])



        if len(terms_vm) > 1:
            expression_vm_code.extend(terms_vm[1])

            for index, operation in enumerate(operations):
                operation_vm = JackTranslatorLibraryCodeGenerator.OPERATIONS[operation]

                expression_vm_code.append(operation_vm)

                try:
                    expression_vm_code.extend(terms_vm[index + 2])
                except:
                    break

        return expression_vm_code


    def _translate_term(self, term_declaration, subroutine_name, statement=""):
        """
        Translate a term to VM code
        """
        term_vm_code = []

        if len(term_declaration) == 1: # Single identifier/constant
            term_type = term_declaration[0].split()[0][1:-1]
            term_value = JackTranslatorLibraryParser._get_tag_value(self, term_declaration[0])

            if term_type == "identifier":
                term_vm_code.append(f"push {JackTranslatorLibraryCodeGenerator._get_identifier(self, term_value, subroutine_name)}")

            elif term_type == "keyword":
                if term_value in ["null", "false"]:
                    term_vm_code.append("push constant 0")
                elif term_value == "true":
                    term_vm_code.extend(["push constant 1", "neg"])
                else:
                    term_vm_code.append("push pointer 0")

            elif term_type == "integerConstant":
                term_vm_code.append(f"push constant {term_value}")

            elif term_type == "stringConstant":
                # WARNING: Not fully tested
                string_length = len(term_value)

                # Construct a new string object
                term_vm_code.extend([f"push constant {string_length}", "call String.new 1"])

                # For every char, append it to the string
                for char in term_value:
                    term_vm_code.extend([f"push constant {ord(char)}", "call String.appendChar 2"])

        else:
            term_value = JackTranslatorLibraryParser._get_tag_value(self, term_declaration[0])
            next_token = JackTranslatorLibraryParser._get_tag_value(self, term_declaration[1])

            if  next_token in [".", "("]: # Subroutine call
                expression_list = term_declaration[term_declaration.index("<symbol> ( </symbol>") + 2: -2]
                expression_list_vm_code = JackTranslatorLibraryCodeGenerator._translate_expression_list(self, expression_list, subroutine_name)

                callee_class_name = term_value if next_token == '.' else ""
                callee_subroutine_name = JackTranslatorLibraryParser._get_tag_value(self, term_declaration[2]) if next_token == '.' else term_value
                callee = callee_class_name + '.' + callee_subroutine_name
                
                args_count = 0
                subroutine_return_type = "NONE" # Start with some default value and eventually change it
            
                if not callee_class_name: # Method in current class
                    term_vm_code.append('push pointer 0')
                    callee_class_name = self.class_info[0]

                    subroutine_return_type = JackTranslatorLibraryParser._get_tag_value(self, self.subroutines[callee_subroutine_name][0][1])
                    args_count += 1

                elif callee_class_name == self.class_info[0]: # Function/constructor in current class
                    subroutine_return_type = JackTranslatorLibraryParser._get_tag_value(self, self.subroutines[callee_subroutine_name][0][1])

                else: # Accessing outside current_class
                    if callee_class_name in self.subroutines[subroutine_name][1].keys() or callee_class_name in self.class_info[1].keys(): # Method accessing outside current class 
                        var_name = callee_class_name
                        method = callee_subroutine_name
                        var_properties = JackTranslatorLibraryCodeGenerator._get_identifier(self, var_name, subroutine_name, info=True)
               
                        callee_class_name = var_properties[0]
                        term_vm_code.extend([f"push {'local' if var_properties[1] == 'var' else ('this' if var_properties[1] == 'field' else var_properties[1])} {var_properties[2]}"])
                    
                        if callee_class_name in self.std_lib.keys():
                            subroutine_return_type = self.std_lib[callee_class_name][method][1]
                        elif callee_class_name in self.subroutines.keys():
                            subroutine_return_type = JackTranslatorLibraryParser._get_tag_value(self, self.subroutines[callee_subroutine_name][0][1])
                        else:
                            outside_class = self.global_subroutines[callee_class_name]
                            outside_subroutine_properties = outside_class[method]

                            subroutine_return_type = outside_subroutine_properties[1]

                        args_count += 1

                    else: # Function/constructor accessing outside current class
                        if callee_class_name in self.std_lib.keys(): # Function/constructor in stdlib
                            subroutine_return_type = self.std_lib[callee_class_name][callee_subroutine_name][1]
                        else: # Function/constructor in global scope
                            subroutine_return_type = self.global_subroutines[callee_class_name][callee_subroutine_name][1]
               
                for vm_command in expression_list_vm_code:
                    term_vm_code.extend(vm_command)

                args_count += len(expression_list_vm_code)
                
                term_vm_code.append(f"call {callee_class_name}.{callee_subroutine_name} {args_count}")
                
                if statement == 'do':
                    term_vm_code.append(subroutine_return_type)

            elif next_token == "[": # varName indexing
                array_indexing_expression = term_declaration[term_declaration.index("<symbol> [ </symbol>") + 2: -2]
                array_indexing_expression_vm_code = JackTranslatorLibraryCodeGenerator._translate_expression(self, array_indexing_expression, subroutine_name)

                identifier = JackTranslatorLibraryCodeGenerator._get_identifier(self, term_value, subroutine_name)

                term_vm_code.extend([f"push {identifier}"])
                term_vm_code.extend(array_indexing_expression_vm_code)
                term_vm_code.append("add")

                term_vm_code.append("pop pointer 1")

                term_vm_code.append("push that 0")

            elif term_value in JackTranslatorLibrary.SYNTAX_ELEMENTS["op"]: # unaryOp term
                term_expression = term_declaration[1:]
                
                term_expression_vm_code = JackTranslatorLibraryCodeGenerator._translate_expression(self, term_expression, subroutine_name)

                term_vm_code.extend(term_expression_vm_code)

                command_expression = "neg" if term_value == "-" else "not"

                term_vm_code.append(command_expression)

            elif term_value == "(": # Bracket expression
                term_expression = term_declaration[2:-2]
                term_expression_vm_code = JackTranslatorLibraryCodeGenerator._translate_expression(self, term_expression, subroutine_name)

                term_vm_code.extend(term_expression_vm_code)

        return term_vm_code

    def _translate_expression_list(self, expression_list_declaration, subroutine_name):
        """
        Translate a sequence of expressions to VM code.
        /* WARNNING: Method not tested*/
        """

        expression_list_vm_code = []

        # expressions will contain every separate expression
        expressions = []

        # Differentiate into expressions and operations
        current_expression = []
        stack = []

        for index, tag in enumerate(expression_list_declaration):
            
            if "expression" in tag and " " not in tag:
                if "/" in tag:
                    stack.pop()
                else:
                    stack.append(1)
            
            if len(stack) > 0:
                current_expression.append(tag)
            else:
                tag_value = JackTranslatorLibraryParser._get_tag_value(self, tag)
                expressions.append(current_expression[1:])
                current_expression = []

        # Extend the expression list VM code with which individual expression VM code

        for expression in expressions:
            if expression:
                expression_list_vm_code.append(JackTranslatorLibraryCodeGenerator._translate_expression(self, expression, subroutine_name))

        return expression_list_vm_code

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~ Auxiliary translation ~~~~~~~~~~~~~~~~~~~~~~~
    def _get_identifier(self, identifier, subroutine_name, info=False):
        """
        Return the correct identifier properties, handle scoping. If info, return the identifier variable - properties
        """
        
        try: # Search for the identifier declaration in current scope
            identifier = self.subroutines[subroutine_name][1][identifier]
            
        except KeyError: # Search in class scope
            identifier = self.class_info[1][identifier]
        
        if info:
            return identifier

        identifier_type, identifier_kind, identifier_count = identifier[0], identifier[1], identifier[2]
        identifier_segment = identifier_kind
        
        if identifier_kind == "var":
            identifier_segment = "local"
        elif identifier_kind == "field":
            identifier_segment = "this"

        identifier_vm = f"{identifier_segment} {identifier_count}"
        
        return identifier_vm

    def _get_subroutines(self):
        """
        Find all name and declaration for subroutines and add them to self.subroutines
        """

        subroutine_declarations = JackTranslatorLibraryCodeGenerator._get_tag_body(self, "<subroutineDec>")

        for subroutine_declaration in subroutine_declarations:
            subroutine_name = JackTranslatorLibraryParser._get_tag_value(self, subroutine_declaration[2])

            self.subroutines[subroutine_name] = [subroutine_declaration]


    def _get_class_info(self):
        """
        Get class name and generate class symbolic table, which are going to be used in translation later
        """

        class_name = JackTranslatorLibraryParser._get_tag_value(self, self.input_commands[2])
        
        class_symbolic_table = {}

        variable_declarations = JackTranslatorLibraryCodeGenerator._get_tag_body(self, "<classVarDec>")

        count = 0
        last_kind = ""

        for variable_declaration in variable_declarations:
            variable_declaration = [JackTranslatorLibraryParser._get_tag_value(self, tag) for tag in variable_declaration]

            variable_kind = variable_declaration[0]

            if variable_kind != last_kind:
                count = 0

            variable_type = variable_declaration[1]

            variable_names = [name for name in variable_declaration[2:] if name != ',']

            for variable_name in variable_names:
                class_symbolic_table[variable_name] = [variable_type, variable_kind, count]
                count += 1

            last_kind = variable_kind
            

        self.class_info = [class_name, class_symbolic_table]


    def _get_tag_body(self, tag, gap=1, field_to_search="input_commands"):
        """
        /* WARNING: Do not use this when there are possible nested structures, e.g. expression parsing */
        Return all the statements (tags) between an opening and closing tag (the argument) in a given field (the default being self.input_commands), for every tag combination.
        Gap is used for the cleaning of e.g. statement ending semicolons
        """

        if field_to_search == "input_commands":
            field_to_search = self.input_commands

        starting_indices = JackTranslatorLibraryCodeGenerator._get_all_occurrences(field_to_search, tag)
        ending_indices = JackTranslatorLibraryCodeGenerator._get_all_occurrences(field_to_search, JackTranslatorLibraryParser._get_closed_tag(self, tag))

        declarations = []

        for starting_index, ending_index in zip(starting_indices, ending_indices):
            declaration = field_to_search[starting_index + 1: ending_index - gap] 
            declarations.append(declaration)

        return declarations


    def _generate_symbolic_table(self, subroutine_name):
        """
        Build up symbolic table for subroutine delcarations to handle identifiers type and scope problems
        """

        subroutine_declaration = self.subroutines[subroutine_name][0]
        symbolic_table = dict()

        # Parse arguments variables
        parameter_list = JackTranslatorLibraryCodeGenerator._get_tag_body(self, "<parameterList>", gap=0, field_to_search=subroutine_declaration)

        subroutine_type = JackTranslatorLibraryParser._get_tag_value(self, subroutine_declaration[0])

        if subroutine_type == "method":
            subroutine_kind = JackTranslatorLibraryParser._get_tag_value(self, subroutine_declaration[1])
            symbolic_table["this"] = [self.class_info[0], "argument", 0]

        if parameter_list:
            parameter_list = parameter_list[0] # There is only one parameterList tags pair

            parameter_variables = list(filter(lambda symbol: symbol != "<symbol> , </symbol>", parameter_list))

            parameter_variables = [[parameter_variables[index], parameter_variables[index + 1]] for index in range(0, len(parameter_variables), 2)]
            # /\ Transforms [type, identifier, ',', type, identifier...] into [[type, identifier], [type, identifier]...] /\

            for count, var_pair in enumerate(parameter_variables):
                if subroutine_type == "method":
                    count += 1

                var_type, var_name = var_pair[0], var_pair[1]
                symbolic_table[JackTranslatorLibraryParser._get_tag_value(self, var_name)] = [JackTranslatorLibraryParser._get_tag_value(self, var_type), "argument", count]


        # Subroutine body variables
        variable_declarations = JackTranslatorLibraryCodeGenerator._get_tag_body(self, "<varDec>", field_to_search=subroutine_declaration)

        count = 0

        for variable_declaration in variable_declarations:
            variable_declaration = [JackTranslatorLibraryParser._get_tag_value(self, tag) for tag in variable_declaration]

            variable_type = variable_declaration[1]
            variable_kind = variable_declaration[0]

            variable_names = [name for name in variable_declaration[2:] if name != ',']

            for variable_name in variable_names:
                symbolic_table[variable_name] = [variable_type, variable_kind, count]
                count += 1

        return symbolic_table

    def _strip_input_commands(self):
        """
        Remove every \n for easier work
        """

        for index, line in enumerate(self.input_commands):
            self.input_commands[index] = line.rstrip()

    def _get_all_occurrences(elements_list, element):
        """
        Return all occurrences of a given element in elements_list
        """
        
        index_list = []
        index_position = 0

        while True:
            try:
                index_position = elements_list.index(element, index_position)
                index_list.append(index_position)
                index_position += 1
            except ValueError as e:
                break

        return index_list

    def _get_global_subroutine_identifiers(self):
        """
        Construct global scope subroutine identifiers
        """

        identifiers = []
        
        if str(type(self.global_subroutines)) == "<class 'dict'>":
            for class_name, subroutine_declarations in self.global_subroutines.items():
                for subroutine_name in subroutine_declarations.keys():
                    identifiers.append(f"{class_name}.{subroutine_name}")

        return identifiers

class JackTranslatorLibraryParser:
    """
    Parse a cleaned, tokenized and classified file (Jack) and return the corresponding XML code

    More information on the parsing logic:
    // We start with the initializing of the class - make an instance, containing tokens (classified Jack keywords) and a row_pointer (used to
    // indicate the current working index).Then we are parsing a file - call a parsing function (in this case _parse_class()) and then write the
    // modified tokens to the file. The work of the _parse_class() function on the other side is pretty interesting - we start calling another
    // inner functions, which call another inner functions. The whole proccess of parsing a file is sequential
    // with recursive elements (e.g. expression parsing).
    """

    def __init__(self, input_file_name):
        self.input_file_name = input_file_name
        self.input_file = open(input_file_name, 'r')
        self.tokens = self.input_file.readlines()

        self.row_pointer = 0

    def parse(self):
        """
        Parse a single file
        """

        JackTranslatorLibraryParser._parse_class(self)

        with open(self.input_file_name, 'w') as input_file:
            input_file.seek(0)

            for line in self.tokens:
                input_file.write(line)

            input_file.truncate()

    # ~~~~~~~~~~~~~ File parsing nodes ~~~~~~~~~~~~~~~~~~~~~~~~~

    def _parse_class(self):
        """
        Parse a class (actually file parsing, but we know that there is only a single class in a file)
        """

        tag = "<class>\n"

        self.tokens.insert(self.row_pointer, tag)
        self.tokens.insert(len(self.tokens), JackTranslatorLibraryParser._get_closed_tag(self, tag))

        self.row_pointer += 4

        JackTranslatorLibraryParser._parse_variableDeclarations(self, class_vars=True)
        JackTranslatorLibraryParser._parse_subroutineDeclarations(self)


    def _parse_variableDeclarations(self, class_vars=False):
        """
        Node of _parse_class
        """

        tag = "<classVarDec>\n" if class_vars else "<varDec>\n"
        body = self.tokens[self.row_pointer:]

        for token in body:
            token_value = JackTranslatorLibraryParser._get_tag_value(self, token)

            if token_value == "var" or token_value == "static" or token_value == "field":
                self.tokens.insert(self.row_pointer, tag)
                self.row_pointer += 1

            if token_value == ";":
                self.tokens.insert(self.row_pointer + 1, JackTranslatorLibraryParser._get_closed_tag(self, tag))
                self.row_pointer += 1

            self.row_pointer += 1

            if class_vars:
                if token_value in JackTranslatorLibrary.SYNTAX_ELEMENTS["subroutines"]:
                    self.row_pointer -= 1
                    break
            else:
                if token_value in JackTranslatorLibrary.SYNTAX_ELEMENTS["statements"]:
                    self.row_pointer -= 1
                    break


    def _parse_subroutineDeclarations(self):
        """
        Node of _parse_class
        """

        current_token = self.tokens[self.row_pointer]

        while current_token != "</class>\n" and current_token != "<symbol> } </symbol>\n":
            JackTranslatorLibraryParser._parse_subroutineDeclaration(self)
            current_token = self.tokens[self.row_pointer]


    def _parse_subroutineDeclaration(self):
        """
        Node of _parse_subroutineDeclarations
        """

        dec_tag = "<subroutineDec>\n"
        param_list_tag = "<parameterList>\n"

        self.tokens.insert(self.row_pointer, dec_tag)
        self.row_pointer += 1

        subroutine_tokens = self.tokens[self.row_pointer:]

        for index, token in enumerate(subroutine_tokens):
            token_value = JackTranslatorLibraryParser._get_tag_value(self, token)

            if token_value == "(":
                if JackTranslatorLibraryParser._get_tag_value(self, subroutine_tokens[index + 1]) == ")":
                    self.row_pointer += 3
                    break
                else:
                    self.row_pointer += 1
                    self.tokens.insert(self.row_pointer, param_list_tag)
            elif token_value == ")":
                self.tokens.insert(self.row_pointer,
                                   JackTranslatorLibraryParser._get_closed_tag(self, param_list_tag))
                self.row_pointer += 3
                break

            self.row_pointer += 1

        JackTranslatorLibraryParser._parse_subroutineBody(self)

        self.tokens.insert(self.row_pointer, JackTranslatorLibraryParser._get_closed_tag(self, dec_tag))
        self.row_pointer += 1


    def _parse_subroutineBody(self):
        """
        Node of _parse_subroutineDeclaration
        """

        tag = "<subroutineBody>\n"

        self.tokens.insert(self.row_pointer, tag)

        self.row_pointer += 1

        JackTranslatorLibraryParser._parse_variableDeclarations(self)

        JackTranslatorLibraryParser._parse_statements(self)

        self.tokens.insert(self.row_pointer, JackTranslatorLibraryParser._get_closed_tag(self, tag))
        self.row_pointer += 1


    def _parse_statements(self, stop_value = "</subroutineDec>\n"):
        """
        Node of _parse_subroutineBody
        """

        tag = "<statements>\n"

        self.tokens.insert(self.row_pointer, tag)
        self.row_pointer += 1
        
       
        current_token = JackTranslatorLibraryParser._get_tag_value(self, self.tokens[self.row_pointer])
        current_token_full = self.tokens[self.row_pointer]

        while current_token_full != stop_value:
            statement_type = current_token + "Statement" if current_token != "return" else "ReturnStatement"
            statement_tag = f"<{statement_type}>\n"

            self.tokens.insert(self.row_pointer, statement_tag)
            self.row_pointer += 1

            if current_token == "let":
                JackTranslatorLibraryParser._parse_let(self)

            elif current_token == "do":
                JackTranslatorLibraryParser._parse_do(self)

            elif current_token == "if":
                JackTranslatorLibraryParser._parse_if(self)

            elif current_token == "while":
                JackTranslatorLibraryParser._parse_while(self)

            elif current_token == "return":
                JackTranslatorLibraryParser._parse_return(self)

                current_token = JackTranslatorLibraryParser._get_tag_value(self, self.tokens[self.row_pointer])
                next_token = JackTranslatorLibraryParser._get_tag_value(self, self.tokens[self.row_pointer + 1])
                self.tokens.insert(self.row_pointer, JackTranslatorLibraryParser._get_closed_tag(self, statement_tag))

                # Find out if this is an ending subroutine declaration return
                if next_token in ["function", "method", "constructor", "</class>\n"]: # Ending statement
                    self.row_pointer += 2
                else:
                    self.row_pointer += 1
                
                # It is meaningless to have statements after the current return, so we just skip them
                # WARNING: The program might break if you try to parse statements in the current statements block after a return
                break

            self.tokens.insert(self.row_pointer, JackTranslatorLibraryParser._get_closed_tag(self, statement_tag))
            self.row_pointer += 1

            current_token = JackTranslatorLibraryParser._get_tag_value(self, self.tokens[self.row_pointer])
            current_token_full = self.tokens[self.row_pointer]

            if current_token == "}": # In case we don't have a return
                next_token = JackTranslatorLibraryParser._get_tag_value(self, self.tokens[self.row_pointer + 1])

                if next_token in ["function", "method", "constructor", "</class>\n"]: # Ending subroutine declaration statement
                    self.row_pointer += 1

                break

        self.tokens.insert(self.row_pointer, JackTranslatorLibraryParser._get_closed_tag(self, tag))
        self.row_pointer += 1

    # ~~~~~~~~~~~~~~ General statement parsing ~~~~~~~~~~~~~~~~~

    def _parse_let(self):
        """
        Node of _parse_statements
        """

        self.row_pointer += 2

        current_token = JackTranslatorLibraryParser._get_tag_value(self, self.tokens[self.row_pointer])

        if current_token == "=":
            if JackTranslatorLibraryParser._get_tag_value(self, self.tokens[self.row_pointer + 1]) == "new":
                self.row_pointer += 1

            self.row_pointer += 1
            JackTranslatorLibraryParser._parse_expression(self)
            self.row_pointer += 1

        else:
            self.row_pointer += 1
            JackTranslatorLibraryParser._parse_expression(self)
            self.row_pointer += 2

            JackTranslatorLibraryParser._parse_expression(self)
            self.row_pointer += 1


    def _parse_do(self):
        """
        Node of _parse_statements
        """

        self.row_pointer += 1

        next_token = JackTranslatorLibraryParser._get_tag_value(self, self.tokens[self.row_pointer + 1])

        if next_token == ".":  # Method call
            self.row_pointer += 4
        else:  # Function call
            self.row_pointer += 2

        JackTranslatorLibraryParser._parse_expression_list(self)

        self.row_pointer += 2


    def _parse_if(self):
        """
        Node of _parse_statements
        """

        self.row_pointer += 2

        JackTranslatorLibraryParser._parse_expression(self)

        self.row_pointer += 2

        JackTranslatorLibraryParser._parse_statements(self, stop_value="<symbol> } </symbol>\n")

        self.row_pointer += 1

        current_token = JackTranslatorLibraryParser._get_tag_value(self, self.tokens[self.row_pointer])

        if current_token == "else":
            self.row_pointer += 2

            JackTranslatorLibraryParser._parse_statements(self, stop_value="<symbol> } </symbol>\n")

            self.row_pointer += 1


    def _parse_while(self):
        """
        Node of _parse_statements
        """

        self.row_pointer += 2

        JackTranslatorLibraryParser._parse_expression(self)

        self.row_pointer += 2

        JackTranslatorLibraryParser._parse_statements(self, stop_value="<symbol> } </symbol>\n")

        self.row_pointer += 1


    def _parse_return(self):
        """
        Node of _parse_statements
        """

        self.row_pointer += 1

        current_token = JackTranslatorLibraryParser._get_tag_value(self, self.tokens[self.row_pointer])

        if current_token == ";":
            self.row_pointer += 1
            return

        JackTranslatorLibraryParser._parse_expression(self)
        self.row_pointer += 1
        
    # ~~~~~~~~~~~~ Statement auxiliary parsing ~~~~~~~~~~~~~~~~~

    def _parse_expression(self):
        """
        Node of _parse_expressionList
        """

        tag = "<expression>\n"

        self.tokens.insert(self.row_pointer, tag)
        self.row_pointer += 1

        JackTranslatorLibraryParser._parse_term(self)

        current_token = JackTranslatorLibraryParser._get_tag_value(self, self.tokens[self.row_pointer])

        while current_token in JackTranslatorLibrary.SYNTAX_ELEMENTS["op"]:
            self.row_pointer += 1

            JackTranslatorLibraryParser._parse_term(self)
            current_token = JackTranslatorLibraryParser._get_tag_value(self, self.tokens[self.row_pointer])

        self.tokens.insert(self.row_pointer, JackTranslatorLibraryParser._get_closed_tag(self, tag))
        self.row_pointer += 1


    def _parse_expression_list(self):
        """
        Node of _parse_let;do;if;while;return
        """
        current_token = JackTranslatorLibraryParser._get_tag_value(self, self.tokens[self.row_pointer])

        if current_token == ")":
            return

        tag = "<expressionList>\n"

        self.tokens.insert(self.row_pointer, tag)
        self.row_pointer += 1

        JackTranslatorLibraryParser._parse_expression(self)

        current_token = JackTranslatorLibraryParser._get_tag_value(self, self.tokens[self.row_pointer])

        while current_token == ",":
            self.row_pointer += 1

            JackTranslatorLibraryParser._parse_expression(self)
            current_token = JackTranslatorLibraryParser._get_tag_value(self, self.tokens[self.row_pointer])

        self.tokens.insert(self.row_pointer, JackTranslatorLibraryParser._get_closed_tag(self, tag))
        self.row_pointer += 1


    def _parse_term(self):
        """
        Node of _parse_expression
        """

        tag = "<term>\n"

        current_token = JackTranslatorLibraryParser._get_tag_value(self, self.tokens[self.row_pointer])
        current_token_type = self.tokens[self.row_pointer].split(" ")[0][1:-1]

        next_token = JackTranslatorLibraryParser._get_tag_value(self, self.tokens[self.row_pointer + 1])

        self.tokens.insert(self.row_pointer, tag)
        self.row_pointer += 1

        if next_token == '[': # Array accessing
            self.row_pointer += 2

            JackTranslatorLibraryParser._parse_expression(self)
            self.row_pointer += 1

        elif current_token == "(": # Expression in brackets
            self.row_pointer += 1

            JackTranslatorLibraryParser._parse_expression(self)
            self.row_pointer += 1

        elif current_token == "-" or current_token == "~":  # Unary op
            self.row_pointer += 1
            JackTranslatorLibraryParser._parse_term(self)

        elif next_token == "(" or next_token == ".":  # Subroutine call
            if next_token == ".":  # Method call
                self.row_pointer += 4
            else:  # Function call
                self.row_pointer += 2

            JackTranslatorLibraryParser._parse_expression_list(self)
            self.row_pointer += 1

        else: # Single variable
            self.row_pointer += 1

        self.tokens.insert(self.row_pointer, JackTranslatorLibraryParser._get_closed_tag(self, tag))
        self.row_pointer += 1

    # ~~~~~~~~~~~ Tag auxiliary ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _get_closed_tag(self, tag):
        """
        Appends '/' in the second place of the input
        """

        tag_list = list(tag)
        tag_list.insert(1, "/")
        return "".join(tag_list)


    def _get_tag_value(self, tag):
        """
        Returns mediocre keyword
        """
        try:
            splitted_tag = tag.split()

            tag_type = splitted_tag[0]

            if tag_type == "<stringConstant>":
                tag_part = tag[tag.index(">") + 3:]
                return tag_part[:tag_part.index("<") - 2]
            else:
                return splitted_tag[1]
        except:
            return tag
