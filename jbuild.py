#!/usr/bin/python3

import re
import shutil
import yaml
import os
import sys

CODEBASE="/home/lianjin/codebase/"
GLOBAL_OUTPUT="/home/lianjin/BUILD_OUTPUT/"
GLOBAL_TEMP="/home/lianjin/BUILD_TEMP/"

BUILD_YAML="BUILD.yaml"
BUILD_TARGET="BUILD_TARGET"
WORKSPACE="WORKSPACE"
LEAK="LEAK"
DEPS="DEPS"
REPO="REPO"
BRANCH="BRANCH"
MODULE="MODULE"
SRCS="SRCS"
HDRS="HDRS"
COPT="COPT"
TYPE="TYPE"
INC="INC"
LINK="LINK"

ARC="ar"
CXX="g++"

#############################################################################################################
map_module_depend = {}
list_build_done = []
map_repo_branch = {}
stack_sub_module = []
list_recurse_sub_module = []
#############################################################################################################
def build_module(module, srcs, workspace, copt, tar_type, repo, inc, link, depend_repo_list, headers):
    # copy header
    print("building module, repo : ", repo, ", module : ", module, ", depend : ", depend_repo_list)
    workspace += "/"
    for h in headers:
        tar_header_file = GLOBAL_OUTPUT + repo + "/include/" + h
        tar_header_dir = os.path.dirname(tar_header_file)
        if not os.path.isdir(tar_header_dir):
            os.makedirs(tar_header_dir)
        sub_header_dir = CODEBASE + repo + workspace + h
        shutil.copy2(sub_header_dir, tar_header_file)
    INC = ""
    LINK = ""
    link_map = {}
    for d in depend_repo_list:
        repo_dir = d[0]
        repo_module = d[1]
        INC += " -I " + GLOBAL_OUTPUT + repo_dir + "/include/"
        if repo not in link_map:
            link_map[repo_dir] = []
        link_map[repo_dir].append(repo_module)
    for k in link_map.keys():
        LINK += " -L " + GLOBAL_OUTPUT+ k + "/lib/"
        link_list = link_map[k]
        for v in link_list:
            LINK += " -l" + v
    INC += " " + inc
    LINK += " " + link

    module_target_changed = False
    object_list = ""
    for src in srcs:
        abs_src = CODEBASE + repo + workspace + src
        abs_obj = GLOBAL_TEMP + repo + workspace + src + ".o"
        abs_dep = GLOBAL_TEMP + repo + workspace + src + ".d"
        object_list += " " + abs_obj
        temp_dir = os.path.dirname(GLOBAL_TEMP + repo + workspace + src)
        if not os.path.isdir(temp_dir):
            os.makedirs(temp_dir)
        if not os.path.isfile(abs_obj):
            module_target_changed = True
            compile_cmd = CXX + " -o " + abs_obj + " -c " + abs_src + " " + copt + " " + INC
            print("compile cmd : ", compile_cmd)
            cmd_ret = os.system(compile_cmd)
            if cmd_ret != 0:
                print("fail to build object : ", abs_obj)
                return -1
        else:
            if not os.path.isfile(abs_dep):
                compile_cmd = CXX + " -MM " + " " + abs_src + " " + INC + " > " + abs_dep
                print("compile cmd : ", compile_cmd)
                cmd_ret = os.system(compile_cmd)
                if cmd_ret != 0:
                    print("fail to gen depend file : ", abs_dep)
                    return -1;
            else:
                depend_string = ""
                with open(abs_dep, 'r') as f:
                    depend_string = f.read()
                depend_str_list = depend_string.replace('\n', ' ').split(":")
                if len(depend_str_list) != 2:
                    print("illegal depend file : ", abs_dep)
                    return -1
                depend_string = depend_str_list[1].replace('\\', ' ')
                depend_str_list = depend_string.split()
                depend_file_time = os.path.getmtime(abs_dep)
                depend_file_changed = False
                for d in depend_str_list:
                    d = d.replace('\n', '').strip()
                    if not os.path.isfile(d):
                        depend_file_changed = True
                        break;
                    header_file_time = os.path.getmtime(d)
                    if header_file_time > depend_file_time:
                        depend_file_changed = True
                        break;
                if depend_file_changed:
                    compile_cmd = CXX + " -MM " + " " + abs_src + " " + INC + " > " + abs_dep
                    print("compile cmd : ", compile_cmd)
                    cmd_ret = os.system(compile_cmd)
                    if cmd_ret != 0:
                        print("fail to gen depend file : ", abs_dep)
                        return -1;

                with open(abs_dep, 'r') as f:
                    depend_string = f.read()
                depend_str_list = depend_string.replace('\n', ' ').replace('\\', ' ').split(":")
                if len(depend_str_list) != 2:
                    print("illegal depend file : ", abs_dep)
                    return -1;
                depend_string = depend_str_list[1]
                depend_str_list = depend_string.split()
                object_file_time = os.path.getmtime(abs_obj)
                for d in depend_str_list:
                    d = d.replace('\n', '').strip()
                    header_file_time = os.path.getmtime(d)
                    if header_file_time > object_file_time:
                        compile_cmd = CXX + " -o " + abs_obj + " -c " + abs_src + " " + copt + " " + INC
                        print("compile cmd : ", compile_cmd)
                        cmd_ret = os.system(compile_cmd)
                        if cmd_ret != 0:
                            print("fail to build object : ", abs_obj)
                            return -1
                        module_target_changed = True
                        break;
        output_bin_dir = os.path.dirname(GLOBAL_OUTPUT + repo + "bin/")
        if not os.path.isdir(output_bin_dir):
            os.makedirs(output_bin_dir)
        output_lib_dir = os.path.dirname(GLOBAL_OUTPUT + repo + "lib/")
        if not os.path.isdir(output_lib_dir):
            os.makedirs(output_lib_dir)
        include_dir = os.path.dirname(GLOBAL_OUTPUT + repo + "include/")
        if not os.path.isdir(include_dir):
            os.makedirs(include_dir)
        compile_cmd = ""
        target = ""
        if tar_type == "static":
            target = output_lib_dir + "/lib" + module + ".a"
            compile_cmd = ARC + " -r " + target + " "+ object_list
        elif tar_type == "shared":
            target = output_lib_dir + "/lib" + module + ".so"
            compile_cmd = CXX + " -shared -o " + target + " " + object_list + " " + LINK
        elif tar_type == "exec":
            target = output_bin_dir + "/" + module
            compile_cmd = CXX + " -o " + target + " " + object_list + " " + LINK 
        else:
            print("unrecoginzed tar type : ", tar_type)
            return -1
        if not os.path.isfile(target):
            module_target_changed = True

        if module_target_changed:
            print("compile cmd : ", compile_cmd)
            cmd_ret = os.system(compile_cmd)
            if cmd_ret != 0:
                print("fail to call cmd : ", compile_cmd)
                return -1;

    print("build done module, repo : ", repo, ", module : ", module)
    list_build_done.append((repo, module))
    return 0

#############################################################################################################
def pull_repo(repo_url, branch):
    re_repo_dir = re.findall(r"git@code.devops.xiaohongshu.com:(.+?).git", repo_url)
    if len(re_repo_dir) == 0:
        print("fail to reg repo url : ", repo_url)
        return -1;
    rela_repo_dir = re_repo_dir[0] + "/"
    if len(rela_repo_dir) == 0:
        print("illegal repo url : ", repo_url)
        return -1
    sub_repo_dir = CODEBASE + rela_repo_dir
    if not os.path.isdir(sub_repo_dir):
        git_clone_cmd = "git clone -b " + branch + " " + repo_url + " " + sub_repo_dir
        cmd_ret = os.system(git_clone_cmd)
        if cmd_ret != 0:
            print("fail to call cmd : ", git_clone_cmd)
            return -1;

    # check the branch 
    repo_branch_cmd = "cd " + sub_repo_dir + " && git symbolic-ref --short -q HEAD"
    repo_branch_fd = os.popen(repo_branch_cmd)
    repo_branch = repo_branch_fd.read().replace('\n', '').strip()
    cmd_ret = repo_branch_fd.close()
    if cmd_ret != None:
        print("fail to call cmd : ", repo_branch_cmd)
        return -1
    branch_sub_repo_dir = sub_repo_dir
    if repo_branch != branch:
        refresh_repo_cmd = "cd " + sub_repo_dir + " && git fetch origin " + branch + ":" + branch
        cmd_ret = os.system(refresh_repo_cmd)
        if cmd_ret != 0:
            print("fail to call cmd : ", refresh_repo_cmd)
            return -1
        if not os.path.isfile(sub_repo_dir + branch) or not Path(sub_repo_dir + branch).is_dir():
            print("git clone : ", repo_url)
            git_local_copy_cmd = "git clone -b " + branch + " " + sub_repo_dir + " " + sub_repo_dir + branch
            cmd_ret = os.system(git_local_copy_cmd)
            if cmd_ret != 0:
                print("fail to call cmd : ", git_local_copy_cmd)
                return -1
        branch_sub_repo_dir = sub_repo_dir + branch

    return (0, branch_sub_repo_dir)

#############################################################################################################

def sub_module(repo_url, branch, module_list):
    if repo_url in map_repo_branch and map_repo_branch[repo_url] != branch:
        print(repo_url, "has more branches, ", map_repo_branch, " and ", branch)
        return -1
    re_repo_dir = re.findall(r"git@code.devops.xiaohongshu.com:(.+?).git", repo_url)
    if len(re_repo_dir) == 0:
        print("fail to reg repo url : ", repo_url)
        return -1;
    rela_repo_dir = re_repo_dir[0] + "/"
    sub_repo_dir = CODEBASE + rela_repo_dir
    if len(rela_repo_dir) == 0:
        print("illegal repo url : ", repo_url)
        return -1
    (ret, branch_sub_repo_dir) = pull_repo(repo_url, branch)
    if ret != 0:
        print("fail to pull module")
        return -1;
    build_config_path = branch_sub_repo_dir + "/" + BUILD_YAML
    if not os.path.isfile(build_config_path):
        print("build config file not exsit : ", build_config_path)
    with open(build_config_path) as file:
        file_stream = file.read()
    yaml_root = yaml.load(file_stream, yaml.FullLoader)

    build_list = []
    if len(module_list) != 0:
        build_list = module_list
    else:
        if not yaml_root.__contains__(BUILD_TARGET):
            print("illegal build config file, no ", BUILD_TARGET)
            return -1
        build_list = yaml_root[BUILD_TARGET]
    
    for b in build_list:
        if (repo_url, b) in stack_sub_module:
            print("loop depend stack : ", stack_sub_module)
            return -1;
        if (repo_url, b) in list_recurse_sub_module:
            continue;
        stack_sub_module.append((repo_url, b))
        if not isinstance(b, str):
            print("build target : ", b, " in build list must be a str, rather : ", type(b))
            return -1
        if not yaml_root.__contains__(b):
            print("build target : ", b, " in build list, but not in BUILD.yaml")
            return -1
        module_root = yaml_root[b]
        
        workspace = ""
        if module_root.__contains__(WORKSPACE):
            if not isinstance(module_root[WORKSPACE], str):
                print("module : ", b, " WORKSPACE not str")
                return -1
            workspace = module_root[WORKSPACE]

        # read srcs copt defs type 
        if not module_root.__contains__(SRCS):
            print("module : ", b, " has not SRCS")
            return -1
        if not isinstance(module_root[SRCS], list):
            print("module : ", b, " SRCS not list")
            return -1;
        srcs = module_root[SRCS]
        src_list=[]
        for s in srcs:
            if os.path.isdir(s):
                print("invalid src : ", s, ", is a directory")
                return -1
            ls_cmd = "cd " + CODEBASE + rela_repo_dir + workspace + "&& ls " + s
            ls_fd = os.popen(ls_cmd)
            ls_srcs = ls_fd.read().replace('\n', ' ').strip()
            ls_srcs_list = ls_srcs.split()
            src_list += ls_srcs_list
            print("src_list : ", ls_srcs)
            cmd_ret = ls_fd.close()
            if cmd_ret != None:
                print("fail to call cmd : ", ls_cmd)
                return -1
        
        headers = []
        hdr_list = []
        if module_root.__contains__(HDRS):
            if not isinstance(module_root[HDRS], list):
                print("module : ", b, " HDRS not list")
                return -1;
            headers = module_root[HDRS]
            for h in headers:
                if os.path.isdir(h):
                    print("invalid src : ", h, ", is a directory")
                    return -1
                ls_cmd = "cd " + CODEBASE + rela_repo_dir + workspace + "&& ls " + h
                ls_fd = os.popen(ls_cmd)
                ls_hdrs = ls_fd.read().replace('\n', ' ').strip()
                ls_hdrs_list = ls_hdrs.split()
                hdr_list += ls_hdrs_list
                print("hdr_list : ", ls_hdrs)
                cmd_ret = ls_fd.close()
                if cmd_ret != None:
                    print("fail to call cmd : ", ls_cmd)
                    return -1


        if not module_root.__contains__(COPT):
            print("module : ", b, " has not COPT")
            return -1
        if not isinstance(module_root[COPT], str):
            print("module : ", b, " COPT not str")
            return -1;
        copt = module_root[COPT]

        if not module_root.__contains__(TYPE):
            print("module : ", b, " has not TYPE")
            return -1
        if not isinstance(module_root[TYPE], str):
            print("module : ", b, " TYPE not list")
            return -1;
        tar_type = module_root[TYPE]

        
        # include dir

        inc = "-I " + sub_repo_dir + "/" + workspace
        if module_root.__contains__(INC):
            if not instance(module_root[INC], str):
                print("module : ", b, " INC not str")
                return -1
            inc = module_root[INC]

        link = ""
        if module_root.__contains__(LINK):
            if not instance(module_root[LINK], str):
                print("module : ", b, " LINK not str")
                return -1
            link = module_root[LINK]

        
        if module_root.__contains__(DEPS):
            if not isinstance(module_root[DEPS], list):
                print("module : ", b, " illegal DEPS info, not list")
                return -1
            repo_deps= module_root[DEPS]
            for r in repo_deps:
                if not isinstance(r, dict):
                    print("module : ", b, ", dep : ", r, " not dict")
                    return (-1, )
                # check git repo
                if not r.__contains__(REPO):
                    print("module : ", b, ", dep : ", r, " has not REPO")
                    return (-1, )
                if not isinstance(r[REPO], str):
                    print("module : ", b, ", dep : ", r, " REPO not str")
                    return (-1, )
                dep_repo_url = r[REPO]
                repo_local_dir = re.findall(r"git@code.devops.xiaohongshu.com:(.+?).git", dep_repo_url)
                # check branch 
                if not r.__contains__(BRANCH):
                    print("module : ", b, ", dep : ", r, " has not BRANCH")
                    return (-1, )
                if not isinstance(r[BRANCH], str):
                    print("module : ", b, ", dep : ", r, " BRANCH not str")
                    return (-1, )
                dep_repo_branch = r[BRANCH]
                # check module
                dep_repo_module = []
                if r.__contains__(MODULE):
                    if not isinstance(r[MODULE], list):
                        print("module : ", b, ", dep : ", r, " MODULE not list")
                        return (-1, )
                    dep_repo_module = r[MODULE]

                (ret, sub_module_repo_dir) = sub_module(dep_repo_url, dep_repo_branch, dep_repo_module)
                if ret == -1:
                    print("fail to call sub module")
                    return (-1, )

                if (repo_url, b) not in map_module_depend:
                    map_module_depend[(repo_url, b)] = []
                for d in dep_repo_module:
                    if (sub_repo_dir, b) not in map_module_depend:
                        map_module_depend[(rela_repo_dir, b)] = []
                    map_module_depend[(rela_repo_dir, b)].append((sub_module_repo_dir, d))
        if module_root.__contains__(LEAK):
            if not isinstance(module_root[LEAK], list):
                print("module : ", b, ", illegal LEAK, not list")
                return -1
            leak_list = module_root[LEAK]
            for l in leak_list:
                if not isinstance(l, str):
                    print("module : ", b, ", illegal LEAK, not str")
                    return -1
                if not yaml_root.__contains__(l):
                    print("module : ", b, ", no such local depend ", l)
                    return -1
                if (repo_url, b) not in map_module_depend:
                    map_module_depend[(repo_url, b)] = []
                map_module_depend[(rela_repo_dir, b)].append((rela_repo_dir, l))
            (ret, sub_module_repo_dir) = sub_module(repo_url, repo_branch, leak_list)
            if ret != 0:
                print("fail to call submodule")
                return -1
        depend_repos = [] 
        if (rela_repo_dir, b) in map_module_depend:
            depend_repos = map_module_depend[(rela_repo_dir, b)]
        if (rela_repo_dir, b) not in list_build_done:
            build_module(b, src_list, workspace, copt, tar_type, rela_repo_dir, inc, link, depend_repos, hdr_list)
        if len(stack_sub_module) >= 1:
            stack_sub_module.pop()
        list_recurse_sub_module.append((repo_url, b))
    return (0, rela_repo_dir)

#############################################################################################################
if __name__ == "__main__":
    
    # read local yaml
    build_config_path = "./BUILD.yaml"
    if not os.path.isfile(build_config_path):
        print(build_config_path, " not exsit")
        sys.exit() 
    with open(build_config_path) as file:
        file_stream = file.read()
    yaml_root = yaml.load(file_stream, yaml.FullLoader)

    build_list=[]
    if len(sys.argv) != 0:
        build_list = sys.argv[1:]

    # start
    repo_url_cmd = "git remote -v | grep fetch | awk -F \" \" \'{print $2}\'"
    repo_url_fd = os.popen(repo_url_cmd)
    repo_url = repo_url_fd.read().replace('\n', '').strip()
    cmd_ret = repo_url_fd.close()
    if cmd_ret != None:
        print("fail to call cmd : ", repo_url_cmd)
        sys.exit()
    repo_url = repo_url.replace('\n', '')
    
    repo_branch_cmd = "git symbolic-ref --short -q HEAD"
    repo_branch_fd = os.popen(repo_branch_cmd)
    repo_branch = repo_branch_fd.read()
    cmd_ret = repo_branch_fd.close()
    if cmd_ret != None:
        print("fail to call cmd : ", repo_branch_cmd)
        sys.exit()
    repo_branch = repo_branch.replace('\n', '').strip()
    sub_module(repo_url, repo_branch, build_list)
