#!/usr/bin/env python3
"""Add or delete fields in every record of an ADIF file.

Usage:
    adif_fields.py input.adi --add-operator KN2D --add-my_gridsquare EL87
    adif_fields.py input.adi --add-operator KN2D --override
    adif_fields.py input.adi --delete-N3FJP%
    adif_fields.py input.adi --delete-APP% --add-operator KN2D --output-file out.adi

Delete patterns use % as a wildcard (e.g. --delete-N3FJP% removes all
N3FJP_COMPUTERNAME, N3FJP_StationID, etc.). % is used instead of * to
avoid shell glob expansion.
"""

import sys
import re
import fnmatch


HELP_TEXT = """\
adif_fields.py - Add or delete fields in ADIF records

Adds new fields to every record, replaces existing fields, or deletes
fields by name or wildcard pattern. When both --add and --delete are
used together, deletes are applied first.

Usage:
    adif_fields.py <input.adi> [options]

Arguments:
    input.adi                   Input ADIF file (use /dev/stdin for pipes)

Options:
    --add-<FIELD> <VALUE>       Add field to every record
    --delete-<PATTERN>          Delete fields matching pattern
    --output-file <file>        Write to file (default: stdout)
    --override                  Allow replacing existing fields on --add
    --help, -h                  Show this help message

Wildcards:
    Use % as a wildcard in --delete patterns (% is used instead of *
    to avoid shell glob expansion). All field matching is case-insensitive,
    so --delete-comment, --delete-Comment, and --delete-COMMENT all work.

    --delete-N3FJP%             Deletes N3FJP_COMPUTERNAME, N3FJP_StationID, etc.
    --delete-APP%               Deletes all APP-prefixed fields
    --delete-Contest_ID         Deletes exact field name

Examples:
    adif_fields.py input.adi --add-OPERATOR KN2D
    adif_fields.py input.adi --add-OPERATOR KN2D --override --output-file out.adi
    adif_fields.py input.adi --delete-N3FJP% --delete-APP%
    adif_fields.py input.adi --delete-N3FJP% --add-OPERATOR KN2D --override
"""


def parse_args(argv):
    if len(argv) > 1 and argv[1] in ("--help", "-h"):
        print(HELP_TEXT)
        sys.exit(0)

    input_file = None
    output_file = None
    override = False
    add_fields = {}
    delete_patterns = []

    i = 1
    while i < len(argv):
        arg = argv[i]
        if arg in ("--help", "-h"):
            print(HELP_TEXT)
            sys.exit(0)
        elif arg == "--output-file" and i + 1 < len(argv):
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
        print(f"Try '{argv[0]} --help' for more information.", file=sys.stderr)
        sys.exit(1)

    if not add_fields and not delete_patterns:
        print("No --add or --delete arguments provided.", file=sys.stderr)
        print(f"Try '{argv[0]} --help' for more information.", file=sys.stderr)
        sys.exit(1)

    return input_file, output_file, add_fields, delete_patterns, override


def format_field(name, value):
    return f"<{name}:{len(value)}>{value}"


def matches_any_pattern(field_name, patterns):
    """Check if field_name matches any of the patterns (case-insensitive).

    Patterns use % as wildcard, converted to * for fnmatch.
    """
    for pattern in patterns:
        glob_pattern = pattern.replace("%", "*")
        if fnmatch.fnmatch(field_name.upper(), glob_pattern.upper()):
            return True
    return False


def delete_fields(record_text, patterns):
    """Remove all ADIF fields matching any of the glob patterns.

    Uses the length encoded in each tag to consume the full value,
    including values that contain spaces.
    """
    result = []
    pos = 0
    for m in re.finditer(r"<([A-Za-z_][A-Za-z0-9_]*):(\d+)>", record_text):
        field_name = m.group(1)
        value_len = int(m.group(2))
        value_end = m.end() + value_len

        if matches_any_pattern(field_name, patterns):
            # Keep any text before this field, but strip trailing whitespace
            # that preceded this tag
            before = record_text[pos:m.start()]
            result.append(before)
            # Skip optional trailing whitespace after the value
            skip = value_end
            while skip < len(record_text) and record_text[skip] in (" ", "\t"):
                skip += 1
            pos = skip
        else:
            # Keep everything from current pos through end of value
            result.append(record_text[pos:value_end])
            pos = value_end

    # Append any remaining text after the last field
    result.append(record_text[pos:])
    return "".join(result)


def add_fields(record_text, fields, override, record_num):
    """Add or replace fields in a record."""
    for field_name, field_value in fields.items():
        pattern = re.compile(
            rf"<({re.escape(field_name)}):(\d+)>",
            re.IGNORECASE,
        )
        existing = pattern.search(record_text)

        if existing:
            # Extract current value using the length from the tag
            old_value_len = int(existing.group(2))
            old_end = existing.end() + old_value_len
            old_value = record_text[existing.end():old_end]

            if old_value == field_value:
                continue  # Same value, skip silently

            if not override:
                print(
                    f"Error: Record {record_num} already has field "
                    f"<{field_name}> with a different value. "
                    f"Use --override to replace.",
                    file=sys.stderr,
                )
                sys.exit(1)
            record_text = (
                record_text[:existing.start()]
                + format_field(field_name, field_value)
                + record_text[old_end:]
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
