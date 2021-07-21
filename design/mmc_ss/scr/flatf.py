#!/usr/bin/python
#hengfengzhang
#20210721

import os
import sys
import re
import argparse
import shutil

def get_parse():
  parser = argparse.ArgumentParser(description='Flating the input filelist with specified macro')
  parser.add_argument('-f', '--file'  , metavar='vlogfile.f', nargs='+', default='../vlogfile.f', help='input filelist'    )
  parser.add_argument('-d', '--define', metavar='FPGA      ', nargs='+', default='ASIC'         , help='input define macro')
  parser.add_argument('-o', '--output', metavar='filelist.f', nargs='+', default='./filelist.f' , help='output filelist'   )
  parser.add_argument('-m', '--macro' , metavar='${SOC_WS} ', nargs='+', default='SOC_WS'       , help='macro path define' )
  args = parser.parse_args()
  print(str(args))
  return args.file, args.define, args.output, args.macro

def match_spaceline(string):
  return re.search(r'^$', string)

def match_comment(string):
  return re.search(r'\s?\/\/\s?', string)

def match_fpath(string):
  return re.search(r'-f\s+\/\w+', string)

def match_ypath(string):
  return re.search(r'-y\s+\/\w+', string)

def match_vpath(string):
  return re.search(r'-v\s+\/\w+', string)

def match_dpath(string):
  return re.search(r'\s?\/\w+', string)

def match_incdir(string):
  return re.search(r'\+incdir\+', string)

def match_libext(string):
  return re.search(r'\+libext\+', string)

def match_ifdef(string):
  return re.search(r'\`ifdef', string)

def match_ifndef(string):
  return re.search(r'\`ifndef', string)

def match_endif(string):
  return re.search(r'\`endif', string)

def match_elseif(string):
  return re.search(r'\`elseif', string)

def match_else(string):
  return re.search(r'\`else', string)

def update_macro_block(string, macro_sts, macro_stk):
  if macro_sts:
    print('INFO: This macro block is  enable -> hier ' + str(len(macro_stk)) +' ' + string.strip())
    return True
  else:
    print('INFO: This macro block is disable  -> hier ' + str(len(macro_stk)) +' ' + string.strip())
    return False

def check_path(string):
  path = string.replace(r'+incdir+', '')
  path = path.split()[-1]
  return os.path.exists(path)

def find_design_file(file_path, macro_sts, macro_stk, file_out):
  print('INFO: Parse filelist   '+str(file_path))
  with open(file_path, 'r') as lines:
    for line in lines.readlines():
      if(macro_path):
        for replace_macro in replace_macro_list:
          line = line.replace(replace_macro, macro_path)
      else:
        print('ERROR: Cannot find macro define ' + str(macro_path))
      if match_comment(line) or match_spaceline(line):
        continue
      elif match_ifdef(line) :
        macro_stk.append(macro_sts)
        if (line.split()[-1] in macro_list):
          macro_sts = update_macro_block(line, macro_sts, macro_stk)
        else:
          macro_sts = update_macro_block(line, False, macro_stk)
      elif match_ifndef(line) :
        macro_stk.append(macro_sts)
        if (line.split()[-1] not in macro_list):
          macro_sts = update_macro_block(line, macro_sts, macro_stk)
        else:
          macro_sts = update_macro_block(line, False, macro_stk)
      elif match_elseif(line) :
        if (line.split()[-1] in macro_list):
          macro_sts_d = macro_stk.pop()
          macro_stk.append(macro_sts_d)
          macro_sts = update_macro_block(line, macro_sts_d, macro_stk)
        else:
          macro_sts = update_macro_block(line, False, macro_stk)
      elif match_else(line):
        macro_sts_d = macro_stk.pop()
        macro_stk.append(macro_sts_d)
        if macro_sts_d:
          macro_sts = update_macro_block(line, not macro_sts, macro_stk)
        else:
          macro_sts = update_macro_block(line, False, macro_stk)
      elif match_endif(line):
        macro_sts = macro_stk.pop()
        print('INFO: Returen to macro hier ' + str(len(macro_stk)) +' '+ line.strip() )
      elif macro_sts:
        if match_fpath(line):
          find_design_file(line.split()[-1], macro_sts, macro_stk, file_out)
        elif  match_dpath(line) or match_vpath(line) or match_ypath(line) or match_incdir(line) :
          if check_path(line) and (line not in file_out):
            file_out.append(line.strip(' '))
          else:
            print('ERROR: Cannot find this file in path ' + str(macro_sts) + ' -> ' + line)
        elif match_libext(line):
            file_out.append(line.strip(' '))
        else:
          print('WARNING: Cannot recognize the line -> ' + line)
      else:
        print('INFO: This line is ignored for macro block is disabled ' + str(macro_sts) + ' -> ' + line.strip() )

if __name__ == '__main__':

  global macro_list 
  global macro_path 
  global replace_macro_list
  macro_list = []
  macro_stk  = []
  macro_sts  = True
  file_list  = []
  input_list = []
  replace_macro_list = []
  directory  = os.getcwd()
  input_list, macro_list, out_file, macro_replace = get_parse()
  macro_path = os.getenv(str(macro_replace))
  replace_macro_list.append('${'+macro_replace+'}')
  output_filelist_path  = directory + '/' + out_file

  if os.path.exists(output_filelist_path):
    os.remove(output_filelist_path)
  for input_filelist_path in input_list:
    process_filelist_path = directory + '/' + input_filelist_path
    with open(output_filelist_path, 'a+') as file_out:
      find_design_file(process_filelist_path, macro_sts, macro_stk, file_list)
      file_out.writelines(file_list)
