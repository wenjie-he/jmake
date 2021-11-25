#!/usr/bin/python3

import re
import yaml
import os
import sys

BUILD_TARGET="BUILD_TARGET"
BUILD_YAML="BUILD.yaml"

if __name__ == "__main__":
    repo_dir = sys.argv[1]
    module = sys.argv[2]
    with open(repo_dir + BUILD_YAML, "r", encoding = "utf-8") as file:
        file_stream = file.read()
    yaml_root = yaml.load(file_stream, yaml.FullLoader)
    if yaml_root.__contains__(module):
        module_root = yaml_root[module]
        module_type = module_root["TYPE"]
        print (module_type)
