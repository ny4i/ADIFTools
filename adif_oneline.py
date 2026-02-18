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


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <input.adi> [output.adi]", file=sys.stderr)
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
