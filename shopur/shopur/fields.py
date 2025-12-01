from django.db import models

from .crypto import encrypt_value, decrypt_value


class EncryptedTextField(models.TextField):
    """TextField шифрует данные перед сохранением и расшифровывает при чтении."""

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return decrypt_value(value)

    def to_python(self, value):
        if value is None or value == '':
            return value
        return decrypt_value(value)

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value in (None, ''):
            return value
        return encrypt_value(value)
