#!/usr/bin/env python3
from shutil import copyfile
from math import isclose

#################################################
# running settings
#################################################
# executable of the NAMD binary
namd_binary = "namd2"
# number of process
num_processes = 16
# use single-node GPU
use_single_node_gpu = True
# used gpu devices
# default from 0 to (num_processes - 1)
gpu_devices = []
# number of threads per NAMD process (+pN)
num_threads_per_process = 1
#################################################

#################################################
# FEP settings
#################################################
# starting lambda from
lambda_start = 0.0
# ending lambda
lambda_end = 1.0
# number of stratified windows
num_windows = 50
# forward template file
forward_template = "forward.template"
# backward template file
backward_template = "backward.template"
# total steps of alchemical transformation in a single window
steps_per_window = 50000
# equilibrium steps before collecting data to the ensemble average
equilibrium_steps = 10000
# prefix for generated NAMD configuration files and output
forward_prefix = "forward"
backward_prefix = "backward"
#################################################

#################################################
# Temporary variables
#################################################
command_list_forward = []
command_list_backward = []
keyword_indent_width = 24
# NAMD keywords
lambda1_keyword = "alchLambda"
lambda2_keyword = "alchLambda2"
equilibrium_steps_keyword = "alchEquilSteps"
running_keyword = "run"
fepout_keyword = "alchOutFile"
outputname_keyword = "outputname"
restartname_keyword = "restartname"
bincoordinates_keyword = "bincoordinates"
binvelocities_keyword = "binvelocities"
extendedsystem_keyword = "extendedsystem"
firsttimestep_steps_keyword = "firsttimestep"
cudasoaintegrate_keyword = "CUDASOAintegrate"
ldbalancer_keyword = "ldbalancer"
alchpmecuda_keyword = "alchPMECUDA"

#################################################
# Functions
#################################################
def gen_namd_fep_config_string_forward(lambda_from, lambda_to, window_size, output_index):
    print(f"Generate config (forward): lambda start = {lambda_from:.7f}, end = {lambda_to:.7f}, stride = {window_size:.7f} ; index = {output_index}")
    # compute the number of windows
    N = int((lambda_to - lambda_from) / window_size)
    # margin for not dividing exactly
    margin = (lambda_to - lambda_from) - N * window_size
    lambda_to_adjusted = lambda_to - margin
    # output and restart settings
    fepout_filename = forward_prefix + "." + str(output_index) + ".fepout"
    outputname = forward_prefix + "." + str(output_index)
    result  = f"\n{outputname_keyword:{keyword_indent_width}} {outputname}\n"
    result += f"{restartname_keyword:{keyword_indent_width}} {outputname}\n"
    result += f"{fepout_keyword:{keyword_indent_width}} {fepout_filename}\n"
    # generating lambda1 and lambda2
    lambda_tmp1 = lambda_from
    lambda_tmp2 = lambda_from + window_size * 1.0
    while (lambda_tmp2 < lambda_to_adjusted) or (isclose(lambda_tmp2, lambda_to_adjusted, abs_tol = 1e-9)):
        result += "\n"
        result += f"{lambda1_keyword:{keyword_indent_width}} {lambda_tmp1:.7f}\n"
        result += f"{lambda2_keyword:{keyword_indent_width}} {lambda_tmp2:.7f}\n"
        result += f"{equilibrium_steps_keyword:{keyword_indent_width}} {equilibrium_steps}\n"
        result += f"{firsttimestep_steps_keyword:{keyword_indent_width}} 0\n"
        result += f"{running_keyword:{keyword_indent_width}} {steps_per_window}\n"
        lambda_tmp1 += window_size
        lambda_tmp2 += window_size
    if not isclose(margin, 0, abs_tol = 1e-9):
        result += "\n"
        result += f"{lambda1_keyword:{keyword_indent_width}} {lambda_to_adjusted:.7f}\n"
        result += f"{lambda2_keyword:{keyword_indent_width}} {lambda_to:.7f}\n"
        result += f"{equilibrium_steps_keyword:{keyword_indent_width}} {equilibrium_steps}\n"
        result += f"{firsttimestep_steps_keyword:{keyword_indent_width}} 0\n"
        result += f"{running_keyword:{keyword_indent_width}} {steps_per_window}\n"
    return result

def gen_namd_fep_config_string_backward(lambda_from, lambda_to, window_size, output_index):
    print(f"Generate config (backward): lambda start = {lambda_from:.7f}, end = {lambda_to:.7f}, stride = {window_size:.7f} ; index = {output_index}")
    # compute the number of windows
    N = int((lambda_from - lambda_to) / window_size)
    # margin for not dividing exactly
    margin = (lambda_from - lambda_to) - N * window_size
    lambda_from_adjusted = lambda_from - margin
    # output and restart settings
    fepout_filename = backward_prefix + "." + str(output_index) + ".fepout"
    outputname = backward_prefix + "." + str(output_index)
    result  = f"\n{outputname_keyword:{keyword_indent_width}} {outputname}\n"
    result += f"{restartname_keyword:{keyword_indent_width}} {outputname}\n"
    # need forward output files as backward input
    forward_output = forward_prefix + "." + str(output_index)
    result += f"{bincoordinates_keyword:{keyword_indent_width}} {forward_prefix}.{output_index}.coor\n"
    result += f"{binvelocities_keyword:{keyword_indent_width}} {forward_prefix}.{output_index}.vel\n"
    result += f"{extendedsystem_keyword:{keyword_indent_width}} {forward_prefix}.{output_index}.xsc\n"
    result += f"{fepout_keyword:{keyword_indent_width}} {fepout_filename}\n"
    # generating lambda1 and lambda2
    lambda_tmp1 = lambda_from_adjusted
    lambda_tmp2 = lambda_from_adjusted - window_size * 1.0
    if not isclose(margin, 0, abs_tol = 1e-9):
        result += "\n"
        result += f"{lambda1_keyword:{keyword_indent_width}} {lambda_from:.7f}\n"
        result += f"{lambda2_keyword:{keyword_indent_width}} {lambda_from_adjusted:.7f}\n"
        result += f"{equilibrium_steps_keyword:{keyword_indent_width}} {equilibrium_steps}\n"
        result += f"{firsttimestep_steps_keyword:{keyword_indent_width}} 0\n"
        result += f"{running_keyword:{keyword_indent_width}} {steps_per_window}\n"
    while (lambda_tmp2 > lambda_to) or (isclose(lambda_tmp2, lambda_to, abs_tol = 1e-9)):
        result += "\n"
        result += f"{lambda1_keyword:{keyword_indent_width}} {lambda_tmp1:.7f}\n"
        result += f"{lambda2_keyword:{keyword_indent_width}} {abs(lambda_tmp2):.7f}\n"
        result += f"{equilibrium_steps_keyword:{keyword_indent_width}} {equilibrium_steps}\n"
        result += f"{firsttimestep_steps_keyword:{keyword_indent_width}} 0\n"
        result += f"{running_keyword:{keyword_indent_width}} {steps_per_window}\n"
        lambda_tmp1 -= window_size
        lambda_tmp2 -= window_size
    return result

def check_forward_template(filename):
    to_be_cleared_fields = ["outputname", "restartname", "alchOutFile", "alchLambda", "alchLambda2", "firsttimestep", "run", "alchPMECUDA", "CUDASOAintegrate"]
    with open(filename, "r") as file_handle:
        lines = file_handle.readlines()
    with open(filename, "w") as file_handle:
        for line in lines:
            fields = line.split()
            if len(fields) > 0:
                if fields[0].lower() in (name.lower() for name in to_be_cleared_fields):
                    line = "\n"
            file_handle.write(line)

def check_backward_template(filename):
    to_be_cleared_fields = ["outputname", "restartname", "alchOutFile", "alchLambda", "alchLambda2", "firsttimestep", "run", "alchPMECUDA", "CUDASOAintegrate", "bincoordinates", "binvelocities", "extendedsystem"]
    with open(filename, "r") as file_handle:
        lines = file_handle.readlines()
    with open(filename, "w") as file_handle:
        for line in lines:
            fields = line.split()
            if len(fields) > 0:
                if fields[0].lower() in (name.lower() for name in to_be_cleared_fields):
                    line = "\n"
            file_handle.write(line)

def gen_gpu_config_string():
    result = "\n"
    if use_single_node_gpu:
        result += f"{cudasoaintegrate_keyword:{keyword_indent_width}} on\n"
        result += f"{alchpmecuda_keyword:{keyword_indent_width}} on\n"
    return result

def gen_namd_config():
    global gpu_devices
    if len(gpu_devices) == 0:
        gpu_devices = list(range(0, num_processes))
    elif use_single_node_gpu and (len(gpu_devices) != num_processes):
        raise RuntimeError(f"The number of GPU devices ({len(gpu_devices)}) does not match the number of parallel processes ({num_processes}).")
    index_list = list(range(0, num_processes))
    window_size = (lambda_end - lambda_start) / float(num_windows)
    window_size_per_gpu = int(num_windows / num_processes) * window_size
    window_size_last_gpu = (lambda_end - lambda_start) - int(num_windows / num_processes) * window_size * (num_processes - 1)
    lambda_tmp1 = lambda_start
    lambda_tmp2 = lambda_start + window_size_per_gpu
    for i,j in zip(index_list,gpu_devices):
        index = str(i).zfill(len(str(num_processes)))
        if use_single_node_gpu:
            gpu_arguments = f"+devices {j}"
        else:
            gpu_arguments = ""
        # copy forward template to forward FEP config file
        forward_filename = forward_prefix + "." + index + ".namd"
        copyfile(forward_template, forward_filename)
        check_forward_template(forward_filename)
        forward_config_string = gen_namd_fep_config_string_forward(lambda_tmp1, lambda_tmp2, window_size, index)
        with open(forward_filename, "a+") as file_handle:
            file_handle.write(gen_gpu_config_string())
            file_handle.write(forward_config_string)
        # generate command for running NAMD
        forward_log_filename = forward_prefix + "." + index + ".log"
        forward_namd_cmdline = f"'{namd_binary}' +idlepoll {gpu_arguments} +p{num_threads_per_process} '{forward_filename}' > {forward_log_filename}"
        command_list_forward.append(forward_namd_cmdline)
        # copy backward template to backward FEP config file
        backward_filename = backward_prefix + "." + index + ".namd"
        copyfile(backward_template, backward_filename)
        check_backward_template(backward_filename)
        backward_config_string = gen_namd_fep_config_string_backward(lambda_tmp2, lambda_tmp1, window_size, index)
        with open(backward_filename, "a+") as file_handle:
            file_handle.write(gen_gpu_config_string())
            file_handle.write(backward_config_string)
        # generate command for running NAMD
        backward_log_filename = backward_prefix + "." + index + ".log"
        backward_namd_cmdline = f"'{namd_binary}' +idlepoll {gpu_arguments} +p{num_threads_per_process} '{backward_filename}' > {backward_log_filename}"
        command_list_backward.append(backward_namd_cmdline)
        # increase for next stride
        lambda_tmp1 += window_size_per_gpu
        if i == (num_processes - 2):
            lambda_tmp2 += window_size_last_gpu
        else:
            lambda_tmp2 += window_size_per_gpu

def gen_shell_script():
    with open("run.sh", "w") as file_handle:
        file_handle.write("#!/bin/sh\n")
        file_handle.write("START=$(date +%s)\n")
        for forward_cmdline, backward_cmdline in zip(command_list_forward, command_list_backward):
            tmp_line = "{ " + forward_cmdline + " && " + backward_cmdline + "; } &"
            file_handle.write(tmp_line + "\n")
        file_handle.write("wait\n")
        file_handle.write("END=$(date +%s)\n")
        file_handle.write("DIFF=$(( $END - $START ))\n")
        file_handle.write("echo \"It took $DIFF seconds\"\n")

gen_namd_config()
gen_shell_script()
