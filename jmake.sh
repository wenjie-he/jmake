#!/bin/bash
set -o errexit

CXX="g++"
ARC="ar"
TEMP="/home/lianjin/BUILD_TEMP/"
OUTPUT="/home/lianjin/BUILD_OUTPUT/"

PYTHON="python3"

repo_url=`git remote -v | grep fetch | awk -F " " '{print $2}'`
repo_branch=`git symbolic-ref --short -q HEAD`
jmake_path=`dirname $0`
build_done_list=()

############################### build single module #################################
REPO=""
MODULE=""
TYPE=""
WORKSPACE=""
SRCS=""
COPT=""
DEFINE=""
HDRS=""
INC=""
LINK=""

function build_module {
    THIS_TEMP=$TEMP$REPO
    THIS_OUTPUT=$OUTPUT$REPO
 
    res_change=false
    object_list=""
    for s in ${SRCS[@]}; do
        src=$WORKSPACE$s
        object_file=${THIS_TEMP}${src}".o"
        object_list+=" "$object_file
        depend_file=${THIS_TEMP}${src}".d"
        if [ ! -f ${object_file} ]; then
    	    res_change=true
    	    $CXX -o ${object_file} -c ${src} $COPT $INC
        else
    	    if [ ! -f $depend_file ]; then
                $CXX -MM ${src} $INC > $depend_file
	    else
	        depend_file_time=`stat -c %Y ${depend_file}`
	        # depend file exsit, whever we should rebuild it
	        headers=`awk -F ":" '{print $2}' $depend_file | sed 's/\\\\/ /g'`
	        depend_file_change=false
	        for h in ${headers[@]}; do
	            if [ ! -f $h ]; then
		        depend_file_change=true
		        break
		    fi
		    header_file_time=`stat -c %Y $h`
		    if [ $header_file_time -gt $depend_file_time ]; then
		        depend_file_change=true
		        break
		    fi
		done
	    	if [ $depend_file_change = true ]; then
	            $CXX -MM ${src} $INC > $depend_file
	    	fi
	    fi
    	    headers=`awk -F ":" '{print $2}' $depend_file | sed 's/\\\\/ /g'`
	    object_file_change=false
	    object_file_time=`stat -c %Y ${object_file}`
	    for h in ${headers[@]}; do
 		header_file_time=`stat -c %Y $h`
                if [ $header_file_time -gt $object_file_time ]; then
                    $CXX -o ${object_file} -c ${src} $COPT $INC
	            res_change=true
	        fi
            done
	fi
    done

    if [ $res_change ]; then
    	if [ $TYPE = "static" ]; then
	    $ARC -r $THIS_OUTPUT"lib/""lib"$MODULE".a" $object_list $LINK
    	elif [ $TYPE = "shared" ]; then
            $CXX -shared -o $THIS_OUTPUT"lib/""lib"$MODULE".so" $object_list $COPT $LINK
        else
            $CXX -o $THIS_OUTPUT"bin/"$MODULE $object_list $COPT $LINK
        fi
    fi

    for h in ${HDRS[@]}; do
        cp $WORKSPACE$h $THIS_OUTPUT"include/"
    done
    return 0
}
############################# repo pull  ###############################
temp_repo_dir=""
function repo_pull {
    repo_url=$1
    branch=$2

    local_dir="/home/lianjin/codebase/"`echo $repo_url | awk -F ':' '{print $2}'| awk -F ".git" '{print $1}'`"/"
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
    temp_repo_dir=$local_dir
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
	
	sub_module $temp_repo_dir $dep_module
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
