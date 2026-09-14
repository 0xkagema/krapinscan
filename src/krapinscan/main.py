import io
import json
import re
import argparse
from enum import Enum
import pdfplumber
from pdfplumber.utils.exceptions import PdfminerException, MalformedPDFException


class KraPinType(Enum):
    INDIVIDUAL = "Individual"
    COMPANY = "Company"


def _clean(value: object) -> str:
    """Normalize a cell without changing the value's meaning."""
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _json_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", _clean(value).lower()).strip("_")


def _extract_header_details(text: str) -> dict[str, str | None]:
    certificate_date = re.search(
        r"Certificate\s+Date\s*:?\s*(\d{2}/\d{2}/\d{4})",
        text,
        flags=re.IGNORECASE,
    )
    pin_number = re.search(
        r"Personal\s+Identification\s+Number\s*:?\s*([A-Z0-9]+)",
        text,
        flags=re.IGNORECASE,
    )

    # determine type => if starts with A -> Individual, else Company
    if pin_number:
        pin_type = (
            KraPinType.INDIVIDUAL.value
            if pin_number.group(1).startswith("A")
            else KraPinType.COMPANY.value
        )

    return {
        "kra_pin": pin_number.group(1) if pin_number else None,
        "certificate_date": certificate_date.group(1) if certificate_date else None,
        "pin_type": pin_type if pin_number else None,
    }


def _label_value(cell: object) -> tuple[str, str] | None:
    """Return a label/value pair from a cell such as ``County : Kiambu``."""
    text = _clean(cell)
    if ":" not in text:
        return None
    label, value = text.split(":", 1)
    label = _clean(label)
    value = _clean(value)
    return (label, value) if label and value else None


def _extract_label_values(table: list[list[object]]) -> dict[str, str]:
    values: dict[str, str] = {}
    for row in table:
        for cell in row:
            pair = _label_value(cell)
            if pair:
                values[pair[0]] = pair[1]
            elif len(row) == 2 and cell is row[0] and ":" not in _clean(cell):
                label = _clean(cell)
                value = _clean(row[1])
                if label and value:
                    values[label] = value
    return values


def _extract_obligations(table: list[list[object]]) -> list[dict[str, str]]:
    header_index = None
    headers: list[str] = []
    for index, row in enumerate(table):
        normalized = {_clean(cell).lower() for cell in row}
        if "tax obligation(s)" in normalized and "status" in normalized:
            header_index = index
            headers = [_clean(cell) for cell in row]
            break

    if header_index is None:
        headers = [
            "Sr. No.",
            "Tax Obligation(s)",
            "Effective From Date",
            "Effective Till Date",
            "Status",
        ]
        data_rows = table
    else:
        data_rows = table[header_index + 1 :]

    obligations = []
    for row in data_rows:
        values = [_clean(cell) for cell in row]
        if not any(values):
            continue
        obligations.append(dict(zip(headers, values)))
    return obligations


def parse_certificate(
    path_or_fp: str | bytes | bytearray,
) -> str:
    # handle bytes/bytearray vs file path
    if isinstance(path_or_fp, (bytes, bytearray)):
        file = io.BytesIO(path_or_fp)
    else:
        file = open(path_or_fp, "rb")

    try:
        with pdfplumber.open(path_or_fp=file) as pdf:

            # a kra pin should only have one page, throw an error if there are more than one page
            if len(pdf.pages) > 1:
                raise Exception("The PDF file has more than one page.")

            first_page = pdf.pages[0]

            tables = first_page.extract_tables()

            if len(tables) != 4:
                raise Exception(
                    "The PDF file does not contain the expected four tables."
                )

            taxpayer = _extract_label_values(tables[1])
            address = _extract_label_values(tables[2])
            header_details = _extract_header_details(first_page.extract_text() or "")
            details = {
                **header_details,
                "taxpayer_name": taxpayer.get("Taxpayer Name"),
                "email_address": taxpayer.get("Email Address"),
                "address": {_json_key(key): value for key, value in address.items()},
                "obligations": [
                    {_json_key(key): value for key, value in obligation.items()}
                    for obligation in _extract_obligations(tables[3])
                ],
            }
            return json.dumps(details, indent=2)

    except PdfminerException as e:

        raise Exception("Wrong password or corrupted PDF file.")
    except MalformedPDFException as e:
        raise Exception("The PDF file is malformed or corrupted.")

    finally:
        if not isinstance(path_or_fp, (bytes, bytearray)):
            file.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract details from a KRA PIN certificate PDF."
    )
    parser.add_argument("pdf_path", help="Path to the KRA PIN certificate PDF")
    args = parser.parse_args()
    print(parse_certificate(args.pdf_path))


if __name__ == "__main__":
    main()
