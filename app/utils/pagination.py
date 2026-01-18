from typing import List
from fastapi import HTTPException


def parse_page_ranges(pages: str, total_pages: int) -> List[int]:
    result = []
    for part in pages.split(","):
        part = part.strip()
        if "-" in part:
            start, end = map(lambda x: int(x.strip()), part.split("-"))
            if start < 1 or end > total_pages or start > end:
                raise HTTPException(status_code=400, detail=f"Intervalo inválido: {part}")
            result.extend(range(start, end + 1))
        else:
            page = int(part)
            if page < 1 or page > total_pages:
                raise HTTPException(status_code=400, detail=f"Página inválida: {page}")
            result.append(page)
    return sorted(set(result))
