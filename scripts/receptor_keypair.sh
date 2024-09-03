#!/bin/bash

EXPIRATION_AFTER_YEARS=5

RECEPTOR_HOSTNAME=""
RECEPTOR_ADDITIONAL_HOSTNAME=""
RECEPTOR_IP_ADDRESS=""

# Display help message
function display_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -n  [REQUIRED]  Set the hostname."
    echo "  -na [OPTIONAL]  Set the additional hostname."
    echo "  -ni [OPTIONAL]  Set ip address."
    echo "  -h              Display this help message."
    echo ""
    echo "Example:"
    echo "  $0 -n receptor1.domain.ltd -na receptor1-ext.domain.ltd -ni 10.0.0.2"
    echo ""
    exit 0
}

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -n) RECEPTOR_HOSTNAME="$2"; shift ;;
        -na) RECEPTOR_ADDITIONAL_HOSTNAME="$2"; shift ;;
        -ni) RECEPTOR_IP_ADDRESS="$2"; shift ;;
        -h) display_help ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Check if -n flag was provided
if [[ -z "$RECEPTOR_HOSTNAME" ]]; then
    echo "Error: -n is required."
    echo "Run '$0 -h' for more information."
    exit 1
fi

# List of possible extensions
EXTENSIONS=("req" "key" "crt")

# Loop through each extension and check if the file exists
for ext in "${EXTENSIONS[@]}"; do
    file="${RECEPTOR_HOSTNAME}.${ext}"
    if [[ -e "$file" ]]; then
        echo "File '$file' exists."
        exit 1
    fi
done

# Detect the OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux system
    ISSE_DATE=$(date --iso-8601=seconds --utc)
    EXPIRATION_DATE=$(date --iso-8601=seconds --utc --date "${EXPIRATION_AFTER_YEARS} years")
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS system
    ISSE_DATE=$(date -u +"%Y-%m-%dT%H:%M:%S+00:00")
    EXPIRATION_DATE=$(date -u -v+${EXPIRATION_AFTER_YEARS}y +"%Y-%m-%dT%H:%M:%S+00:00")
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

# Initialize an empty string for the Docker arguments
DOCKER_ARGS=""

# Append arguments only if they are provided
if [[ -n "$RECEPTOR_HOSTNAME" ]]; then
    DOCKER_ARGS+="commonname=$RECEPTOR_HOSTNAME dnsname=$RECEPTOR_HOSTNAME nodeid=$RECEPTOR_HOSTNAME "
fi
if [[ -n "$RECEPTOR_ADDITIONAL_HOSTNAME" ]]; then
    DOCKER_ARGS+="dnsname=$RECEPTOR_ADDITIONAL_HOSTNAME "
fi
if [[ -n "$RECEPTOR_IP_ADDRESS" ]]; then
    DOCKER_ARGS+="ipaddress=$RECEPTOR_IP_ADDRESS "
fi

echo "Generating a key pair for receptor ${RECEPTOR_HOSTNAME}"

docker run --rm -v $PWD:/tmp quay.io/ansible/receptor:latest \
       receptor \
       --cert-makereq bits=2048 \
       $DOCKER_ARGS \
       outreq=/tmp/${RECEPTOR_HOSTNAME}.req \
       outkey=/tmp/${RECEPTOR_HOSTNAME}.key

docker run --rm -v $PWD:/tmp quay.io/ansible/receptor:latest \
       receptor \
       --cert-signreq req=/tmp/${RECEPTOR_HOSTNAME}.req \
       cacert=/tmp/awx_mesh_ca_crt \
       cakey=/tmp/awx_mesh_ca_key \
       notbefore=${ISSE_DATE} \
       notafter=${EXPIRATION_DATE} \
       outcert=/tmp/${RECEPTOR_HOSTNAME}.crt verify=yes

echo "Finished"
