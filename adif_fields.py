#!/usr/bin/env python3
"""Add or delete fields in every record of an ADIF file.

Usage:
    adif_fields.py input.adi --add-operator KN2D --add-my_gridsquare EL87
    adif_fields.py input.adi --add-operator KN2D --override
    adif_fields.py input.adi --delete-N3FJP*
    adif_fields.py input.adi --delete-APP* --add-operator KN2D --output-file out.adi

Delete patterns support * as a wildcard (e.g. --delete-N3FJP* removes all
N3FJP_COMPUTERNAME, N3FJP_StationID, etc.).
"""

import sys
import re
import fnmatch


def parse_args(argv):
    input_file = None
    output_file = None
    override = False
    add_fields = {}
    delete_patterns = []

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
            add_fields[field_name] = argv[i + 1]
            i += 2
        elif arg.startswith("--delete-"):
            pattern = arg[9:]  # strip --delete-
            delete_patterns.append(pattern)
            i += 1
        elif not arg.startswith("-") and input_file is None:
            input_file = arg
            i += 1
        else:
            print(f"Unknown argument: {arg}", file=sys.stderr)
            sys.exit(1)

    if not input_file:
        print(
            f"Usage: {argv[0]} <input.adi> [--output-file out.adi] "
            f"[--add-<field> <value>] [--delete-<pattern>] [--override]",
            file=sys.stderr,
        )
        sys.exit(1)

    if not add_fields and not delete_patterns:
        print("No --add or --delete arguments provided.", file=sys.stderr)
        sys.exit(1)

    return input_file, output_file, add_fields, delete_patterns, override


def format_field(name, value):
    return f"<{name}:{len(value)}>{value}"


def matches_any_pattern(field_name, patterns):
    """Check if field_name matches any of the glob patterns (case-insensitive)."""
    for pattern in patterns:
        if fnmatch.fnmatch(field_name.upper(), pattern.upper()):
            return True
    return False


def delete_fields(record_text, patterns):
    """Remove all ADIF fields matching any of the glob patterns."""
    # Match a field tag + value + optional trailing whitespace
    def replacer(m):
        field_name = m.group(1)
        if matches_any_pattern(field_name, patterns):
            return ""
        return m.group(0)

    return re.sub(r"<([A-Za-z_][A-Za-z0-9_]*):\d+>[^\s<]*\s?", replacer, record_text)


def add_fields(record_text, fields, override, record_num):
    """Add or replace fields in a record."""
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

    return record_text


def process(content, add_flds, del_patterns, override):
    # Split header from body at <EOH>
    eoh_match = re.search(r"<EOH>\s*\n?", content, re.IGNORECASE)
    if eoh_match:
        header = content[: eoh_match.end()]
        body = content[eoh_match.end() :]
    else:
        header = ""
        body = content

    result = header
    pos = 0
    record_num = 0

    for eor_match in re.finditer(r"<eor>", body, re.IGNORECASE):
        record_num += 1
        record_text = body[pos : eor_match.start()]
        eor_tag = eor_match.group()

        # Deletes first, then adds
        if del_patterns:
            record_text = delete_fields(record_text, del_patterns)

        if add_flds:
            record_text = add_fields(record_text, add_flds, override, record_num)

        result += record_text + eor_tag
        pos = eor_match.end()

    # Append any trailing content after the last <eor>
    result += body[pos:]
    return result


def main():
    input_file, output_file, add_flds, del_patterns, override = parse_args(sys.argv)

    with open(input_file, "r") as f:
        content = f.read()

    output = process(content, add_flds, del_patterns, override)

    if output_file:
        with open(output_file, "w") as f:
            f.write(output)
    else:
        sys.stdout.write(output)


if __name__ == "__main__":
    main()
