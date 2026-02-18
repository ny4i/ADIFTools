# ADIFTools

A suite of Python utilities for manipulating ADIF (Amateur Data Interchange Format) files commonly used in amateur radio logging.

No dependencies beyond Python 3.

All scripts support `--help` / `-h` for built-in usage information.

## Tools

### adif_oneline.py

Converts ADIF files with one field per line (as exported by N3FJP and other loggers) into standard one-record-per-line format. The header is preserved as-is.

```bash
# Print to stdout
./adif_oneline.py input.adi

# Write to file
./adif_oneline.py input.adi output.adi
```

### adif_fields.py

Add or delete fields across every record in an ADIF file.

**Options:**

| Option | Description |
|--------|-------------|
| `--add-<FIELD> <VALUE>` | Add a field to every record |
| `--delete-<PATTERN>` | Delete fields matching a name or pattern |
| `--output-file <file>` | Write to file (default: stdout) |
| `--override` | Allow replacing fields that already exist |

**Wildcards:** Use `%` as a wildcard in `--delete` patterns (`%` is used instead of `*` to avoid shell glob expansion). All field matching is case-insensitive.

```bash
# Add a field
./adif_fields.py input.adi --add-OPERATOR KN2D

# Add multiple fields, write to file
./adif_fields.py input.adi --add-OPERATOR KN2D --add-MY_GRIDSQUARE EL87 --output-file output.adi

# Replace existing fields (errors without --override)
./adif_fields.py input.adi --add-OPERATOR KN2D --override

# Delete fields by exact name
./adif_fields.py input.adi --delete-Contest_ID

# Delete fields by wildcard pattern
./adif_fields.py input.adi --delete-N3FJP%

# Combine operations (deletes run first, then adds)
./adif_fields.py input.adi --delete-N3FJP% --delete-APP% --add-OPERATOR KN2D --override
```

### adif_clean.sh

Batch processing script that runs all `.adi` files in a directory through `adif_oneline.py` and `adif_fields.py` to produce cleaned output. Removes `APP*`, `N3FJP*`, and `Comment` fields by default.

Edit the `TOOLS_DIR` variable at the top of the script to point to the directory containing the Python scripts.

```bash
./adif_clean.sh <input_dir> <output_dir>

# Example
./adif_clean.sh ~/logs ~/logs/cleaned
```

### Piping

The tools are designed to work together in a pipeline:

```bash
# Full cleanup pipeline
./adif_oneline.py n3fjp_export.adi \
    | ./adif_fields.py /dev/stdin --delete-N3FJP% --delete-APP% --delete-Comment \
        --add-OPERATOR KN2D --override \
        --output-file clean.adi

# One-liner to process all files in a directory (zsh)
for f in /path/to/dir/*.adi; do
    ./adif_oneline.py "$f" \
        | ./adif_fields.py /dev/stdin --delete-N3FJP% --delete-APP% \
            --output-file "processed/${f:t}"
done
```

## License

MIT
