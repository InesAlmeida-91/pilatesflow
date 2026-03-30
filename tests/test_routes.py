"""
test_routes.py - Testes de integração das rotas Flask.
"""

import unittest
import os
import json
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch
from werkzeug.security import generate_password_hash


class TestRoutes(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.patcher = patch('src.database.DATA_DIR', self.temp_dir.name)
        self.patcher.start()

        # Criar dados de teste
        users = [
            {
                "id": 1,
                "name": "Instrutor",
                "email": "i@t.com",
                "password": generate_password_hash("Test123!"),
                "type": "INSTRUCTOR",
                "created_at": "2025-01-01"
            },
            {
                "id": 2,
                "name": "Aluno",
                "email": "a@t.com",
                "password": generate_password_hash("Test123!"),
                "type": "STUDENT",
                "created_at": "2025-01-01"
            },
        ]
        future = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        classes = [
            {
                "id": 1,
                "name": "Aula Teste",
                "schedule": f"{future} 10:00",
                "duration": 60,
                "description": "Teste",
                "status": "confirmado",
                "max_students": 2,
                "instructor_id": 1,
                "created_at": "2025-01-01"
            }
        ]

        for filename, data in [
            ("users.json", users),
            ("classes.json", classes),
            ("reservations.json", []),
            ("waitlist.json", []),
            ("notifications.json", []),
        ]:
            path = os.path.join(self.temp_dir.name, filename)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)

        from main import app
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.app = app
        self.client = app.test_client()

    def tearDown(self):
        self.patcher.stop()
        self.temp_dir.cleanup()

    def _login(self, email="i@t.com", password="Test123!"):
        return self.client.post("/login", data={"email": email, "password": password}, follow_redirects=True)

    # ── Rotas públicas ──
    def test_index_redirects_to_login(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 302)

    def test_login_page_get(self):
        resp = self.client.get("/login")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Login", resp.data)

    def test_register_page_get(self):
        resp = self.client.get("/register")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Registo", resp.data)

    def test_login_post_success_instructor(self):
        resp = self._login("i@t.com", "Test123!")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Instrutor", resp.data.decode())

    def test_login_post_success_student(self):
        resp = self._login("a@t.com", "Test123!")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Aluno", resp.data.decode())

    def test_login_post_fail(self):
        resp = self.client.post("/login", data={"email": "x@x.com", "password": "wrong"}, follow_redirects=True)
        self.assertIn("inv\u00e1lidas", resp.data.decode())

    def test_register_post_success(self):
        resp = self.client.post("/register", data={
            "name": "Novo", "email": "novo@t.com", "password": "Novo123!"
        }, follow_redirects=True)
        self.assertIn("sucesso", resp.data.decode())

    def test_register_post_duplicate(self):
        resp = self.client.post("/register", data={
            "name": "Dup", "email": "a@t.com", "password": "Test123!"
        }, follow_redirects=True)
        self.assertIn("e-mail", resp.data.decode())

    def test_logout(self):
        self._login()
        resp = self.client.get("/logout", follow_redirects=True)
        self.assertIn(b"Login", resp.data)

    # ── Rotas protegidas sem login ──
    def test_instructor_dashboard_requires_login(self):
        resp = self.client.get("/instructor")
        self.assertEqual(resp.status_code, 302)

    def test_student_dashboard_requires_login(self):
        resp = self.client.get("/student")
        self.assertEqual(resp.status_code, 302)

    def test_profile_requires_login(self):
        resp = self.client.get("/profile")
        self.assertEqual(resp.status_code, 302)

    # ── Rotas do instrutor ──
    def test_instructor_dashboard(self):
        self._login("i@t.com")
        resp = self.client.get("/instructor")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Dashboard", resp.data.decode())

    def test_instructor_list_classes(self):
        self._login("i@t.com")
        resp = self.client.get("/instructor/classes")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Aula Teste", resp.data.decode())

    def test_instructor_create_class(self):
        self._login("i@t.com")
        future = (datetime.now() + timedelta(days=10)).strftime("%d/%m/%Y")
        resp = self.client.post("/instructor/classes/create", data={
            "name": "Nova Aula",
            "schedule_date": future,
            "schedule_time": "14:00",
            "duration": "45",
            "description": "Teste",
            "max_students": "8"
        }, follow_redirects=True)
        self.assertIn("sucesso", resp.data.decode())

    def test_instructor_cancel_class(self):
        self._login("i@t.com")
        resp = self.client.post("/instructor/classes/1/cancel", follow_redirects=True)
        self.assertIn("cancelada", resp.data.decode())

    def test_instructor_class_students(self):
        self._login("i@t.com")
        resp = self.client.get("/instructor/classes/1/students")
        self.assertEqual(resp.status_code, 200)

    def test_instructor_export_csv(self):
        self._login("i@t.com")
        resp = self.client.get("/instructor/classes/1/students/export")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/csv", resp.content_type)

    def test_instructor_search(self):
        self._login("i@t.com")
        resp = self.client.post("/instructor/search", data={"query": "Aluno"}, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

    # ── Rotas do aluno ──
    def test_student_dashboard(self):
        self._login("a@t.com")
        resp = self.client.get("/student")
        self.assertEqual(resp.status_code, 200)

    def test_student_available_classes(self):
        self._login("a@t.com")
        resp = self.client.get("/student/classes")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Aula Teste", resp.data.decode())

    def test_student_available_classes_filter_name(self):
        self._login("a@t.com")
        resp = self.client.get("/student/classes?name=Teste")
        self.assertIn("Aula Teste", resp.data.decode())

    def test_student_available_classes_filter_no_match(self):
        self._login("a@t.com")
        resp = self.client.get("/student/classes?name=Inexistente")
        self.assertNotIn("Aula Teste", resp.data.decode())

    def test_student_reserve_class(self):
        self._login("a@t.com")
        resp = self.client.post("/student/reserve/1", follow_redirects=True)
        self.assertIn("sucesso", resp.data.decode())

    def test_student_reservations(self):
        self._login("a@t.com")
        self.client.post("/student/reserve/1")
        resp = self.client.get("/student/reservations")
        self.assertEqual(resp.status_code, 200)

    def test_student_cancel_reservation(self):
        self._login("a@t.com")
        self.client.post("/student/reserve/1")
        resp = self.client.post("/student/reservations/1/cancel", follow_redirects=True)
        self.assertIn("cancelada", resp.data.decode())

    # ── Waitlist ──
    def test_student_join_waitlist(self):
        self._login("a@t.com")
        # Encher a aula (max 2)
        from src.containers.reservation_service import reserve_class
        reserve_class(2, 1)  # aluno 2
        # Adicionar outro aluno manualmente
        from src.database import load_json, save_json
        res = load_json("reservations.json")
        res.append({"id": 99, "student_id": 99, "class_id": 1, "created_at": "2025-01-01", "status": "confirmado"})
        save_json("reservations.json", res)

        # Registar novo aluno e tentar lista de espera
        self.client.get("/logout")
        self.client.post("/register", data={"name": "Espera", "email": "e@t.com", "password": "Espera1!"})
        self._login("e@t.com", "Espera1!")
        resp = self.client.post("/student/waitlist/1", follow_redirects=True)
        self.assertIn("lista de espera", resp.data.decode())

    # ── Perfil ──
    def test_profile_page(self):
        self._login("a@t.com")
        resp = self.client.get("/profile")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Perfil", resp.data.decode())

    def test_profile_update_name(self):
        self._login("a@t.com")
        resp = self.client.post("/profile", data={
            "name": "Novo Nome", "email": "a@t.com", "current_password": "", "new_password": ""
        }, follow_redirects=True)
        self.assertIn("sucesso", resp.data.decode())

    # ── Recuperação de password ──
    def test_forgot_password_page(self):
        resp = self.client.get("/forgot-password")
        self.assertEqual(resp.status_code, 200)

    def test_forgot_password_post(self):
        resp = self.client.post("/forgot-password", data={"email": "a@t.com"}, follow_redirects=True)
        self.assertIn("instru", resp.data.decode())

    def test_reset_password_invalid_token(self):
        resp = self.client.get("/reset-password/bad-token", follow_redirects=True)
        self.assertIn("inv\u00e1lido", resp.data.decode())

    # ── Acesso cruzado ──
    def test_student_cannot_access_instructor_routes(self):
        self._login("a@t.com")
        resp = self.client.get("/instructor", follow_redirects=True)
        self.assertIn("restrito", resp.data.decode())

    def test_instructor_cannot_access_student_routes(self):
        self._login("i@t.com")
        resp = self.client.get("/student", follow_redirects=True)
        self.assertIn("restrito", resp.data.decode())


if __name__ == "__main__":
    unittest.main()
