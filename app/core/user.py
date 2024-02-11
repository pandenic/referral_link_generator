from typing import Union, Optional
from uuid import UUID

from fastapi import Depends, Request
from fastapi_users import UUIDIDMixin, BaseUserManager, InvalidPasswordException, FastAPIUsers
from fastapi_users.authentication import BearerTransport, JWTStrategy, AuthenticationBackend
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_async_session
from app.models import User
from app.schemas import UserCreate


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=settings.secret, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


class UserManager(UUIDIDMixin, BaseUserManager[User, UUID]):
    reset_password_token_secret = settings.secret
    verification_token_secret = settings.secret

    async def validate_password(
        self,
        password: str,
        user: Union[UserCreate, User],
    ) -> None:
        if len(password) < 3:
            raise InvalidPasswordException(
                reason="Password should be at least 8 characters"
            )
        if user.email in password:
            raise InvalidPasswordException(
                reason="Password should not contain e-mail"
            )

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)

fastapi_users = FastAPIUsers[User, UUID](
    get_user_manager, [auth_backend],
)

current_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)