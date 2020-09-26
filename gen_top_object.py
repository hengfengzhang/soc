#!/usr/bin/python3
# Copyright Hengfeng.zhang
# soc top rtl integration
# the module ports in one more module will be connected
# the module ports only in one module will be exported
# the ports and signals will commented with its connection for review
# 20200925, initial this script

import re
import os
import sys

if __name__ == '__main__':

    print('-----Connector Generator Begin-------')
    # open the design file
    try:
        top = sys.argv[1]
        file_group = sys.argv[2:]
    except Exception:
        raise ("Error: gen_tb.py need some design.v ")

    # define the generated file
    inst = 'inst.tmp'
    directory = os.getcwd()
    inst_path = directory + '/' + inst
    top_path = directory + '/' + top

    # remove tmp
    if os.path.exists(inst_path):
        os.remove(inst_path)

    if os.path.exists(top_path):
        os.remove(top_path)

    with open(inst_path, 'a') as instance_group:
        port_list = []
        sig_dir = {}
        inst_list = []
        for file_design in file_group:
            file_path = directory + '/' + file_design

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
                if len(module_obj) > 1:
                    print('Error: ', len(module_obj), ' module have been found')
                if len(module_obj) == 1:
                    module_name = module_obj[0][2]
                    print('Info: Found module, ', module_name)

                # regex match ports name
                regex_ports = re.compile(r'(input|output|inout)(\s+)(reg|wire)?(\s+)?(\[.*:.*\]\s+)?(\w+)')
                groups_ports = re.findall(regex_ports, content)
                print('Info: Found ports, ', len(groups_ports))

                # write the instance and signal
                if module_obj is not None:
                    instance_group.write('\n//instance module of ' + module_name)
                    instance_group.write('\n' + module_name + ' u_' + module_name + ' (\n')

                    num = len(groups_ports)
                    for i in range(num):
                        port_name = groups_ports[i][5]
                        port_width = groups_ports[i][4]
                        port_type = groups_ports[i][0]
                        if port_name not in port_list:
                            sig_dir[port_name] = {}
                            sig_dir[port_name]['input_inst'] = []
                            sig_dir[port_name]['output_inst'] = []
                            sig_dir[port_name]['inout_inst'] = []
                            sig_dir[port_name]['input_num'] = 0
                            sig_dir[port_name]['output_num'] = 0
                            sig_dir[port_name]['inout_num'] = 0
                            sig_dir[port_name]['port_name'] = port_name
                            sig_dir[port_name]['port_width'] = port_width
                            sig_dir[port_name]['port_type'] = port_type
                            port_list.append(port_name)

                        if port_type == 'input':
                            sig_dir[port_name]['input_num'] = 1 + sig_dir[port_name]['input_num']
                            sig_dir[port_name]['input_inst'].append(module_name)
                        elif port_type == 'output':
                            sig_dir[port_name]['output_num'] = 1 + sig_dir[port_name]['output_num']
                            sig_dir[port_name]['output_inst'].append(module_name)
                        else:
                            sig_dir[port_name]['inout_num'] = 1 + sig_dir[port_name]['inout_num']
                            sig_dir[port_name]['inout_inst'].append(module_name)

                        if i == num - 1:
                            instance_group.write('\t.' + port_name + '\t(' + port_name + ')'
                                                 + '\t// ' + port_type + ' ' + port_width
                                                 + '\n);\n')
                        else:
                            instance_group.write('\t.' + port_name + '\t(' + port_name + '),'
                                                 + '\t //' + port_type + ' ' + port_width
                                                 + '\n')

                # regex match parameter define
                regex_para = re.compile(r'parameter')
                groups_para = re.findall(regex_para, content)
                if len(groups_para) > 0:
                    print('Warn: Found parameters, ', len(groups_para))

        # Write signals declartion
        with open(top_path, 'a') as top_group:
            top_group.write('/*------------------------------------------------------------------\n')
            top_group.write('//The design file is generated by gen_top.py\n')
            top_group.write('//The design file including:\n')
            for file_design in file_group:
                top_group.write('//--' + file_design + ';\n')
            top_group.write('-------------------------------------------------------------------*/\n\n')

            top_group.write('module top (\n')

            num_port = 0
            cmt_input = {}
            cmt_output = {}
            cmt_inout = {}
            cmt_sig = {}
            port_sig = {}
            wire_sig = {}
            for i in sig_dir:
                cmt_input[i] = str('to: ' + str(sig_dir[i]['input_inst']) + '; ') if sig_dir[i]['input_num'] > 0 else ''
                cmt_output[i] = str('from: ' + str(sig_dir[i]['output_inst']) + '; ') if sig_dir[i]['output_num'] > 0 else ''
                cmt_inout[i] = str('connect: ' + str(sig_dir[i]['inout_inst']) + '; ') if sig_dir[i]['inout_num'] > 0 else ''
                cmt_sig[i] = '\t//' + cmt_input[i] + cmt_output[i] + cmt_inout[i]
                port_sig[i] = str('\t' + sig_dir[i]['port_type'] + '\t' + sig_dir[i]['port_width'] + '\t' + sig_dir[i]['port_name'])
                wire_sig[i] = str('wire' + '\t' + sig_dir[i]['port_width'] + '\t' + sig_dir[i]['port_name'])
                if sig_dir[i]['input_num'] == 0 or sig_dir[i]['output_num'] == 0 or sig_dir[i]['inout_num'] > 0:
                    num_port = num_port + 1
                if sig_dir[i]['output_num'] > 1:
                    print('Error: ' + i + ' have been multiple derived by ' + str(sig_dir[i]['output_inst']))
                if sig_dir[i]['input_num'] > 1:
                    print('Info: ' + i + ' have been broadcast to ' + str(sig_dir[i]['input_inst']))

            cnt_port = 0
            for i in sig_dir:
                if sig_dir[i]['input_num'] == 0 or sig_dir[i]['output_num'] == 0 or sig_dir[i]['inout_num'] > 0:
                    if cnt_port == num_port - 1:
                        top_group.write(port_sig[i] + ' ' + cmt_sig[i] + '\n);\n\n')
                    else:
                        top_group.write(port_sig[i] + ',' + cmt_sig[i] + '\n')
                    cnt_port = cnt_port + 1

            for i in sig_dir:
                if sig_dir[i]['input_num'] > 0 and sig_dir[i]['output_num'] > 0 and sig_dir[i]['inout_num'] == 0:
                    top_group.write(wire_sig[i] + ' ' + cmt_sig[i] + '\n')

    # Write module instance
    with open(inst_path, 'r') as instance_group:
        res = instance_group.read()
        with open(top_path, 'a') as top_group:
            top_group.write(res + '\nendmodule\n')

    # Clean the env
    if os.path.exists(directory + '/' + inst):
        os.remove(directory + '/' + inst)
        print('\nInfo: ' + top + ' have been generated\n')
        print('-----Connector Generator End---------')
