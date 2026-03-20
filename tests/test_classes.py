"""
test_aulas.py - Testes unitários para gestão de aulas.
"""

import unittest
import os
import json
from src.containers.class_service import create_class, list_classes, cancel_class, edit_class, get_class_by_id
from src.database import DATA_DIR


class TestClasses(unittest.TestCase):

    def setUp(self):
        """Limpa dados de aulas e reservas antes de cada teste."""
        for filename in ["classes.json", "reservations.json"]:
            path = os.path.join(DATA_DIR, filename)
            with open(path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def test_create_class(self):
        success, msg = create_class("Pilates Mat", "15/04/2025", "10:00", 60, "Aula básica", 10, 1)
        self.assertTrue(success)
        classes = list_classes()
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0]["name"], "Pilates Mat")

    def test_cancel_class(self):
        create_class("Pilates", "15/04/2025", "10:00", 60, "", 10, 1)
        classes = list_classes()
        success, msg = cancel_class(classes[0]["id"], 1)
        self.assertTrue(success)
        updated = get_class_by_id(classes[0]["id"])
        self.assertEqual(updated["status"], "cancelado")

    def test_cancel_class_wrong_instructor(self):
        create_class("Pilates", "15/04/2025", "10:00", 60, "", 10, 1)
        classes = list_classes()
        success, msg = cancel_class(classes[0]["id"], 999)
        self.assertFalse(success)

    def test_edit_class(self):
        create_class("Pilates", "15/04/2025", "10:00", 60, "", 10, 1)
        classes = list_classes()
        success, msg = edit_class(classes[0]["id"], 1, name="Pilates Avançado")
        self.assertTrue(success)
        updated = get_class_by_id(classes[0]["id"])
        self.assertEqual(updated["name"], "Pilates Avançado")


if __name__ == "__main__":
    unittest.main()
