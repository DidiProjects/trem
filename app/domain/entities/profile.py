from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Profile:
    id: str
    name: str
    description: Optional[str]
    created_at: datetime


# Nomes de perfil como constantes para evitar strings soltas no código
FILE_EDITOR = "file_editor"
AIRLINE_COMPANY = "airline_company"
