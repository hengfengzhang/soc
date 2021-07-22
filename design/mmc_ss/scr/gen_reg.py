#! /bin/python
#hengfengzhang
#20200721

import os
import sys
import re
import optparse
import xlrd


def get_opt():
    parser = optparse.OptionParser()
    parser.add_option("-i", "--input", dest="input_file", help="input excel which define apb registers")
    parser.add_option("-o", "--output", dest="output_file", help="output rtl which instance apb registers")
    args, opts = parser.parse_args()
    return args.input_file, args.output_file


def get_excel(input_file):
    book = xlrd.open_workbook(filename=input_file)
    sheet = book.sheets()[0]
    reg_def_list = []
    for i in range(sheet.nrows):
        row_data = sheet.row_values(i)
        if i==0:
            base_address = row_data[1]
        if i>1:
            reg_def_list.append(row_data)
    return base_address, reg_def_list

def gen_addr(offset_address):
    string = '''\nreg [31:0] paddr_d;
always @(posedge pclk or negedge presetn)
    if(!presetn)
        paddr_d <= 32'h0;
    else
        paddr_d <= paddr - ''' + str(base_address)+';\n'
    return string

def gen_reg(reg_name, reg_bit):
    string = '\n\nreg\t[' + str(reg_bit) + '-1:0]\t' + reg_name + ';'

def gen_clk():
    string = '\n\nalways @(posedge pclk or negedge presetn)'
    return string

def gen_rst(reg_name, reg_default):
    string = '\nif(!presetn)\n\t\t' + reg_name + '\t<=\t' + str(reg_default) + ';'
    return  string

def gen_hw_wr(reg_name, hw_wr):
    if 'Y' in hw_wr:
        string = '\nelse if( ' + reg_name + '_hw_en )\n\t\t' + reg_name + '\t<=\t' + reg_name + '_hw_wdat' + ';'
    else:
        string = None
    return string

def gen_sw_wr(reg_name, sw_wr):
    if 'Y' in sw_wr :
        string = '\nelse if( paddr_d' + '=='+offset_address+'\t&&penable&&pwrite&&psel\t)\n\t\t' + reg_name + '\t<=\t' + 'pwdata' + ';'
    else:
        string = None
    return string

if __name__ == '__main__':
    input_file  = []
    output_file = []
    input_file, output_file = get_opt()
    base_address, reg_def_list = get_excel(input_file)
    rtl_wr = []
    hw_wr_proc = []
    hw_wr_port = []
    hw_rd_proc = []
    hw_rd_port = []
    sw_rd_port = []
    sw_rd_proc = []
    sw_rd_port.append('''
input pclk,
input presetn,
input psel,
input pwrite,
input penable,
output prdata,
output pready
    ''')
    rtl_wr.append(gen_addr(base_address))
    sw_rd_proc.append(gen_clk())
    sw_rd_proc.append(gen_rst('prdata', '32h000000'))
    sw_rd_proc.append('\nelse if(\t!pwrite\t&&\t!penable\t&&\tpsel\t)\n\t\tprdata\t<=\t')
    for reg in reg_def_list:
        offset_address = reg[0]
        reg_name       = reg[1]
        reg_bit        = reg[2]
        reg_default    = reg[3]
        sw_wr          = reg[4]
        sw_rd          = reg[5]
        hw_wr          = reg[6]
        hw_rd          = reg[7]
        print(reg)
        rtl_wr.append(gen_reg(reg_name, reg_bit))
        rtl_wr.append(gen_clk())
        rtl_wr.append(gen_rst(reg_name, reg_default))
        rtl_wr.append(gen_hw_wr(reg_name, hw_wr))
        rtl_wr.append(gen_sw_wr(reg_name, sw_wr))
        if 'Y' in hw_wr:
            hw_wr_port.append('input\t\t\t\t' + reg_name + '_hw_en,\n')
            hw_wr_port.append('input\t[' + str(reg_bit) + '-1:0]\t' + reg_name + '_hw_wdat,\n')
        if 'Y' in hw_rd:
            hw_rd_port.append('output\t[' + str(reg_bit) + '-1:0]\t' + reg_name + '_hw_rdat,\n')
            hw_rd_proc.append('\nassign\t'+reg_name+'_hw_rdat\t=\t'+reg_name+';\n')
        if 'Y' in sw_rd:
            sw_rd_proc.append('\t\t\t\t(' + reg_name + ' & {'+str(reg_bit)+'{paddr=='+offset_address+'}}\t) |\n')
    sw_rd_proc.append('\t\t\t\t32\'h000000;')


    rtl_gen = ['module sc(\n']
    for line in hw_wr_port:
        rtl_gen.append(line)
    for line in hw_rd_port:
        rtl_gen.append(line)
    for line in sw_rd_port:
        rtl_gen.append(line)
    rtl_gen.append(');\n')
    for line in hw_rd_proc:
        rtl_gen.append(line)
    for line in sw_rd_proc:
        rtl_gen.append(line)
    for line in rtl_wr:
        if line != None:
           rtl_gen.append(line)

    rtl_gen.append('\n\nendmodule')

    with open(output_file, 'w+') as w_obj:
        for line in rtl_gen:
            w_obj.write(line)
