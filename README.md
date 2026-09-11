## Krapinscan

Krapinscan extracts taxpayer, address, tax obligation, KRA PIN, and certificate
date details from Kenya Revenue Authority PIN certificate PDFs.

### Install

```bash
uv add krapinscan
```

For local development:

```bash
uv sync
```

### Python API

```python
from krapinscan import parse_statement

result_json = parse_statement("certificate.pdf")
```

`parse_statement` accepts a PDF path or PDF bytes and returns a JSON string with
lowercase snake_case keys.

### Command line

```bash
krapinscan certificate.pdf
```
