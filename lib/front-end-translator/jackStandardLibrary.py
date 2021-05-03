# A library file containing Jack Standard Library function declarations and methods used to work with them. @DimitarYordanov17

import re

class JackStandardLibrary:
    """
    Main class to work with

    Standard library raw:
    Raw text and data from the book

    Standard library formatted:
    {class_name: {subroutine_name1: [subroutine_kind, subroutine_type, subroutine_parameter_list], subroutine_name2: [subroutine_kind, subroutine_type, subroutine_parameter_list]}}

    Full subroutine names:
    [class_name1.subroutine_name1, class_name1.subroutine_name2..., class_name2.subroutine_name1, class_name2.subroutine_name2...]
    """
    
    def __init__(self, file_name='jackStandardLibraryRaw.txt'):
        self.standard_library_raw = open(file_name, 'r').read()
        self.standard_library_formatted = JackStandardLibrary.construct_formatted_library(self.standard_library_raw)
        self.full_subroutine_names = JackStandardLibrary.construct_full_subroutine_names(self.standard_library_formatted)

    def construct_formatted_library(text):
        """
        Format the raw library text into class segments dictionaries
        """
        
        dictionary = {}
        
        classes_declarations = re.split(r'[a-zA-Z]+\n\n', text)
        classes_names = [class_name.split('\n')[0] for class_name in re.findall(r'[a-zA-Z]+\n\n', text)]

        for class_name, class_dec in zip(classes_names, classes_declarations[1:]):
            methods_and_functions_declarations = re.findall(r'((constructor|function|method).+:)', class_dec)
            cleaned_methods_functions = [pair[0][:-1] for pair in methods_and_functions_declarations]
            
            classified_methods_functions = {}
            
            for subroutine_dec in cleaned_methods_functions:
                subroutine_parts = subroutine_dec.split()
                subroutine_name = subroutine_parts[2]
                subroutine_kind = subroutine_parts[0]
                subroutine_type = subroutine_parts[1]
                parameter_list = subroutine_dec[subroutine_dec.index('('):]

                classified_methods_functions[subroutine_name] = [subroutine_kind, subroutine_type, parameter_list]

            dictionary[class_name] = classified_methods_functions

        return dictionary
    
    def construct_full_subroutine_names(formatted_dict):
        """
        Return the full subroutine name which is: {main_key}.{current_key}
        """

        full_subroutine_names = []

        for class_name, subroutines in formatted_dict.items():
            current_full_subroutine_names = []

            for subroutine_name in subroutines.keys():
                current_full_subroutine_names.append(f"{class_name}.{subroutine_name}")

            full_subroutine_names.extend(current_full_subroutine_names)

        return full_subroutine_names
