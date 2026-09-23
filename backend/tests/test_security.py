import pytest

from app.core.security import hash_password, verify_password


@pytest.mark.parametrize("password", ["synthetic-password", "x" * 100, "测试密码" * 10])
def test_argon2_password_round_trip(password):
    hashed = hash_password(password)
    assert hashed.startswith("$argon2id$")
    assert verify_password(password, hashed)
    assert not verify_password(password + "wrong", hashed)
