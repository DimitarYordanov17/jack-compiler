# A jack translator (front-end). Jack code to Intermediate (VM) code. @DimitarYordanov17

# To run: python3 jackTranslator.py {path} {generate corresponding XML files, yes/no}

from jackTranslatorLibrary import JackTranslatorLibrary
import os
import sys


class JackTranslator:
    """
    Main class, capable of translating/parsing a full directory, with .jack files, resulting in corresponding .vm files and eventually .xml files
    """


    def translate(path, generate_xml=False):
        """
        Translate a directory/file, .jack -> .vm. A middle .xml file is used and if generate_xml=True, we keep it
        """
       
        jack_files = []
        global_scope_subroutines = {}

        if ".jack" in path: # Single file
            jack_files.append(path)

        else:
            for root, dirs, files in os.walk(path):
                for file_name in files:
                    if file_name.endswith(".jack"):
                      jack_files.append(file_name)
        
        # Construct global scope subroutines table and create xml files
        for jack_full_file_name in jack_files:
            jack_xml_file_name = jack_full_file_name.split(".")[0] + ".xml"

            JackTranslator._generate_xml(jack_full_file_name, tabularize=False)
             
            file_subroutines = JackTranslatorLibrary.get_file_subroutines(jack_xml_file_name)
            global_scope_subroutines.update(file_subroutines)

        # Translate each file
        for jack_full_file_name in jack_files:
            jack_file_name = jack_full_file_name.split(".")[0]

            output_file_name = jack_file_name + ".vm"
            jack_xml_file_name = jack_file_name + ".xml"
          
            vm_code = JackTranslatorLibrary.translate_file(jack_xml_file_name, global_scope_subroutines)

            JackTranslatorLibrary.tabularize(jack_xml_file_name)

            if not generate_xml:
                os.system(f"rm {jack_xml_file_name}")
 
            with open(output_file_name, 'w') as output_file:
                for line in vm_code:
                    output_file.write(line)

                output_file.truncate()

    def _generate_xml(input_file_name, tabularize=True):
        """
        Parses a single .jack file, resulting in a .xml file
        """

        output_file_name = input_file_name.split(".")[0] + ".xml"
        os.system(f"cp {input_file_name} {output_file_name}")
        JackTranslatorLibrary.clean(output_file_name)
        JackTranslatorLibrary.tokenize(output_file_name)

        JackTranslatorLibrary.parse_file(output_file_name)

        if tabularize:
            JackTranslatorLibrary.tabularize(output_file_name)


JackTranslator.translate(sys.argv[1], generate_xml = True if sys.argv[2] == "yes" else False)
