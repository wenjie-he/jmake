#!/usr/bin/python3

import re
import yaml
import os
import sys

BUILD_TARGET="BUILD_TARGET"
BUILD_YAML="BUILD.yaml"

def ReadBuildYaml(repo):
    yaml_file_dir = repo
    with open(yaml_file_dir + BUILD_YAML, "r", encoding = "utf-8") as file:
        file_stream = file.read()
    yaml_root = yaml.load(file_stream, yaml.FullLoader)
    return yaml_root

def GetTargetList(yaml_root):
    target_list = []
    if yaml_root.__contains__(BUILD_TARGET):
        target_list = yaml_root[BUILD_TARGET]
    return target_list

if __name__ == "__main__":
    yaml_dir = sys.argv[1]
    yaml_root = ReadBuildYaml("/home/lianjin/codebase/" + yaml_dir)

    target_list = GetTargetList(yaml_root)
    print(" ".join(str(i) for i in target_list))
