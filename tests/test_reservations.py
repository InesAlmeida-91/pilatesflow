"""
test_reservas.py - Testes unitários para gestão de reservas.
"""

import unittest
import os
import json
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch
from src.containers.class_service import create_class, list_classes
from src.containers.reservation_service import reserve_class, cancel_reservation, list_student_reservations, list_available_classes
from src.database import save_json
from src.utils import paginate


class TestReservations(unittest.TestCase):

    def setUp(self):
        """Usa directório temporário para não afectar os dados reais."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.patcher = patch('src.database.DATA_DIR', self.temp_dir.name)
        self.patcher.start()
        for filename in ["classes.json", "reservations.json", "waitlist.json", "notifications.json"]:
            path = os.path.join(self.temp_dir.name, filename)
            with open(path, "w", encoding="utf-8") as f:
                json.dump([], f)

        users = [
            {"id": 1, "name": "Instrutor", "email": "i@t.com", "password": "Test123!", "type": "INSTRUCTOR", "created_at": "2025-01-01"},
            {"id": 2, "name": "Aluno", "email": "a@t.com", "password": "Test123!", "type": "STUDENT", "created_at": "2025-01-01"},
        ]
        path = os.path.join(self.temp_dir.name, "users.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(users, f)

        future_date = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
        create_class("Pilates", future_date, "09:00", 60, "", 2, 1)

    def tearDown(self):
        self.patcher.stop()
        self.temp_dir.cleanup()

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
        res = load_json("reservations.json")
        res.append({"id": 2, "student_id": 3, "class_id": classes[0]["id"], "created_at": "2025-01-01", "status": "confirmado"})
        save_json("reservations.json", res)

        available = list_available_classes()
        self.assertEqual(len(available), 1)  # Aula visível mas sem vagas (lista de espera)
        self.assertEqual(available[0]["spots_left"], 0)

    def test_reservations_pagination(self):
        # Cria várias reservas para o mesmo aluno em aulas diferentes
        for i in range(7):
            future_date = (datetime.now() + timedelta(days=i + 2)).strftime("%d/%m/%Y")
            create_class(f"Pilates {i+1}", future_date, "09:00", 60, "", 10, 1)
            classes = list_classes()
            reserve_class(2, classes[-1]["id"])

        all_reservations = list_student_reservations(2)
        page1, total_pages, current_page = paginate(all_reservations, 1, 5)
        page2, _, _ = paginate(all_reservations, 2, 5)

        self.assertEqual(total_pages, 2)
        self.assertEqual(len(page1), 5)
        self.assertEqual(len(page2), 2)
        self.assertEqual(current_page, 1)

    def test_list_student_reservations_separates_active_and_history(self):
        future_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        past_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
        save_json("classes.json", [
            {
                "id": 1,
                "name": "Aula Ativa",
                "schedule": f"{future_date} 09:00",
                "duration": 60,
                "description": "",
                "status": "confirmado",
                "max_students": 10,
                "instructor_id": 1,
                "created_at": "2025-01-01"
            },
            {
                "id": 2,
                "name": "Aula Passada",
                "schedule": f"{past_date} 09:00",
                "duration": 60,
                "description": "",
                "status": "confirmado",
                "max_students": 10,
                "instructor_id": 1,
                "created_at": "2025-01-01"
            },
            {
                "id": 3,
                "name": "Aula Cancelada",
                "schedule": f"{future_date} 11:00",
                "duration": 60,
                "description": "",
                "status": "cancelado",
                "max_students": 10,
                "instructor_id": 1,
                "created_at": "2025-01-01"
            }
        ])
        save_json("reservations.json", [
            {"id": 1, "student_id": 2, "class_id": 1, "created_at": "2025-01-01", "status": "confirmado"},
            {"id": 2, "student_id": 2, "class_id": 2, "created_at": "2025-01-01", "status": "confirmado"},
            {"id": 3, "student_id": 2, "class_id": 3, "created_at": "2025-01-01", "status": "cancelado"}
        ])

        active_reservations = list_student_reservations(2)
        history_reservations = list_student_reservations(2, history=True)

        self.assertEqual([r["class_name"] for r in active_reservations], ["Aula Ativa"])
        self.assertEqual([r["display_status"] for r in history_reservations], ["Cancelada", "Realizada"])

    def test_list_available_classes_excludes_past_classes(self):
        future_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        past_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
        save_json("classes.json", [
            {
                "id": 1,
                "name": "Aula Passada",
                "schedule": f"{past_date} 09:00",
                "duration": 60,
                "description": "",
                "status": "confirmado",
                "max_students": 10,
                "instructor_id": 1,
                "created_at": "2025-01-01"
            },
            {
                "id": 2,
                "name": "Aula Futura",
                "schedule": f"{future_date} 09:00",
                "duration": 60,
                "description": "",
                "status": "confirmado",
                "max_students": 10,
                "instructor_id": 1,
                "created_at": "2025-01-01"
            }
        ])

        available = list_available_classes(2)

        self.assertEqual([c["name"] for c in available], ["Aula Futura"])


if __name__ == "__main__":
    unittest.main()
