from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


_fernet = Fernet(settings.DATA_ENCRYPTION_KEY.encode())


def encrypt_value(value: str) -> str:
    """Encrypt plain text and return a base64 string."""
    if value is None:
        return value
    return _fernet.encrypt(value.encode('utf-8')).decode('utf-8')


def decrypt_value(value: str) -> str:
    """Decrypt stored value; return original if token is invalid (for legacy data)."""
    if value is None:
        return value
    try:
        return _fernet.decrypt(value.encode('utf-8')).decode('utf-8')
    except InvalidToken:
        return value
