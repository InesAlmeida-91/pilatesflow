"""
auth.py - Lógica de login e registo de utilizadores.
"""

from datetime import date
from src.database import load_json, save_json, get_next_id
from src.utils import validate_email, validate_password


def login(email, password):
    """
    Verifica credenciais do utilizador.
    Retorna o utilizador se login for bem-sucedido, None caso contrário.
    """
    users = load_json("users.json")
    for user in users:
        if user["email"] == email and user["password"] == password:
            return user
    return None


def register(name, email, password):
    """
    Regista um novo aluno no sistema.
    Valida email e password, verifica duplicados.
    Retorna (sucesso: bool, mensagem: str).
    """
    if not name or not name.strip():
        return False, "O nome não pode estar vazio."

    if not validate_email(email):
        return False, "Formato de e-mail inválido."

    valid, msg = validate_password(password)
    if not valid:
        return False, msg

    users = load_json("users.json")

    # Verificar se já existe utilizador com este email
    for user in users:
        if user["email"] == email:
            return False, "Já existe um utilizador registado com este e-mail."

    new_user = {
        "id": get_next_id(users),
        "name": name.strip(),
        "email": email.strip(),
        "password": password,
        "type": "STUDENT",
        "created_at": str(date.today())
    }

    users.append(new_user)
    save_json("users.json", users)

    return True, f"Registo efetuado com sucesso! Bem-vindo(a), {new_user['name']}."