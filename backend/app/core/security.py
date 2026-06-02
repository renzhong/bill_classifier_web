from datetime import UTC, datetime, timedelta
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

_settings = get_settings()
_pwd_hasher = PasswordHash.recommended()


def hash_password(raw: str) -> str:
    return _pwd_hasher.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    return _pwd_hasher.verify(raw, hashed)


def create_access_token(subject: str | int, extra: dict[str, Any] | None = None) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": now + timedelta(minutes=_settings.jwt_access_ttl_min),
        "type": "access",
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, _settings.jwt_secret, algorithm=_settings.jwt_alg)


def create_refresh_token(subject: str | int) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(subject),
        "iat": now,
        "exp": now + timedelta(days=_settings.jwt_refresh_ttl_days),
        "type": "refresh",
    }
    return jwt.encode(payload, _settings.jwt_secret, algorithm=_settings.jwt_alg)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, _settings.jwt_secret, algorithms=[_settings.jwt_alg])
    except JWTError as e:
        raise ValueError(f"invalid token: {e}") from e


def _fernet() -> Fernet:
    key = _settings.fernet_key.encode() if isinstance(_settings.fernet_key, str) else _settings.fernet_key
    return Fernet(key)


def encrypt_secret(plain: str) -> str:
    return _fernet().encrypt(plain.encode()).decode()


def decrypt_secret(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken as e:
        raise ValueError("invalid encrypted secret") from e
