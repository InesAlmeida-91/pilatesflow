"""
test_aulas.py - Testes unitários para gestão de aulas.
"""

import unittest
import os
import json
import tempfile
from unittest.mock import patch
from src.containers.class_service import create_class, list_classes, cancel_class, edit_class, get_class_by_id


class TestClasses(unittest.TestCase):

    def setUp(self):
        """Usa directório temporário para não afectar os dados reais."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.patcher = patch('src.database.DATA_DIR', self.temp_dir.name)
        self.patcher.start()
        for filename in ["classes.json", "reservations.json"]:
            path = os.path.join(self.temp_dir.name, filename)
            with open(path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def tearDown(self):
        self.patcher.stop()
        self.temp_dir.cleanup()

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
