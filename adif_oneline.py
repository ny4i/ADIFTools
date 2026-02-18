#!/usr/bin/env python3
"""Convert N3FJP-style ADIF (one field per line) to one record per line."""

import sys
import re


def convert(infile, outfile):
    in_header = True
    record_fields = []

    for line in infile:
        line = line.rstrip("\r\n")

        if in_header:
            outfile.write(line + "\n")
            if re.match(r"<EOH>", line, re.IGNORECASE):
                in_header = False
            continue

        stripped = line.strip()
        if not stripped:
            if record_fields:
                outfile.write(" ".join(record_fields) + "\n")
                record_fields = []
            continue

        record_fields.append(stripped)
        if re.match(r"<eor>", stripped, re.IGNORECASE):
            outfile.write(" ".join(record_fields) + "\n")
            record_fields = []

    # flush any trailing record without a blank line after it
    if record_fields:
        outfile.write(" ".join(record_fields) + "\n")


HELP_TEXT = """\
adif_oneline.py - Convert multi-line ADIF to one record per line

Converts ADIF files where each field is on its own line (as exported by
N3FJP and other loggers) into one-record-per-line format. The file header
is preserved as-is. Each QSO record is joined into a single line ending
with <eor>.

Usage:
    adif_oneline.py <input.adi> [output.adi]

Arguments:
    input.adi       Input ADIF file (one field per line)
    output.adi      Output file (optional, defaults to stdout)

Options:
    --help, -h      Show this help message

Examples:
    adif_oneline.py n3fjp.adi
    adif_oneline.py n3fjp.adi output.adi
    adif_oneline.py n3fjp.adi | adif_fields.py /dev/stdin --add-OPERATOR KN2D
"""


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("--help", "-h"):
        print(HELP_TEXT)
        sys.exit(0)

    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <input.adi> [output.adi]", file=sys.stderr)
        print(f"Try '{sys.argv[0]} --help' for more information.", file=sys.stderr)
        sys.exit(1)

    inpath = sys.argv[1]
    outpath = sys.argv[2] if len(sys.argv) > 2 else None

    with open(inpath, "r") as f:
        if outpath:
            with open(outpath, "w") as out:
                convert(f, out)
        else:
            convert(f, sys.stdout)


if __name__ == "__main__":
    main()
