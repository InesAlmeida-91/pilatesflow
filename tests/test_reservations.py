"""
test_reservas.py - Testes unitários para gestão de reservas.
"""

import unittest
import os
import json
from src.containers.class_service import create_class, list_classes
from src.containers.reservation_service import reserve_class, cancel_reservation, list_student_reservations, list_available_classes
from src.database import DATA_DIR


class TestReservations(unittest.TestCase):

    def setUp(self):
        """Prepara dados de teste."""
        for filename in ["classes.json", "reservations.json"]:
            path = os.path.join(DATA_DIR, filename)
            with open(path, "w", encoding="utf-8") as f:
                json.dump([], f)

        users = [
            {"id": 1, "name": "Instrutor", "email": "i@t.com", "password": "Test123!", "type": "INSTRUCTOR", "created_at": "2025-01-01"},
            {"id": 2, "name": "Aluno", "email": "a@t.com", "password": "Test123!", "type": "STUDENT", "created_at": "2025-01-01"},
        ]
        path = os.path.join(DATA_DIR, "users.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(users, f)

        create_class("Pilates", "20/04/2025", "09:00", 60, "", 2, 1)

    def test_reserve_class(self):
        classes = list_classes()
        success, msg = reserve_class(2, classes[0]["id"])
        self.assertTrue(success)

    def test_reserve_duplicate(self):
        classes = list_classes()
        reserve_class(2, classes[0]["id"])
        success, msg = reserve_class(2, classes[0]["id"])
        self.assertFalse(success)

    def test_cancel_reservation(self):
        classes = list_classes()
        reserve_class(2, classes[0]["id"])
        reservations = list_student_reservations(2)
        success, msg = cancel_reservation(reservations[0]["reservation_id"], 2)
        self.assertTrue(success)

    def test_max_students_limit(self):
        classes = list_classes()
        # Aula com max 2 alunos
        reserve_class(2, classes[0]["id"])
        # Adicionar outro aluno manualmente
        from src.database import load_json, save_json
        res = load_json("reservas.json")
        res.append({"id": 2, "student_id": 3, "class_id": classes[0]["id"], "created_at": "2025-01-01", "status": "confirmado"})
        save_json("reservas.json", res)

        available = list_available_classes()
        self.assertEqual(len(available), 0)  # Sem vagas


if __name__ == "__main__":
    unittest.main()
