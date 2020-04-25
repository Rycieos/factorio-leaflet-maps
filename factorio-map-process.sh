#!/usr/bin/env bash

## Defaults
SERVER_BASE_PATH=/srv/factorio/maps
MAP_TILES_PATH=images
FACTORIO_MAP_SCRIPT="$(dirname "${BASH_SOURCE[0]}")/factoriomap.py"
TARFILE=
REDUCE=0

function usage() {
    cat <<-EOF
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
	if ! [ -x "$(command -v jq)" ]; then
		echo "ERROR: Requirement not satisfied - jq -"
		exit 1
	fi

	if ! [ -x "$(command -v python3)" ]; then
		echo "ERROR: Requirement not satisfied - python3 -"
		exit 1
	fi

        if [[ REDUCE -eq 1 && !(-x "$(command -v rdfind)") ]]; then
		echo "ERROR: Requirement not satisfied - rdfind -"
		exit 1
	fi

}

function parseFileName() {
	NAME_NOEXT="${FILENAME%.*}"
	echo "Target File: $NAME_NOEXT"

	infos=($(awk -F'[_.]' '{print $1; print $2}' <<< $NAME_NOEXT))

	WORLDNAME=${infos[0]}
	echo "WORLD NAME $WORLDNAME"

	DATESTR=${infos[1]}
	echo "DATE STRING $DATESTR"
	DESTPATH=$SERVER_BASE_PATH/$WORLDNAME/$MAP_TILES_PATH/$DATESTR/
}

function createNewWorld() {
    ## Test for existing world folder
    if [[ ! -d $SERVER_BASE_PATH/$WORLDNAME ]]; then
        ## Create New world folder
        mkdir -p $SERVER_BASE_PATH/$WORLDNAME/$MAP_TILES_PATH
        cp example.html $SERVER_BASE_PATH/$WORLDNAME/index.html
    fi
}

function processTiles() {
    echo "DESTINATION $DESTPATH"
    mkdir $DESTPATH
    python3 $FACTORIO_MAP_SCRIPT $TARFILE $DESTPATH

    if [ $REDUCE -eq 1 ]; then
        rdfind -makehardlinks true $SERVER_BASE_PATH/$WORLDNAME/$MAP_TILES_PATH
    fi
}

function addDatesJSON() {
    DATEFILE=$SERVER_BASE_PATH/$WORLDNAME/dates.json
    if [[ -f $DATEFILE ]]; then
        TMPFILE=$(mktemp)
        jq --arg date "$DATESTR" '. |= .+ [$date]' $DATEFILE > "$TMPFILE" && cat $TMPFILE > $DATEFILE
        rm $TMPFILE
    else
        echo -e '[\n    "'$DATESTR'" \n]' >> $DATEFILE
    fi

}

function main() {
    testRequirements;

    parseFileName;

    createNewWorld;

    processTiles;

    addDatesJSON;

    echo "Success"
    exit 0
}


while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            # Print Usage
            usage;
            exit 0
            ;;
        -r)
            REDUCE=1
            shift
            ;;
        -t|--tiles)
            MAP_TILES_PATH="$2"
            echo "Using MAP Path $MAP_TILES_PATH"
            shift
            shift
            ;;
        -s|--server)
            SERVER_BASE_PATH="$2"
            echo "Using Server Path $SERVER_BASE_PATH"
            shift 2
            ;;
        *)
            TARFILE=$1
            echo "TARFILE $TARFILE"
            if  ! { tar tf "$TARFILE"; } >/dev/null 2>&1;; then
	            echo "ERROR: File is not a tar archive```
                usage;
	            exit 0
            fi
            FILENAME=$(basename "$TARFILE")
            shift
            ;;
    esac    
done

main;
