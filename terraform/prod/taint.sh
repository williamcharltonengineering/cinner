#!/usr/bin/env bash
# set -u

if [[ "${1}" == "" ]]; then
    echo "provide resource to taint (e.g. null_resource.install_nginx_certificate)"
    exit 1
fi

source .tf-deploy-env

print_vars_obfuscated () {
    set -u
    echo "AWS_PROFILE=$AWS_PROFILE"
    echo "TF_VAR_namecheap_api_key=${TF_VAR_namecheap_api_key:0:${#TF_VAR_namecheap_api_key}-28}..."
    echo "LINODE_TOKEN=${LINODE_TOKEN:0:${#LINODE_TOKEN}-16}..."
    set +u
}

if [[ -z $AWS_PROFILE || -z $TF_VAR_namecheap_api_key || -z $LINODE_TOKEN ]]; then
    echo "You must provide all necessary deployment variables and secrets"
    echo "recommendation: you can provide them in the command, but you can also define them in the git-ignored file .tf-deploy-env"
    print_vars_obfuscated
fi

print_vars_obfuscated

export AWS_PROFILE
export TF_VAR_namecheap_api_key
export TF_VAR_namecheap_api_user
export LINODE_TOKEN
# export TF_LOG=DEBUG

terraform taint ${1}
