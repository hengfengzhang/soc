#!/usr/bin/python
#hengfengzhang
#20210721

import os
import sys
import re
import argparse
import shutil

def get_parse():
  parser = argparse.ArgumentParser(description='''Generate stub file for top design with ready/rdy output tied high.
  ''')
  parser.add_argument('-i', '--design' , metavar='design.v'     , nargs='+', default='a.v',      help='input file'    )
  parser.add_argument('-o', '--wrapper', metavar='design_stub.v', nargs='+', default='a_stub.v', help='output file'   )
  args = parser.parse_args()
  print(str(args))
  return args.design, args.wrapper

def match_spaceline(string, port_active):
  if port_active:
    return re.search(r'^(\s?)+//', string)
  else:
    return False

def match_module_begin(string, port_active):
  if not port_active:
    return re.search(r'^\s?module\s+\w+\(?', string)
  else:
    return False

def match_module_end(string, port_active):
  if port_active:
    return re.search(r'\s?endmodule', string)
  else:
    return False

def match_port(string, port_active):
  port_type = ''     #input/output/inout
  port_is   = False
  if port_active:
    if re.search(r'output.*;', string):
      port_type = 'output'
      port_is   = True
    elif re.search(r'input.*;', string):
      port_type = 'input'
      port_is   = True
    elif re.search(r'inout.*;', string):
      port_type = 'inout'
      port_is   = True
    else:
      port_type = None
      port_is   = False
  else:
    port_type = None
    port_is   = False
  return port_is, port_type

def get_port_attri(string, port_type):
  string     = re.sub(r';', '', string)
  string     = re.sub(r'\]', '] ', string)
  string     = re.sub(r'\[', ' [', string)
  port_dict  = {}
  port_name  = ''
  port_width = ''
  port_attri = ''
  port_split = string.split()
  port_name = port_split[-1]
  for val in port_split:
    if '[' in val:
      port_width = val
    elif ('wire' in val) or ('reg' in val):
      port_attri = val
    elif port_type in val:
      port_type = val
  #default all output port assign to the w_${port_name}
  #default all inout  port assign to the p_${port_name}
  #default all input  port assign to the u_${port_name}
  if port_type == 'output':
    port_wire = 'w_' + port_name
  elif port_type == 'inout':
    port_wire = 'p_' + port_name
  else:
    port_wire = 'u_' + port_name
  port_dict[port_name] = [port_type, port_width, port_attri, port_wire, ['']]
  return port_dict

#scheme to connect port
def update_module_dict(module_dict):
  for module_name in module_dict:
    module_port = module_dict[module_name]
    for port in module_port.keys():
      port_attri     = module_port[port]
      port_type      = port_attri[0]
      same_name_port = {}
      if port_type == 'output':
        port_type = 'input'
      elif port_type == 'input':
        port_type = 'output'
      else:
        port_type = 'inout'
      same_name_port = find_same_port(module_dict, port, port_type, module_name)
      #print('search '+module_name + ' -> ' + port + '->' + str(same_name_port))
      if ( len(same_name_port) > 0 ) and (same_name_port[0] != ''):
        port_attri[3] = 'w_' + port
      else:
        port_attri[3] = 'p_' + port
      port_attri[4] = same_name_port
      module_port.update({port:port_attri})
      module_dict.update({module_name:module_port})
  return module_dict

def find_same_port(module_dict, port_name, port_type, module_name):
  same_name_port = []
  for t_module_name in module_dict:
    if module_name != t_module_name:
      t_module_port = module_dict[t_module_name]
      for t_port_name in t_module_port.keys(): #find the port
        if port_type == t_module_port[t_port_name][0] and port_name == t_port_name:
         same_name_port.append({t_module_name:port_name })
  return same_name_port

def find_module_port(cur_design, cur_dir):
  port_active = False
  module_port = {}
  design_path = cur_dir + '/' + cur_design
  with open(design_path, 'r') as design_obj:
    lines = design_obj.readlines()
    for line in lines:
      line = re.sub(r'\/\/.*$','', line)
      line = re.sub(r'\/\*.*$','', line)
      if not match_spaceline(line, port_active):
        if match_module_begin(line, port_active):
          module_name = line.replace(r'(', '').split()[-1]
          port_active = True
          print('INFO: module begin -> '+module_name+'\n')
        elif match_module_end(line, port_active):
          port_active = True
          print('INFO: module end   -> '+module_name+'\n')
        port_is, port_type = match_port(line, port_active)
        if port_is:
          module_port.update( get_port_attri(line, port_type) )
    return module_name, module_port

def get_module_dict(ori_list):
  module_name = '' #module_name
  module_port = {} #{port_name: port_attri[]}
  module_dict = {} #{module_name: module_dict}
  for ori_module in ori_list:
    module_name, module_port = find_module_port(ori_module, cur_dir)
    module_dict.update( {module_name : module_port} )
  return module_dict

def print_module_dict(module_dict):
  for module_name in module_dict:
    print( 'Find module -> ' + module_name )
    module_port = module_dict[module_name]
    for port in module_port:
      print( 'Find module port ->-> ' + port )
      port_attri = module_port[port]
      for attri in port_attri:
        print( 'Find module port attribute ->->-> ' + str(attri) )

def inst_port(module_dict, gen_design):
  inst = []
  #inst header
  inst_hdr = '\nmodule\t' + gen_design.replace('_stub','') + '\t(\t//beginport\t' + gen_design
  inst.append(inst_hdr)
  #inst port
  p_port = []
  for module_name in module_dict:
    module_port = module_dict[module_name]
    for port in module_port.keys():
      port_attri   = module_port[port]
      inst_port    = '\n\t' + port_attri[0] + '\t' + port_attri[1]  + '\t' + port + '\t'
      if inst_port not in p_port:
        p_port.append(inst_port)
  if len(p_port) > 0:
    for line in p_port[0:-1]:
      inst.append(line + ',')
    inst.append(p_port[-1])
  #inst tail
  inst_tail = '\n);\t\t\t//endport\t' + gen_design + '\n\n\n'
  inst.append(inst_tail)
  return inst

def inst_tie(module_dict):
  inst = []
  #inst wire
  for module_name in module_dict:
    module_port = module_dict[module_name]
    for port in module_port.keys():
      port_attri   = module_port[port]
      if port_attri[0] == 'output':
        if ('ready' in port) or ('rdy' in port) :
          inst_wire    = '\n\tassign\t'  + '\t' + port + '\t=\t\'h1;'
        else:
          inst_wire    = '\n\tassign\t'  + '\t' + port + '\t=\t\'h0;'
        if inst_wire not in inst:
          inst.append(inst_wire)
  return inst

def inst_tail(module_dict):
  inst = []
  inst_m = []
  #inst list
  for module_name in module_dict:
    inst_m.append(module_name)
  inst_tail = '\n\n\nendmodule\t//\tinst' + str(inst_m)
  inst.append(inst_tail)
  return inst

def inst_v(module_dict, gen_design):
  inst = []
  for line in ( inst_port( module_dict, gen_design.split('.')[0] )  ):
    inst.append(line)
  for line in ( inst_tie(module_dict)                               ):
    inst.append(line)
  for line in ( inst_tail(module_dict)                              ):
    inst.append(line)
  with open(gen_design, 'w+') as w_obj:
    for line in inst:
      w_obj.write(line)


if __name__ == '__main__':
  
  ori_list = []
  gen_list = []
  cur_dir  = os.getcwd()
  ori_list, gen_list = get_parse()
  gen_design = gen_list[0]
  gen_path   = cur_dir + '/' + str(gen_design)
  if os.path.exists(gen_path):
    os.remove(gen_path)
  if os.path.exists('filelist.f'):
    os.remove('filelist.f')

  with open('filelist.f','w+') as w_obj:
    w_obj.write(gen_design+'\n')

  module_dict = get_module_dict(ori_list)
  print_module_dict(module_dict)
  inst_v(module_dict, gen_design)
    
