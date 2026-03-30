"""
test_aulas.py - Testes unitários para gestão de aulas.
"""

import unittest
import os
import json
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch
from src.containers.class_service import create_class, list_classes, cancel_class, edit_class, get_class_by_id
from src.database import save_json
from src.utils import paginate


class TestClasses(unittest.TestCase):

    def setUp(self):
        """Usa directório temporário para não afectar os dados reais."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.patcher = patch('src.database.DATA_DIR', self.temp_dir.name)
        self.patcher.start()
        for filename in ["classes.json", "reservations.json", "waitlist.json", "notifications.json"]:
            path = os.path.join(self.temp_dir.name, filename)
            with open(path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def tearDown(self):
        self.patcher.stop()
        self.temp_dir.cleanup()

    def test_create_class(self):
        future_date = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
        success, msg = create_class("Pilates Mat", future_date, "10:00", 60, "Aula básica", 10, 1)
        self.assertTrue(success)
        classes = list_classes()
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0]["name"], "Pilates Mat")

    def test_cancel_class(self):
        future_date = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
        create_class("Pilates", future_date, "10:00", 60, "", 10, 1)
        classes = list_classes()
        success, msg = cancel_class(classes[0]["id"], 1)
        self.assertTrue(success)
        updated = get_class_by_id(classes[0]["id"])
        self.assertEqual(updated["status"], "cancelado")

    def test_cancel_class_wrong_instructor(self):
        future_date = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
        create_class("Pilates", future_date, "10:00", 60, "", 10, 1)
        classes = list_classes()
        success, msg = cancel_class(classes[0]["id"], 999)
        self.assertFalse(success)

    def test_edit_class(self):
        future_date = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
        create_class("Pilates", future_date, "10:00", 60, "", 10, 1)
        classes = list_classes()
        success, msg = edit_class(classes[0]["id"], 1, name="Pilates Avançado")
        self.assertTrue(success)
        updated = get_class_by_id(classes[0]["id"])
        self.assertEqual(updated["name"], "Pilates Avançado")

    def test_create_class_past_datetime_is_rejected(self):
        from datetime import datetime, timedelta

        now = datetime.now()
        yesterday = now - timedelta(days=1)
        date_past = yesterday.strftime("%d/%m/%Y")
        time_past = yesterday.strftime("%H:%M")

        success, msg = create_class("Pilates", date_past, time_past, 60, "", 10, 1)
        self.assertFalse(success)
        self.assertIn("futuro", msg.lower())

    def test_create_class_today_with_past_time_is_rejected(self):
        from datetime import datetime, timedelta

        now = datetime.now()
        date_today = now.strftime("%d/%m/%Y")
        time_past = (now - timedelta(minutes=15)).strftime("%H:%M")

        success, msg = create_class("Pilates", date_today, time_past, 60, "", 10, 1)
        self.assertFalse(success)
        self.assertIn("futuro", msg.lower())

    def test_create_class_today_with_future_time_is_accepted(self):
        from datetime import datetime, timedelta

        now = datetime.now()
        date_today = now.strftime("%d/%m/%Y")
        time_future = (now + timedelta(minutes=15)).strftime("%H:%M")

        success, msg = create_class("Pilates", date_today, time_future, 60, "", 10, 1)
        self.assertTrue(success)

    def test_pagination_workflow(self):
        now = datetime.now()
        for i in range(7):
            schedule_date = (now + timedelta(days=i + 1)).strftime("%d/%m/%Y")
            create_class(f"Pilates {i+1}", schedule_date, "09:00", 60, "", 10, 1)

        all_classes = list_classes(instructor_id=1)
        page1, total_pages, current_page = paginate(all_classes, 1, 5)
        page2, _, _ = paginate(all_classes, 2, 5)

        self.assertEqual(total_pages, 2)
        self.assertEqual(len(page1), 5)
        self.assertEqual(len(page2), 2)
        self.assertEqual(current_page, 1)

    def test_list_classes_separates_active_and_history(self):
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
                "name": "Aula Realizada",
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

        active_classes = list_classes(instructor_id=1)
        history_classes = list_classes(instructor_id=1, history=True)

        self.assertEqual([c["name"] for c in active_classes], ["Aula Ativa"])
        self.assertEqual([c["display_status"] for c in history_classes], ["Cancelada", "Realizada"])


if __name__ == "__main__":
    unittest.main()
