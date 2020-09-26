import re

from bo.port import Port


class Module:
    ports = []
    valid = False
    name = ""

    def isValid(self):
        return self.valid

    def __init__(self, file_path):
        self.ports = []
        self.valid = False
        with open(file_path, 'r') as file_obj:
            print('\nInfo: Read file, ' + file_path)
            content = file_obj.read()

            # delete verilog comment
            regex_note = re.compile(r'//.*')
            match_string = re.findall(regex_note, content)
            for k in range(len(match_string)):
                content = content.replace(match_string[k], '')

            # regex match module name
            regex_module = re.compile(r'(module)(\s+)(\w+)(\s+)')
            module_obj = re.findall(regex_module, content)
            if len(module_obj) == 0:
                print('Error: Cannot find any module')
                return
            if len(module_obj) > 1:
                print('Error: ', len(module_obj), ' module have been found')
                return
            if len(module_obj) == 1:
                self.name = module_obj[0][2]
                print('Info: Found module, ', self.name)

            # regex match ports name
            regex_ports = re.compile(r'(input|output|inout)(\s+)(reg|wire)?(\s+)?(\[.*:.*\]\s+)?(\w+)')
            groups_ports = re.findall(regex_ports, content)
            print('Info: Found ports, ', len(groups_ports))

            self.ports = [Port(port_content) for port_content in groups_ports]

            # regex match parameter define
            regex_para = re.compile(r'parameter')
            groups_para = re.findall(regex_para, content)
            if len(groups_para) > 0:
                print('Warn: Found parameters, ', len(groups_para))

            self.valid = True

    def getInfo(self):
        info = ""
        info += "\n//instance module of " + self.name
        info += "\n" + self.name + " u_" + self.name + " (\n"

        for port in self.ports:
            info += "\t." + port.name + "\t( " + port.name + ")," + "\t\t//" + port.type + " " + port.width + "\n"

        info += ");\n"
        return info
