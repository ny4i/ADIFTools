#!/usr/bin/env python3
"""Add fields to every record in an ADIF file.

Usage:
    adif_addfields.py input.adi --add-operator KN2D --add-my_gridsquare EL87
    adif_addfields.py input.adi --output-file out.adi --add-operator KN2D --override
"""

import sys
import re


def parse_args(argv):
    input_file = None
    output_file = None
    override = False
    fields = {}

    i = 1
    while i < len(argv):
        arg = argv[i]
        if arg == "--output-file" and i + 1 < len(argv):
            output_file = argv[i + 1]
            i += 2
        elif arg == "--override":
            override = True
            i += 1
        elif arg.startswith("--add-") and i + 1 < len(argv):
            field_name = arg[6:]  # strip --add-
            fields[field_name] = argv[i + 1]
            i += 2
        elif not arg.startswith("-") and input_file is None:
            input_file = arg
            i += 1
        else:
            print(f"Unknown argument: {arg}", file=sys.stderr)
            sys.exit(1)

    if not input_file:
        print(
            f"Usage: {argv[0]} <input.adi> [--output-file out.adi] "
            f"--add-<field> <value> [--override]",
            file=sys.stderr,
        )
        sys.exit(1)

    if not fields:
        print("No --add-<field> arguments provided.", file=sys.stderr)
        sys.exit(1)

    return input_file, output_file, fields, override


def format_field(name, value):
    return f"<{name}:{len(value)}>{value}"


def process(content, fields, override):
    # Split header from body at <EOH>
    eoh_match = re.search(r"<EOH>\s*\n?", content, re.IGNORECASE)
    if eoh_match:
        header = content[: eoh_match.end()]
        body = content[eoh_match.end() :]
    else:
        header = ""
        body = content

    # Process each record in the body
    result = header
    pos = 0
    record_num = 0

    for eor_match in re.finditer(r"<eor>", body, re.IGNORECASE):
        record_num += 1
        record_text = body[pos : eor_match.start()]
        eor_tag = eor_match.group()

        for field_name, field_value in fields.items():
            pattern = re.compile(
                rf"<{re.escape(field_name)}:\d+>[^\s<]*",
                re.IGNORECASE,
            )
            existing = pattern.search(record_text)

            if existing:
                if not override:
                    print(
                        f"Error: Record {record_num} already has field "
                        f"<{field_name}>. Use --override to replace.",
                        file=sys.stderr,
                    )
                    sys.exit(1)
                record_text = pattern.sub(
                    format_field(field_name, field_value),
                    record_text,
                    count=1,
                )
            else:
                # Insert before <eor>: detect format (one-per-line vs inline)
                if record_text.rstrip().endswith("\n") or "\n" in record_text.strip():
                    record_text = record_text.rstrip() + "\n" + format_field(field_name, field_value) + "\n"
                else:
                    record_text = record_text + format_field(field_name, field_value) + " "

        result += record_text + eor_tag
        # Preserve any whitespace/newlines after <eor>
        after_eor_end = eor_match.end()
        pos = after_eor_end

    # Append any trailing content after the last <eor>
    result += body[pos:]
    return result


def main():
    input_file, output_file, fields, override = parse_args(sys.argv)

    with open(input_file, "r") as f:
        content = f.read()

    output = process(content, fields, override)

    if output_file:
        with open(output_file, "w") as f:
            f.write(output)
    else:
        sys.stdout.write(output)


if __name__ == "__main__":
    main()
