"""
test_login.py - Testes unitários para login e registo.
"""

import unittest
import os
import json
from src.auth import login, register
from src.database import DATA_DIR


class TestLogin(unittest.TestCase):

    def setUp(self):
        """Prepara dados de teste."""
        self.test_users = [
            {
                "id": 1,
                "name": "Instrutor Teste",
                "email": "instrutor@test.com",
                "password": "Test123!",
                "type": "INSTRUCTOR",
                "created_at": "2025-01-01"
            }
        ]
        path = os.path.join(DATA_DIR, "users.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.test_users, f)

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
