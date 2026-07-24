import uuid
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    encrypt_api_key,
    decrypt_api_key,
)


def test_password_hashing():
    """Test password hashing and verification."""
    password = "MySuperSecretPassword123!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_token_encode_decode():
    """Test JWT creation and decoding."""
    user_id = uuid.uuid4()
    token = create_access_token(user_id)

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert "exp" in payload
    assert "iat" in payload


def test_jwt_invalid_token():
    """Test decoding an invalid token returns None."""
    assert decode_access_token("invalid.token.str") is None


def test_api_key_encryption_decryption():
    """Test API key symmetric encryption and decryption."""
    api_key = "sk_live_1234567890abcdef"
    encrypted = encrypt_api_key(api_key)

    assert encrypted != api_key
    decrypted = decrypt_api_key(encrypted)
    assert decrypted == api_key
