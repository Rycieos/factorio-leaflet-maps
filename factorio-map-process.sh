#!/usr/bin/env bash
set -euo pipefail

## Defaults
SERVER_BASE_PATH=/srv/factorio/maps
MAP_TILES_PATH=images
FACTORIO_MAP_SCRIPT="$(dirname "${BASH_SOURCE[0]}")/factoriomap.py"
TARFILE=
REDUCE=0

function usage() {
    cat <<EOF
USAGE

factorio-map-process.sh [OPTIONS] tarfile

DESCRIPTION

This script will process a given tarfile into a set of images used in a leaflet map.
The default behavior will create a directory for the world maps if one does not exist and copy the example html page in as 'index.html'
The tar file will be parsed for a map name and a date, separated by underscores (_). Files should be of the format {WorldName}_YYYY-MM-DD.tar.

OPTIONS

    -t | --tiles <images>           Set the name of the directory to store the tile images in.  Default value is
                                    'images'

    -s | --server <server path>     Set the base path where the http server files will be stored.  Default value is
                                    '/srv/factorio/maps'

    -r                              Flag to size-reduce the images folder with the rdfind tool
EOF
}

function testRequirements() {
    if ! command -v jq >/dev/null; then
        echo "ERROR: Requirement not satisfied - jq -" >&2
        exit 1
    fi

    if [[ $REDUCE -eq 1 ]] && ! command -v rdfind >/dev/null; then
        echo "ERROR: Requirement not satisfied - rdfind -" >&2
        exit 1
    fi

}

function parseFileName() {
    printf 'Target File: "%s"\n' "$FILENAME"

    local file_name=${FILENAME%.*}

    date_string=${file_name##*_}
    printf 'Date String: "%s"\n' "$date_string"

    local world_name=${file_name%_*}

    if [[ $date_string != $world_name ]]; then
        printf 'World Name: "%s"\n' "$world_name"
        SERVER_BASE_PATH="${SERVER_BASE_PATH}/${world_name}"
    fi

    DESTPATH="${SERVER_BASE_PATH}/${MAP_TILES_PATH}/${date_string}/"
}

function createNewWorld() {
    ## Test for existing world folder
    if [[ ! -d ${SERVER_BASE_PATH}/${MAP_TILES_PATH} ]]; then
        ## Create New world folder
        mkdir -p "${SERVER_BASE_PATH}/${MAP_TILES_PATH}"
        cp example.html "${SERVER_BASE_PATH}/index.html"
    fi
}

function processTiles() {
    printf 'Destination: "%s"\n' "$DESTPATH"
    mkdir "$DESTPATH"
    "$FACTORIO_MAP_SCRIPT" "$TARFILE" "$DESTPATH"

    if [[ $REDUCE -eq 1 ]]; then
        rdfind -makehardlinks true "${SERVER_BASE_PATH}/${MAP_TILES_PATH}"
    fi
}

function addDatesJSON() {
    local date_file="${SERVER_BASE_PATH}/dates.json"

    if [[ -f $date_file ]]; then
        local temp_file="$(mktemp)"
        jq ". += [\"${date_string}\"]" "$date_file" > "$temp_file" && cat "$temp_file" > "$date_file"
        rm "${temp_file}"
    else
        jq '.' <<< "[\"${date_string}\"]" > "$date_file"
    fi
}

function main() {
    testRequirements

    parseFileName

    createNewWorld

    processTiles

    addDatesJSON

    echo "Success"
    exit 0
}


while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            # Print Usage
            usage
            exit 0
            ;;
        -r)
            REDUCE=1
            shift
            ;;
        -t|--tiles)
            MAP_TILES_PATH="${2%/}"
            printf 'Using MAP Path: "%s"\n' "$MAP_TILES_PATH"
            shift 2
            ;;
        -s|--server)
            SERVER_BASE_PATH="${2%/}"
            printf 'Using Server Path: "%s"\n' "$SERVER_BASE_PATH"
            shift 2
            ;;
        *)
            TARFILE=$1
            printf 'Tarfile: "%s"\n' "$TARFILE"
            if ! tar tf "$TARFILE" >/dev/null 2>&1; then
                echo "ERROR: File is not a tar archive" >&2
                usage
                exit 2
            fi
            FILENAME=$(basename "$TARFILE")
            shift
            ;;
    esac
done

main
