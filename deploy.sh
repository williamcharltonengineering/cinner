#!/usr/bin/env bash

fatal () {
    echo -e "\e[31m${1}\e[0m"
    exit 1
}

info () {
    echo -e "\e[38;5;214m${1}\e[0m"
}

valid_envs=("prod")
valid_envs_joined=$(printf "|%s" "${valid_envs[@]}")
valid_envs_joined=${valid_envs_joined:1} # Remove the leading "|"
HELP="usage: $0 <ENVIRONMENT> <ACTION>

Required arguments:
 ☐ ENVIRONMENT:                <${valid_envs_joined}>
 ☐ ACTION:                     <deploy|destroy>
"
ORIGINAL_ARGS="$0 $*"
set -e
elementInArray() {
    local element
    for element in "${@:2}"; do
        [[ "$element" == "$1" ]] && return 0
    done
    return 1
}
if [[ -z "$1" ]] || ! elementInArray "$1" "${valid_envs[@]}"
then
    info "Valid values are:"
    for element in "${valid_envs[@]}"; do
        info " - $element"
    done
    fatal "Error: deployment environment '${1}' is invalid."
fi
if [[ "$1" == "" ]] || [[ "$2" == "" ]]
then
    info "$HELP"
    fatal "Must provide both env and cluster direction as args one and two (e.g. $0 staging up)"
fi
export ENVIRONMENT=$1
export ACTION=$2
shift # respect first positional arg as deployment environment
shift # respect second positional arg as cluster direction

AWS_PROFILE=wce

if [[ "$ACTION" == "plan" ]]; then
    cd ./terraform/${ENVIRONMENT}
    ./init.sh
    ./plan.sh
fi

if [[ "$ACTION" == "apply" ]]; then
    cd ./terraform/${ENVIRONMENT}
    ./deploy.sh
fi

if [[ "$ACTION" == "taint" ]]; then
    cd ./terraform/${ENVIRONMENT}
    ./taint.sh ${1}
fi

if [[ "$ACTION" == "destroy" ]]; then
    cd ./terraform/${ENVIRONMENT}
    ./destroy.sh
fi
