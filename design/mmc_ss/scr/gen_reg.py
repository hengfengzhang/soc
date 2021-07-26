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

def gen_bitwise(reg_bit):
    string = '\t[' + str(reg_bit) + '-1:0]\t'
    return string

def gen_reg_def(reg_name, bitwise):
    string = '\n\nreg\t[ ' + bitwise + '-1:0 ]\t' + reg_name + ';'
    return string

def gen_offset_addr_assign(base_address):
    string = '\n\nwire [31: 0]   offset_addr;\n'\
             '\nassign offset_addr = paddr - ' + base_address + ';'
    return string

def gen_paddr_d_block(base_address):
    string = '''
\nreg [31:0] paddr_d;
always @(posedge pclk or negedge presetn)
    if(!presetn)
        paddr_d <= 32'h0;
    else
        paddr_d <= offset_addr;'''
    return string

def gen_clk_always():
    string = '''
\nalways @(posedge pclk or negedge presetn)'''
    return string

def gen_rst_block(reg_name, reg_default):
    string = '\n\tif(!presetn)\n\t\t'\
             + reg_name + ' <= ' + str(reg_default) + ';'
    return string

def hw_wr_cond(reg_name):
    string = '( ' + reg_name + '_hw_wen )'
    return string

def hw_rd_data(reg_name):
    string = ' ' + reg_name + '_hw_rdata '
    return string

def hw_wr_data(reg_name):
    string = ' ' + reg_name + '_hw_wdata '
    return string

def hw_wr_wen(reg_name):
    string = '' + reg_name + '_hw_wen'
    return string

def gen_hw_wr_block(reg_name, hw_wr):
    if 'Y' in hw_wr:
        string = '\n\telse if ' + hw_wr_cond(reg_name) + '\n\t\t'\
                 + reg_name + ' <= ' + hw_wr_data(reg_name) + ';'
    else:
        string = None
    return string

def gen_hw_rd_assign(reg_name, hw_wr):
    if 'Y' in hw_wr:
        string = '\n\nassign\t' + hw_rd_data(reg_name) + '\t=\t' + reg_name + ';'
    else:
        string = None
    return string

def sw_wr_en():
    string = 'penable && pwrite && psel'
    return string

def sw_addr_en(offset_address):
    string = '(paddr_d==' + offset_address + ')'
    return string

def sw_wr_cond(offset_address):
    string = '( ' + sw_addr_en(offset_address) + ' && ' + sw_wr_en() + ' )'
    return string

def gen_sw_wr_block(reg_name, sw_wr, offset_address):
    if 'Y' in sw_wr:
        string = '\n\telse if ' + sw_wr_cond(offset_address) + '\n\t\t'\
                 + reg_name + ' <= ' + 'pwdata;'
    else:
        string = None
    return string

def sw_access_port():
    string ='''
\tinput\t\t\tpclk,
\tinput\t\t\tpresetn,
\tinput\t\t\tpsel,
\tinput\t\t\tpwrite,
\tinput\t\t\tpenable,
\tinput\twire\t[31:0]\tpaddr,
\tinput\twire\t[31:0]\tpwdata,
\toutput\treg\t[31:0]\tprdata,
\toutput\t\t\tpready
'''
    return string

def gen_sw_rd_en():
    string = '( psel && (!pwrite) && (!penable) )'
    return string

def gen_sw_rd_always(reg_mux):
    rdat = ' 32\'h00000000\n'
    for rdata_mux in reg_mux:
        rdat = rdat + '\t\t\t\t\t|' + rdata_mux
    string = '''
\n\nalways @(posedge pclk or negedge presetn)
    if(!presetn)
        prdata <= 32'h00000000;
    else if''' + gen_sw_rd_en() + '\n' + \
'\t\tprdata <= ' + rdat.strip('\n') + ';'
    return string

def gen_pready_assign(reg_mux):
    rdat = '\n\t\t\t\t\t'
    for rdata_mux in reg_mux:
        rdat = rdat + '\n\t\t\t\t\t| ' + rdata_mux
    string = '\n\nassign\tpready\t=\t~( ' + sw_wr_en() + ' & (' + '1\'h0' +  rdat.strip('\n') + ')\t);'
    return string


def gen_rtl(inst_head, inst_body, inst_tail):
    inst_rtl = []
    for lines in (inst_head, inst_body, inst_tail):
        for line in lines:
            inst_rtl.append(line)
    return inst_rtl

def get_reg_def_dict(reg_def_list):
    reg_def_dict = {}
    for reg_def in reg_def_list:
        offset_address ,reg_name ,reg_bitwise ,reg_default ,sw_wr ,sw_rd ,hw_wr ,hw_rd, description = reg_def
        reg_attri = [offset_address ,reg_bitwise ,reg_default ,sw_wr ,sw_rd ,hw_wr ,hw_rd]
        reg_def_dict.update({reg_name:reg_attri})
    return reg_def_dict

def gen_reg_rtl(output_file, base_address, reg_def_dict):
    inst_head = []
    inst_body = []
    inst_tail = []

    design_name = output_file.replace('.v', '')
    module_begin = 'module ' + design_name
    port_begin = '(  //port begin'
    port_end = '); //port end'
    module_end = '\nendmodule'

    # generate header
    inst_head.append(module_begin)
    inst_head.append(port_begin)
    for reg_name in reg_def_dict.keys():
        offset_address, reg_bit, reg_default, sw_wr, sw_rd, hw_wr, hw_rd = reg_def_dict[reg_name]
        if hw_wr == 'Y':
            port_line = '\n\tinput ' + gen_bitwise(reg_bit) + ' ' + hw_wr_data(reg_name) + ', '
            inst_head.append(port_line)
            port_line = '\n\tinput ' + '\t\t\t' + ' ' + hw_wr_wen(reg_name) + ', '
            inst_head.append(port_line)
        if hw_rd == 'Y':
            port_line = '\n\toutput ' + gen_bitwise(reg_bit) + ' ' + hw_rd_data(reg_name) + ', '
            inst_head.append(port_line)
    inst_head.append(sw_access_port())
    inst_head.append(port_end)

    # generate body
    reg_mux = []
    hw_wr_list = []
    inst_body.append(gen_offset_addr_assign(base_address))
    inst_body.append(gen_paddr_d_block(base_address))
    for reg_name in reg_def_dict.keys():
        offset_address, reg_bit, reg_default, sw_wr, sw_rd, hw_wr, hw_rd = reg_def_dict[reg_name]

        inst_body.append(gen_reg_def(reg_name, reg_bit))

        inst_body.append(gen_clk_always())
        inst_body.append(gen_rst_block(reg_name, reg_default))
        if 'Y' in hw_wr:
            inst_body.append(gen_hw_wr_block(reg_name, hw_wr))
            hw_wr_list.append('(' + sw_addr_en(offset_address) + '&&' + hw_wr_wen(reg_name) + ')')
        if 'Y' in sw_wr:
            inst_body.append(gen_sw_wr_block(reg_name, sw_wr, offset_address))
        if 'Y' in hw_rd:
            inst_body.append(gen_hw_rd_assign(reg_name, hw_rd))
        if 'Y' in sw_rd:
            reg_mux.append(' ( ' + reg_name + ' & { ' + str(reg_bit) + '{(offset_addr==' + offset_address + ')} } )\n')


    inst_body.append(gen_sw_rd_always(reg_mux))

    inst_body.append(gen_pready_assign(hw_wr_list))

    inst_body.append(module_end)

    with open(output_file, 'w+') as w_obj:
        inst_rtl = gen_rtl(inst_head, inst_body, inst_tail)
        for line in inst_rtl:
            print(line)
            w_obj.write(str(line))

def gen_reg_model(output_file, base_address, reg_def_dict):
    print('''
//TBD
uvm_block_begin
    uvm_map_begin
        uvm_map_define
    uvm_map_end    
    uvm_reg_begin
        uvm_field_begin
            uvm_field_define
        uvm_field_end
    uvm_reg_end   
uvm_block_end
     ''')

if __name__ == '__main__':
    input_file  = []
    output_file = []
    input_file, output_file = get_opt()
    base_address, reg_def_list = get_excel(input_file)
    reg_def_dict = get_reg_def_dict(reg_def_list)
    gen_reg_rtl(output_file, base_address, reg_def_dict)
    gen_reg_model(output_file, base_address, reg_def_dict)




