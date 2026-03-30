"""
test_login.py - Testes unitários para login, registo, perfil e recuperação de password.
"""

import unittest
import os
import json
import tempfile
from unittest.mock import patch
from werkzeug.security import generate_password_hash
from src.auth import login, register, update_profile, generate_reset_token, verify_reset_token, reset_password


class TestLogin(unittest.TestCase):

    def setUp(self):
        """Usa directório temporário para não afectar os dados reais."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.patcher = patch('src.database.DATA_DIR', self.temp_dir.name)
        self.patcher.start()
        test_users = [
            {
                "id": 1,
                "name": "Instrutor Teste",
                "email": "instrutor@test.com",
                "password": generate_password_hash("Test123!"),
                "type": "INSTRUCTOR",
                "created_at": "2025-01-01"
            },
            {
                "id": 2,
                "name": "Aluno Teste",
                "email": "aluno@test.com",
                "password": generate_password_hash("Aluno12!"),
                "type": "STUDENT",
                "created_at": "2025-01-01"
            }
        ]
        path = os.path.join(self.temp_dir.name, "users.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(test_users, f)

    def tearDown(self):
        self.patcher.stop()
        self.temp_dir.cleanup()

    # ── Login ──
    def test_login_success(self):
        user = login("instrutor@test.com", "Test123!")
        self.assertIsNotNone(user)
        self.assertEqual(user["name"], "Instrutor Teste")

    def test_login_wrong_password(self):
        user = login("instrutor@test.com", "wrongpass")
        self.assertIsNone(user)

    def test_login_wrong_email(self):
        user = login("naoexiste@test.com", "Test123!")
        self.assertIsNone(user)

    def test_login_empty_fields(self):
        self.assertIsNone(login("", ""))
        self.assertIsNone(login("instrutor@test.com", ""))
        self.assertIsNone(login("", "Test123!"))

    def test_login_case_sensitive_email(self):
        user = login("INSTRUTOR@TEST.COM", "Test123!")
        self.assertIsNone(user)

    # ── Registo ──
    def test_register_success(self):
        success, msg = register("Novo Aluno", "novo@test.com", "Aluno12!")
        self.assertTrue(success)

    def test_register_duplicate_email(self):
        success, msg = register("Outro", "instrutor@test.com", "Test123!")
        self.assertFalse(success)
        self.assertIn("e-mail", msg.lower())

    def test_register_duplicate_email_student(self):
        success, msg = register("Outro", "aluno@test.com", "Test123!")
        self.assertFalse(success)

    def test_register_invalid_email(self):
        success, msg = register("Teste", "emailinvalido", "Test123!")
        self.assertFalse(success)

    def test_register_weak_password(self):
        success, msg = register("Teste", "teste@test.com", "abc")
        self.assertFalse(success)

    def test_register_empty_name(self):
        success, msg = register("", "novo2@test.com", "Aluno12!")
        self.assertFalse(success)

    def test_register_whitespace_name(self):
        success, msg = register("   ", "novo3@test.com", "Aluno12!")
        self.assertFalse(success)

    def test_register_password_no_uppercase(self):
        success, msg = register("Teste", "t@t.com", "aluno12!")
        self.assertFalse(success)
        self.assertIn("maiúscula", msg.lower())

    def test_register_password_no_special(self):
        success, msg = register("Teste", "t@t.com", "Aluno123")
        self.assertFalse(success)
        self.assertIn("especial", msg.lower())

    def test_register_is_student_type(self):
        register("Novo", "tipo@test.com", "Aluno12!")
        user = login("tipo@test.com", "Aluno12!")
        self.assertEqual(user["type"], "STUDENT")

    # ── Perfil ──
    def test_update_profile_name(self):
        success, msg, user = update_profile(2, "Novo Nome", "aluno@test.com", "", "")
        self.assertTrue(success)
        self.assertEqual(user["name"], "Novo Nome")

    def test_update_profile_email(self):
        success, msg, user = update_profile(2, "Aluno Teste", "novo@email.com", "", "")
        self.assertTrue(success)
        self.assertEqual(user["email"], "novo@email.com")

    def test_update_profile_duplicate_email(self):
        success, msg, user = update_profile(2, "Aluno Teste", "instrutor@test.com", "", "")
        self.assertFalse(success)

    def test_update_profile_password(self):
        success, msg, user = update_profile(2, "Aluno Teste", "aluno@test.com", "Aluno12!", "NovaPass1!")
        self.assertTrue(success)
        logged = login("aluno@test.com", "NovaPass1!")
        self.assertIsNotNone(logged)

    def test_update_profile_wrong_current_password(self):
        success, msg, user = update_profile(2, "Aluno Teste", "aluno@test.com", "Errada!1", "NovaPass1!")
        self.assertFalse(success)

    def test_update_profile_new_password_without_current(self):
        success, msg, user = update_profile(2, "Aluno Teste", "aluno@test.com", "", "NovaPass1!")
        self.assertFalse(success)

    # ── Recuperação de Password ──
    def test_generate_and_verify_token(self):
        token = generate_reset_token("aluno@test.com", "test-secret")
        email = verify_reset_token(token, "test-secret")
        self.assertEqual(email, "aluno@test.com")

    def test_verify_invalid_token(self):
        email = verify_reset_token("token-invalido", "test-secret")
        self.assertIsNone(email)

    def test_reset_password_success(self):
        success, msg = reset_password("aluno@test.com", "Reset12!")
        self.assertTrue(success)
        user = login("aluno@test.com", "Reset12!")
        self.assertIsNotNone(user)

    def test_reset_password_weak(self):
        success, msg = reset_password("aluno@test.com", "abc")
        self.assertFalse(success)

    def test_reset_password_nonexistent_user(self):
        success, msg = reset_password("fake@test.com", "Reset12!")
        self.assertFalse(success)

    def test_register_invalid_email(self):
        success, msg = register("Teste", "emailinvalido", "Test123!")
        self.assertFalse(success)

    def test_register_weak_password(self):
        success, msg = register("Teste", "teste@test.com", "abc")
        self.assertFalse(success)


if __name__ == "__main__":
    unittest.main()
