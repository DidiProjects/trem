from urllib.parse import quote


def safe_filename(filename: str) -> str:
    return quote(filename, safe='')


def get_output_filename(original: str, operation: str) -> str:
    name = original.rsplit(".", 1)[0]
    return f"{name}-{operation}.pdf"
