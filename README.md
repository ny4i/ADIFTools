# ADIFTools

A suite of Python utilities for manipulating ADIF (Amateur Data Interchange Format) files commonly used in amateur radio logging.

No dependencies beyond Python 3.

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

Add or delete fields across every record in an ADIF file. Supports wildcard deletion using `%` as the wildcard character.

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

### Piping

The tools are designed to work together in a pipeline:

```bash
./adif_oneline.py n3fjp_export.adi | ./adif_fields.py /dev/stdin --delete-N3FJP% --add-OPERATOR KN2D --override --output-file clean.adi
```

## License

MIT
