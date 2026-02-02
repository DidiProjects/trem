from urllib.parse import quote


def safe_filename(filename: str) -> str:
    if not filename:
        return ""
    filename = filename.replace("..", "")
    return quote(filename, safe='')


def get_output_filename(original: str, operation: str, preserve_extension: bool = False) -> str:
    if "." in original:
        name, ext = original.rsplit(".", 1)
        if preserve_extension:
            return f"{name}-{operation}.{ext}"
    else:
        name = original
        ext = "pdf"
    return f"{name}-{operation}.pdf"
