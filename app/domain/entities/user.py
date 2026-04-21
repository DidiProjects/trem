from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    id: str
    username: str
    email: Optional[str]
    password_hash: str
    profile_id: str
    profile_name: str
    status: str  # 'blocked' | 'active' | 'suspended'
    must_change_password: bool
    provisional_password_sent_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    @property
    def is_blocked(self) -> bool:
        return self.status == "blocked"
