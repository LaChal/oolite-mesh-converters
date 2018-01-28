#!/bin/bash
#
# test_dat2obj.sh
#
# Script to test dat2obj.py
#

VIRTUALENV_URL="https://github.com/pypa/virtualenv/archive/15.1.0.tar.gz"
VENV_EXECUTABLE=".venv/bin/python"
OOLITE_MODELS_DIR="$HOME/GNUstep/Applications/Oolite/oolite.app/Resources/Models"
OOLITE_TEXTURES_DIR="$HOME/GNUstep/Applications/Oolite/oolite.app/Resources/Textures"
OOLITE_PLIST_FILE="$HOME/GNUstep/Applications/Oolite/oolite.app/Resources/Config/shipdata.plist"
OUTPUT_LEFT="output_l"
OUTPUT_RIGHT="output_r"
INPUT_DAT_FILES="dat_files"

CLEANUP=true

# Some files are ill-formed, and can't be parsed.
# They also may not work in game.
IGNORE="alloy.dat
buoy.dat
scarred_alloy.dat"

function install_virtualenv () {
    # Install Python virtual env if not yet installed in the current directory.
    if [ ! -d ".virtualenv" ]; then
        echo "Installing Python virtual environment for tests..."
        wget -q --no-check-certificate -O .virtenv-inst "$VIRTUALENV_URL"
        tar xvf .virtenv-inst
        mv virtualenv* .virtualenv
        python .virtualenv/virtualenv.py .venv --system-site-packages
        chmod 755 .venv/bin/activate
    fi
}

function activate_venv () {
    # Activate the Python virtual environment.
    source .venv/bin/activate
    echo "Activated Python virtual environment in:"
    echo "$VIRTUAL_ENV"
}

function install_openstep_parser () {
    # Install the .plits Python parser in the virtual environment.
    pip install openstep_parser
}

function build_oti () {
    # build_otis.py creates tex_files which contains indexed textures file got
    # from the .plist $PLIST_FILE file
    "$VENV_EXECUTABLE" build_otis.py "$1" "$2" "$3"
}

function find_files () {
    # Find file in a given place using a given regex.
    # Results contain only file names. Path is stripped out.
    where="$1"
    regex="$2"
    echo $(find "$where" -name "$regex" -printf '%f\n')
}

function copy_files () {
    # Copy files with a given extension from a given place to another given one.
    # First argument is an expression like '*.foo'.
    # Second argument is the source directory.
    # Third argument is the destination directory.
    # Fourth argument is a 'catalog' file to write copied file names to.
    # Fifth argument is a list of file names to not copy.
    expr="$1"
    src="$2"
    dest="$3"
    catalog="$4"
    skip="$5"
    if [ -f "$catalog" ]; then
        rm "$catalog"
    fi
    for name in $(find_files "$src" "${expr}"); do
        if [ -z "$(echo "$skip" | grep "$name")" ]; then
            cp "$src/$name" "$dest/$name"
            if [ -n "$catalog" ]; then
                echo "$name" >> "$catalog"
            fi
        fi
    done
}

function diff_files () {
    # Find differences between .dat file in to given places.
    # If differences are found, output is saved into the directory given as 
    # third argument. This directory is created if nonexistent.
    # The fourth argument is a 'regex' like '*.foo'.
    left="$1"
    right="$2"
    output="$3"
    regex="$4"
    # Use arrays to store file names.
    # List files names only!
    # Paths will be rebuilt later :)
    declare -a left_names=( $(find_files "$left" "$regex") )
    # Use a positional array for $right_names to speed to avoid a double loop.
    declare -a rns=( $(find_files "$right" "$regex") )
    declare -A right_names
    for n in "${rns[@]}"; do
        right_names["$n"]=$n
    done
    echo "* Comparing ${#left_names[@]} '$regex' files."
    # Store the number of different files in 'status'
    status=0
    ext=$(echo $regex | awk -F. '{print $NF}')
    for name in ${left_names[@]}; do
        if [[ "${right_names[@]}" =~ "$name" ]]; then
            echo -n "  * '$name' ('$left' | '$right')"
            delta="$(diff "$left/$name" "$right/$name")"
            # If there are differences between the files, store them in a
            # '.diff' file into '$output' and increase '$status' by one.
            r=" OK"
            if [ -n "$delta" ]; then
                if [ ! -d "$output" ]; then
                    mkdir -p "$output"
                fi
                echo "$delta" > "$output/$(echo $name | sed "s/\.${ext}/.diff/g")"
                status=$(( $status + 1 ))
                r=" FAILED"
            fi
            echo "$r"
        fi
    done
    return $status
}

function convert_dat () {
    # Converts .dat files into .obj (and subsequent .mtl) ones.
    # The argument is a directory.
    dire="$1"
    status=0
    for name in $(find_files "$dire" "*.dat"); do
        "$VENV_EXECUTABLE" ../dat2obj.py "$dire/$name"
        status=$(( $status + $? ))
    done
    return $status
}

function convert_obj () {
    # Converts .obj files to .dat ones.
    # The argument is a directory.
    dire="$1"
    status=0
    for name in $(find_files "$dire" "*.obj"); do
        prog='../Obj2DatTex.py'
        if [ -n "$(grep '^vn ' $dire/$name)" ];then
            prog='../Obj2DatTexNorm.py'
        fi
        echo "Calling $prog $dire/$name"
        "$VENV_EXECUTABLE" "$prog" "$dire/$name"
        status=$(( $status + $? ))
    done
    return $status
}

if [ "$1" == "--no-cleanup" ]; then
    CLEANUP=false
fi

# Main process.
if [ ! -d "$OUTPUT_LEFT" ]; then
    mkdir -p "$OUTPUT_LEFT"
fi

if [ ! -d "$OUTPUT_RIGHT" ]; then
    mkdir -p "$OUTPUT_RIGHT"
fi

install_virtualenv

activate_venv

install_openstep_parser

copy_files "oolite*.dat" "$OOLITE_MODELS_DIR" "$OUTPUT_LEFT" "$INPUT_DAT_FILES" "$IGNORE"

build_oti "$OOLITE_PLIST_FILE" "$OOLITE_MODELS_DIR" "$OUTPUT_LEFT"

# copy_files ".png" "$OOLITE_TEXTURES_DIR" "$OUTPUT" "" # Valid only if we can
#     # test the .obj files in a 3D editor...

convert_dat "$OUTPUT_LEFT"
result="$?"
first_pass="$result"
if [ "$result" -gt "0" ]; then
    echo "First conversion to .obj failed for $result files!"
    read -p "Press ENTER" -t 60 $foo
fi

# The obj to dat converter can't produce expected result for now...
convert_obj "$OUTPUT_LEFT"
result="$?"
# echo $result
if [ "$result" -gt "0" ]; then
    echo "Conversion to .dat failed for $result files!"
    read -p "Press ENTER" -t 60 $foo
fi

# Copy the new generated .dat files to the other output directory
copy_files "oolite*.dat" "$OUTPUT_LEFT" "$OUTPUT_RIGHT" "$INPUT_DAT_FILES" "$IGNORE"
copy_files "*.oti" "$OUTPUT_LEFT" "$OUTPUT_RIGHT"

# Convert the new .dat files
convert_dat "$OUTPUT_RIGHT"
result="$?"
second_pass="$result"
if [ "$result" -gt "0" ]; then
    echo "Second conversion to .obj failed for $result files!"
    read -p "Press ENTER" -t 60 $foo
fi

if [ "$first_pass" -ne "$second_pass" ]; then
    echo "Second dat2obj pass did not gave the same converted file number:"
    echo "First: $first_pass, second: $second_pass."
fi

# Compare re-converted .obj files whit first ones.
diff_files "$OUTPUT_LEFT" "$OUTPUT_RIGHT" "cmp_output" "*.obj"
result="$?"

if [ "$result" -gt "0" ]; then
    echo "Comparison did not pass for $result .obj files."
    echo "See '.diff' file in '$output'."
    echo "Test failed!"
    exit $result
else
    echo "Tests successful!"
fi

# Consider to change this, because a virtualenv may be already installed for the
# tested application.
if [ "$CLEANUP" == true ]; then
    rm -rf .v*
fi

#exit $result

