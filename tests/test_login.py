"""
test_login.py - Testes unitários para login e registo.
"""

import unittest
import os
import json
import tempfile
from unittest.mock import patch
from werkzeug.security import generate_password_hash
from src.auth import login, register


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
            }
        ]
        path = os.path.join(self.temp_dir.name, "users.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(test_users, f)

    def tearDown(self):
        self.patcher.stop()
        self.temp_dir.cleanup()

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

    def test_register_success(self):
        success, msg = register("Novo Aluno", "novo@test.com", "Aluno12!")
        self.assertTrue(success)

    def test_register_duplicate_email(self):
        success, msg = register("Outro", "instrutor@test.com", "Test123!")
        self.assertFalse(success)

    def test_register_invalid_email(self):
        success, msg = register("Teste", "emailinvalido", "Test123!")
        self.assertFalse(success)

    def test_register_weak_password(self):
        success, msg = register("Teste", "teste@test.com", "abc")
        self.assertFalse(success)


if __name__ == "__main__":
    unittest.main()
