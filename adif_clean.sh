#!/bin/bash
# adif_clean.sh - Process all .adi files in a directory
#
# Converts each file to one-record-per-line and removes APP* and N3FJP*
# fields. Cleaned files are written to an output directory.
#
# Usage:
#   adif_clean.sh <input_dir> <output_dir>
#   adif_clean.sh .            ./cleaned

# Directory containing the Python ADIF scripts
TOOLS_DIR=~/projects/ADIFTools

if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "adif_clean.sh - Batch clean ADIF files"
    echo ""
    echo "Converts all .adi files in a directory to one-record-per-line"
    echo "format and removes APP* and N3FJP* fields."
    echo ""
    echo "Usage:"
    echo "    adif_clean.sh <input_dir> <output_dir>"
    echo ""
    echo "Arguments:"
    echo "    input_dir     Directory containing .adi files"
    echo "    output_dir    Directory for cleaned output (created if needed)"
    exit 0
fi

if [ $# -ne 2 ]; then
    echo "Usage: adif_clean.sh <input_dir> <output_dir>" >&2
    echo "Try 'adif_clean.sh --help' for more information." >&2
    exit 1
fi

INPUT_DIR="$1"
OUTPUT_DIR="$2"

if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory '$INPUT_DIR' does not exist." >&2
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

count=0
errors=0

for f in "$INPUT_DIR"/*.adi; do
    [ -f "$f" ] || continue
    basename="$(basename "$f")"
    echo "Processing: $basename"

    if python3 "$TOOLS_DIR/adif_oneline.py" "$f" \
        | python3 "$TOOLS_DIR/adif_fields.py" /dev/stdin \
            --delete-APP% --delete-N3FJP% --delete-Comment \
            --output-file "$OUTPUT_DIR/$basename"; then
        count=$((count + 1))
    else
        echo "  ERROR processing $basename" >&2
        errors=$((errors + 1))
    fi
done

if [ $count -eq 0 ] && [ $errors -eq 0 ]; then
    echo "No .adi files found in '$INPUT_DIR'." >&2
    exit 1
fi

echo ""
echo "Done. $count file(s) cleaned, $errors error(s)."
echo "Output: $OUTPUT_DIR"
