#!/usr/bin/python
#hengfengzhang
#20210721

import os
import sys
import re
import argparse
import shutil

def get_parse():
  parser = argparse.ArgumentParser(description='''Check wire connection and width mismatch.''')
  parser.add_argument('-m', '--mode'   , metavar='check, stub, define' , nargs='+', default='check', help='check mode/stub mode'    )
  parser.add_argument('-v', '--verilog', metavar='design', nargs='+', default='./rsu_top.v', help='top design verilog'      )
  args = parser.parse_args()
  return args.verilog, args.mode

def get_name(verilog):
    re_name = re.compile('module\s*(\w+)(\s+\()')
    with open(verilog,'r') as top:
        for line in top.readlines():
            if re.search(re_name, line):
                return re.search(re_name, line).group(1)

def get_sigs(verilog):
    re_port = re.compile('(input|output|inout)(\[(\d+):0\])?(\w+)(,?)')
    re_wire = re.compile('\.\w+\((\w+)(\[(\d+):0\])?\),?(\/\/(input|output))?')
    with open(verilog,'r') as top:
        lines = top.readlines();
        obj_dir  = {}
        obj_wid  = {}
        obj_cnt  = {}
        obj_exp  = {}
        obj_lin  = {}
        for line in lines:
            line = re.sub(r'\s', '', line)
            line = re.sub(r'^\/\/.*$', '', line)
            line = re.sub(r'^(\w+.*)?\.\w+\(\d+\).*', '', line)
            if re.search(re_port, line):
                port_dir = re.search(re_port, line).group(1)
                port_rag = re.search(re_port, line).group(2)
                if port_rag:
                    port_wid = int(re.search(re_port, line).group(3)) + 1
                else:
                    port_wid = 1
                port_sig = re.search(re_port, line).group(4)
                if port_sig not in obj_dir:
                    obj_dir[port_sig] = port_dir
                    obj_wid[port_sig] = port_wid
                    obj_cnt[port_sig] = 1
                    obj_exp[port_sig] = port_dir
                    obj_lin[port_sig] = line
                else:
                    obj_cnt[port_sig] = 1 + obj_cnt[port_sig]
            elif re.search(re_wire, line):
                wire_dir = re.search(re_wire, line).group(5)
                wire_rag = re.search(re_wire, line).group(2)
                if wire_rag:
                    wire_wid = int(re.search(re_wire, line).group(3)) + 1
                else:
                    wire_wid = 1
                wire_sig = re.search(re_wire, line).group(1)
                if wire_sig not in obj_dir:
                    obj_dir[wire_sig] = wire_dir
                    obj_wid[wire_sig] = wire_wid
                    obj_cnt[wire_sig] = 1
                    obj_exp[wire_sig] = 'wire'
                    obj_lin[wire_sig] = line
                else:
                    obj_cnt[wire_sig] = 1 + obj_cnt[wire_sig]
                    if wire_wid != obj_wid[wire_sig]:
                        print('error: width mismath', obj_lin[wire_sig], wire_sig)
    return obj_dir, obj_wid, obj_cnt, obj_exp, obj_lin


def get_wire(obj_wid, obj_exp):
    wire_def = []
    for obj in sorted(obj_wid):
        if 'wire' in obj_exp[obj]:
            wire_def.append( 'wire'+' ['+str(obj_wid[obj]-1)+':0] '+obj+';//'+str(obj_cnt[obj]) )
    for line in wire_def:
        print(line)
    return wire_def

def get_port(obj_wid, obj_exp):
    port_def = []
    for obj in sorted(obj_wid):
        if 'wire' not in obj_exp[obj]:
            port_def.append( obj_exp[obj]+' ['+str(obj_wid[obj]-1)+':0] '+obj+',' )
    return port_def

def get_tie0(obj_wid, obj_exp):
    tie0_def = []
    for obj in sorted(obj_wid):
        if 'output' in obj_exp[obj]:
            if 'ready' in obj:
                tie0_def.append( 'assign '+obj+' = '+str(obj_wid[obj])+'\'h1;' )
            else:
                tie0_def.append( 'assign '+obj+' = '+str(obj_wid[obj])+'\'h0;' )
    return tie0_def

def get_float(obj_wid, obj_exp):
    for obj in sorted(obj_wid):
        if obj_cnt[obj] == 1:
            if 'proc' not in obj:
                print('error: not connected wire -> ', obj_lin[obj], obj_cnt[obj])
    return True

def get_broadcast(obj_wid, obj_exp):
    for obj in sorted(obj_wid):
        if obj_cnt[obj] > 2:
            print('info: multiple load wire -> ', obj_lin[obj], obj_cnt[obj])
    return True

def gen_stub(module, port, tie0):
    with open(module+'_stub.v','w') as top:
        top.write('module '+module+'(\n')
        for line in port[0:-1]:
            top.write('\t'+line+'\n')
        top.write('\t'+port[-1].replace(r',','')+'\n')
        top.write(');\n')
        for line in tie0:
            top.write('\t'+line+'\n')
        top.write('endmodule')

if __name__ == '__main__':
    obj_dir  = {}
    obj_wid  = {}
    obj_cnt  = {}
    obj_exp  = {}
    obj_lin  = {}
    verilog, mode = get_parse()
    obj_dir, obj_wid, obj_cnt, obj_exp, obj_lin = get_sigs(verilog[0])
    if 'define' in mode:
        get_wire(obj_wid, obj_exp)
    if 'check' in mode:
        get_float(obj_wid, obj_exp)
        get_broadcast(obj_wid, obj_exp)
    if 'stub' in mode:
        module = get_name(verilog[0])
        port   = get_port(obj_wid, obj_exp)
        tie0   = get_tie0(obj_wid, obj_exp)
        gen_stub(module, port, tie0)
