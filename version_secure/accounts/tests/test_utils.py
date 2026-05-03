import pytest
import secrets
from accounts.utils import hash_password, verify_password, validate_password
from accounts.models import Worker, PasswordHistory


class TestHashPassword:
    def test_same_input_same_salt_produces_same_hash(self):
        h1 = hash_password('MyPass@1', 'somesalt')
        h2 = hash_password('MyPass@1', 'somesalt')
        assert h1 == h2

    def test_different_salts_produce_different_hashes(self):
        h1 = hash_password('MyPass@1', 'salt1')
        h2 = hash_password('MyPass@1', 'salt2')
        assert h1 != h2

    def test_different_passwords_produce_different_hashes(self):
        h1 = hash_password('MyPass@1', 'salt')
        h2 = hash_password('OtherPass@1', 'salt')
        assert h1 != h2


class TestVerifyPassword:
    def test_correct_password_returns_true(self):
        salt = secrets.token_hex(16)
        hashed = hash_password('MyPass@1', salt)
        assert verify_password('MyPass@1', salt, hashed) is True

    def test_wrong_password_returns_false(self):
        salt = secrets.token_hex(16)
        hashed = hash_password('MyPass@1', salt)
        assert verify_password('WrongPass@1', salt, hashed) is False


@pytest.mark.django_db
class TestValidatePassword:
    def test_too_short_fails(self):
        errors = validate_password('Abc@1')
        assert any('10 characters' in e for e in errors)

    def test_missing_uppercase_fails(self):
        errors = validate_password('mypassword@1')
        assert any('uppercase' in e for e in errors)

    def test_missing_lowercase_fails(self):
        errors = validate_password('MYPASSWORD@1')
        assert any('lowercase' in e for e in errors)

    def test_missing_digit_fails(self):
        errors = validate_password('MyPassword@abc')
        assert any('digit' in e for e in errors)

    def test_missing_special_char_fails(self):
        errors = validate_password('MyPassword123')
        assert any('special character' in e for e in errors)

    def test_dictionary_word_fails(self):
        errors = validate_password('password')
        assert any('common' in e for e in errors)

    def test_valid_password_returns_no_errors(self):
        errors = validate_password('StrongPass@1')
        assert errors == []

    def test_password_history_rejected(self, regular_worker):
        old_pass = 'OldPass@123'
        PasswordHistory.objects.create(
            worker=regular_worker,
            hashed_password=hash_password(old_pass, 'oldsalt'),
            salt='oldsalt',
        )
        errors = validate_password(old_pass, worker=regular_worker)
        assert any('reuse' in e for e in errors)
