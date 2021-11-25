#!/usr/bin/python3

import re
import yaml
import os
import sys

CODEBASE="~/codebase/"
BUILD_TARGET="BUILD_TARGET"
BUILD_YAML="BUILD.yaml"
DEPS="DEPS"
REPO="REPO"
BRANCH="BRANCH"
MODULE="MODULE"
LEAK="LEAK"

if __name__ == "__main__":
    local_repo_dir = sys.argv[1]
    module = sys.argv[2]

    with open(local_repo_dir + BUILD_YAML, "r", encoding = "utf-8") as file:
        file_stream = file.read()
    yaml_root = yaml.load(file_stream, yaml.FullLoader)

    depend_lists = []
    if not yaml_root.__contains__(module):
        print("\n".join(str(i) for i in depend_lists))
        sys.exit()
    module_root = yaml_root[module]
    if not module_root.__contains__(LEAK):
        print("\n".join(str(i) for i in depend_lists))
        sys.exit()
    leak_modules = module_root[LEAK]
    for module in leak_modules:
        depend_lists.append(local_repo_dir + " "  + module)

    print("\n".join(str(i) for i in depend_lists))
