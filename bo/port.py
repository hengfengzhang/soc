class Port:
    name = ""
    width = ""
    type = ""

    def __init__(self, port_content):
        self.name = port_content[5]
        self.width = port_content[4] if len(port_content[4]) > 0 else "\t"
        self.type = port_content[0]


class PortInfo:
    port = None
    insts = {}

    def __init__(self, port):
        self.port = port
        self.insts = {"input": [], "output": [], "inout": []}

    def add(self, port, module_name):
        self.insts[port.type].append("'" + module_name + "'")

    def getComment(self):
        comment = "//"
        comment += "to: " + ", ".join(self.insts["input"]) + ";" if self.insts["input"] else ""
        comment += "from: " + ", ".join(self.insts["output"]) + ";" if self.insts["output"] else ""
        comment += "connect: " + ", ".join(self.insts["inout"]) + ";" if self.insts["inout"] else ""
        return comment

    def isValid(self):
        if len(self.insts["output"]) > 1:
            print('Error: ' + self.port.name + " " + str(len(self.insts["output"])) + ' have been multiple derived by ' + str(self.insts["output"]))
            return False
        if len(self.insts["input"]) > 1:
            print('Info: ' + self.port.name + " " + str(len(self.insts["input"])) + ' have been broadcast to ' + str(self.insts["input"]))
        return True

    def isWire(self):
        if len(self.insts["inout"]) == 0:
            if len(self.insts["input"]) > 0 and len(self.insts["output"]) > 0:
                return True
        return False

    def getInfo(self):
        if self.isWire():
            return "wire\t" + self.port.width + "\t" + self.port.name + ";"
        else:
            return "\t" + self.port.type + "\t" + self.port.width + "\t" + self.port.name + ","


class PortInfos:
    port_infos = {}

    def __init__(self):
        self.port_infos = {}

    def add(self, module):
        for port in module.ports:
            if port.name not in self.port_infos:
                self.port_infos[port.name] = PortInfo(port)
            self.port_infos[port.name].add(port, module.name)
