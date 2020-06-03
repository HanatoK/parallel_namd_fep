#!/usr/bin/env python3
from shutil import copyfile

num_processes = 16
forward_prefix = "forward"
backward_prefix = "backward"

copyfile(f"{forward_prefix}.{str(0).zfill(len(str(num_processes)))}.fepout", f"{forward_prefix}_merged.fepout")
with open(f"{forward_prefix}_merged.fepout", "a+") as fh_merged:
    for i in range(1, num_processes):
        forward_fepout_filename = f"{forward_prefix}." + str(i).zfill(len(str(num_processes))) + ".fepout"
        with open(forward_fepout_filename, "r") as fh_i:
            lines = fh_i.readlines()[2:]
            fh_merged.writelines(lines)

copyfile(f"{backward_prefix}.{str(num_processes-1).zfill(len(str(num_processes)))}.fepout", f"{backward_prefix}_merged.fepout")
with open(f"{backward_prefix}_merged.fepout", "a+") as fh_merged:
    for i in reversed(range(0, num_processes - 1)):
        backward_fepout_filename = f"{backward_prefix}." + str(i).zfill(len(str(num_processes))) + ".fepout"
        with open(backward_fepout_filename, "r") as fh_i:
            lines = fh_i.readlines()[2:]
            fh_merged.writelines(lines)
