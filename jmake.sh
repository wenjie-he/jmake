#!/bin/bash
set -o errexit

PYTHON="python3"

repo_url=`git remote -v | grep fetch | awk -F " " '{print $2}'`
repo_branch=`git symbolic-ref --short -q HEAD`
jmake_path=`dirname $0`
build_done_list=()

############################# repo pull  ###############################
temp_repo_dir=""
function repo_pull {
    repo_url=$1
    branch=$2

    echo "repo_url : "$repo_url
    local_dir="/home/lianjin/codebase/"`echo $repo_url | awk -F ':' '{print $2}'| awk -F ".git" '{print $1}'`
    if [ ! -d $local_dir ];then
	git clone -b $branch $repo_url $local_dir
    else
	current_branch=`cd $local_dir && git symbolic-ref --short -q HEAD`
	if [ "$current_branch" != "$branch" ]; then
            branch_repo_dir=$local_dir"_"$branch
	    cd $local_dir && git fetch origin $branch:$branch
	    if [ ! -d $branch_repo_dir ];then
                git clone -b $branch $local_dir $branch_repo_dir
            fi
	    cd $branch_repo_dir && git fetch origin $branch
	    local_dir=$branch_repo_dir
	fi
    fi
    temp_repo_dir=local_dir
    return 0
}

############################## sub module  ###############################
temp_dep_type=""
function sub_module {
    repo=$1
    module=$2
	
    depend_list=`$PYTHON $jmake_path"/get_local_depend_list.py" $repo $module`
    echo "$depend_list" | while read d
    do
	if [ -z "$d" ]; then
            continue
	fi
	repo_dir=`echo $d | awk -F ' ' '{print $1}'`
	dep_module=`echo $d | awk -F ' ' '{print $2}'`
	sub_module $repo_dir $dep_module
    done

    depend_list=`$PYTHON $jmake_path"/get_repo_depend_list.py" $repo $module`
    echo "$depend_list" | while read d
    do
	if [ -z "$d" ]; then
	    continue
	fi
	repo_url=`echo $d | awk -F " " '{print $1}'`
	repo_dir=`echo $repo_url | awk -F ':' '{print $1}' | awk -F ".git" '{print $1}'`
	branch=`echo $d | awk -F " " '{print $2}'`
	dep_module=`echo $d | awk -F " " '{print $3}'`
	repo_pull "$repo_url" "$branch"
	
	sub_module $repo_dir $depend_module
    done

    # build module

    temp_dep_type=`$PYTHON $jmake_path"/get_module_type.py" $repo $module`
    return 0
}


#################################### main entry ########################################

module_list=()
if [ $# -eq 0 ]; then
    module_list=`$PYTHON $jmake_path"/get_all_module.py" ./`
else
    for param in "$*"; do
        module_list+=param
    done
fi
for m in ${module_list[@]}; do
    sub_module ./ $m
done
