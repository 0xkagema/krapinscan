## Krapinscan

Krapinscan extracts taxpayer, address, tax obligation, KRA PIN, and certificate
date details from Kenya Revenue Authority PIN certificate PDFs.

### Install

```bash
 uv add git+https://github.com/0xkagema/krapinscan
```

For local development:

```bash
uv sync
```

### Usage

```python
from krapinscan import parse_certificate

result_json = parse_certificate("certificate.pdf")
```

`parse_certificate` accepts a PDF path or PDF bytes and returns a JSON string with
lowercase snake_case keys.


```
