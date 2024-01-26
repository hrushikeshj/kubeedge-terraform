#!/bin/bash
#
# RECHECK - interbal to check if filw was created
# bash /tail_all.sh /output.log /common.log /master.log /master_edgemesh.log
# bash /tail_all.sh /output.log /common.log /edge.log /edge_edgemesh.log

set -eo pipefail
file_try_again_time="5s"

if [[ -v RECHECK ]]; then
    echo "Recheck time: $RECHECK"
    file_try_again_time=$RECHECK
fi

ljust=$(echo $@ | sed 's/ /\n/g' | sort | uniq | awk '{print length}' | sort -nr | head -n 1)
ljust=$(($ljust))

YELLOW="$(printf '\033[33m')"
RED="$(printf '\033[0;31m')"
GREEN="$(printf '\033[0;32m')"
BLUE="$(printf '\033[0;34m')"
PURPLE="$(printf '\033[0;35m')"
CYAN="$(printf '\033[0;36m')"
WHITE="$(printf '\033[0;37m')"
COLOURS=($YELLOW $RED $GREEN $BLUE $PURPLE $CYAN)
NC="$(printf '\033[0m')"

pids=()
function kill_all(){
    for f in ${pids[@]}; do
        echo killing $f
        kill $f
    done
    exit 0
}
trap kill_all SIGINT

function tail_my(){
    file_prepend=$(printf "%-${ljust}s " $1)
    # escape /
    file_prepend=$(echo "$file_prepend" | sed 's/\//\\\//g')

    # consistent hasing for file color
    colour_idx=$(cksum <<< "$1" |  cut -f 1 -d ' ' )
    colour_idx=$(($colour_idx % ${#COLOURS[@]}))
    color=${COLOURS[colour_idx]}
    
    until [ -f  $1 ];
    do
        echo "$file_prepend: not found. Trying again in $file_try_again_time"
        sleep $file_try_again_time
    done

    tail -f $1 | sed "s/^/$color $file_prepend :$NC /"
}

for f in $@; do
    tail_my $f &
    pids+=($!)
done

#kill_all
while true; do
sleep 10s
done
