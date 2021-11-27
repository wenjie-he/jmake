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
TYPE="TYPE"
SRCS="SRCS"
COPT="COPT"
LEAK="LEAK"
HDRS="HDRS"
WORKSPACE="WORKSPACE"

if __name__ == "__main__":
    local_repo_dir = sys.argv[1]
    module = sys.argv[2]

    with open("/home/lianjin/codebase/" + local_repo_dir + BUILD_YAML, "r", encoding = "utf-8") as file:
        file_stream = file.read()
    yaml_root = yaml.load(file_stream, yaml.FullLoader)

    module_info = []
    if not yaml_root.__contains__(module):
        module_info.append("--error=" + "\"" + "no this module " + module + "\"")
        #print(module_info)
        print("\n".join(str(i) for i in module_info))
        sys.exit()
    module_root = yaml_root[module]

    module_info.append("--" + MODULE + "=\"" + module + "\"")
    
    # workspace
    if not module_root.__contains__(WORKSPACE) or not isinstance(module_root[WORKSPACE], str):
        module_info.append("--error=" + "\"" + module + " no workspace" + "\"")
        #print(module_info)
        print("\n".join(str(i) for i in module_info))
        sys.exit()
    module_info.append("--" + WORKSPACE + "=\"" + module_root[WORKSPACE] + "\"")

    # type
    if not module_root.__contains__(TYPE) or not isinstance(module_root[TYPE], str):
        module_info.append("--error=" + "\"" + module + " no type" + "\"")
        #print(module_info)
        print("\n".join(str(i) for i in module_info))
        sys.exit()
    module_info.append("--" + TYPE + "=\"" + module_root[TYPE] + "\"")

    # src
    if not module_root.__contains__(SRCS) or not isinstance(module_root[SRCS], str):
        module_info.append("--error=" + "\"" + module + " no srcs" + "\"")
        #print(module_info)
        print("\n".join(str(i) for i in module_info))
        sys.exit()
    module_info.append("--" + SRCS + "=\"" + module_root[SRCS] + "\"")

    # copts
    if not module_root.__contains__(COPT) or not isinstance(module_root[COPT], str):
        module_info.append("--error=" + "\"" + module + " no copt" + "\"")
        #print(module_info)
        print("\n".join(str(i) for i in module_info))
        sys.exit()
    module_info.append("--" + COPT + "=\"" + module_root[COPT] + "\"")

    # hdrs
    if module_root.__contains__(HDRS) and isinstance(module_root[HDRS], str):
        module_info.append("--" + HDRS + "=\"" + module_root[HDRS] + "\"")

    #print(module_info)
    print("\n".join(str(i) for i in module_info))
