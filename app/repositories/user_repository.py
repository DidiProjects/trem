from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.interfaces.i_user_repository import IUserRepository
from app.domain.entities.user import User
from app.infrastructure.database.models import ProfileModel, RefreshTokenModel, UserModel
from app.repositories.base import BaseRepository


def _to_entity(orm: UserModel) -> User:
    return User(
        id=str(orm.id),
        username=orm.username,
        email=orm.email,
        password_hash=orm.password_hash,
        profile_id=str(orm.profile_id),
        profile_name=orm.profile.name if orm.profile else "",
        status=orm.status,
        must_change_password=orm.must_change_password,
        provisional_password_sent_at=orm.provisional_password_sent_at,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
        last_login_at=orm.last_login_at,
    )


class UserRepository(BaseRepository, IUserRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_id(self, user_id: str) -> Optional[User]:
        result = await self._session.execute(
            select(UserModel)
            .options(joinedload(UserModel.profile))
            .where(UserModel.id == user_id)
        )
        orm = result.scalar_one_or_none()
        return _to_entity(orm) if orm else None

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self._session.execute(
            select(UserModel)
            .options(joinedload(UserModel.profile))
            .where(UserModel.username == username)
        )
        orm = result.scalar_one_or_none()
        return _to_entity(orm) if orm else None

    async def create(
        self,
        username: str,
        password_hash: str,
        profile_id: str,
        email: Optional[str] = None,
    ) -> User:
        orm = UserModel(
            username=username,
            email=email,
            password_hash=password_hash,
            profile_id=profile_id,
        )
        self._session.add(orm)
        await self._session.flush()
        await self._session.refresh(orm, ["profile"])
        return _to_entity(orm)

    async def update_password(
        self,
        user_id: str,
        password_hash: str,
        must_change_password: bool,
    ) -> None:
        await self._session.execute(
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(
                password_hash=password_hash,
                must_change_password=must_change_password,
                updated_at=datetime.now(timezone.utc),
            )
        )

    async def update_status(self, user_id: str, status: str) -> None:
        await self._session.execute(
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(status=status, updated_at=datetime.now(timezone.utc))
        )

    async def update_last_login(self, user_id: str, at: datetime) -> None:
        await self._session.execute(
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(last_login_at=at, updated_at=at)
        )

    async def set_provisional_password_sent(self, user_id: str, at: datetime) -> None:
        await self._session.execute(
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(
                provisional_password_sent_at=at,
                updated_at=datetime.now(timezone.utc),
            )
        )

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[User]:
        result = await self._session.execute(
            select(UserModel)
            .options(joinedload(UserModel.profile))
            .order_by(UserModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [_to_entity(row) for row in result.scalars().all()]

    # --- Refresh tokens ---

    async def create_refresh_token(
        self,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        token = RefreshTokenModel(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self._session.add(token)
        await self._session.flush()

    async def get_refresh_token(self, token_hash: str) -> Optional[RefreshTokenModel]:
        result = await self._session.execute(
            select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, token_hash: str) -> None:
        await self._session.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.token_hash == token_hash)
            .values(revoked=True)
        )

    async def revoke_all_refresh_tokens(self, user_id: str) -> None:
        await self._session.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.user_id == user_id)
            .values(revoked=True)
        )

    async def get_profile_by_name(self, name: str) -> Optional[ProfileModel]:
        result = await self._session.execute(
            select(ProfileModel).where(ProfileModel.name == name)
        )
        return result.scalar_one_or_none()
