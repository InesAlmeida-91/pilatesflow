"""
auth.py - Lógica de login e registo de utilizadores.
"""

from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from src.database import load_json, save_json, get_next_id
from src.utils import validate_email, validate_password


def login(email, password):
    """
    Verifica credenciais do utilizador.
    Retorna o utilizador se login for bem-sucedido, None caso contrário.
    """
    users = load_json("users.json")
    for user in users:
        if user["email"] == email and check_password_hash(user["password"], password):
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
        "password": generate_password_hash(password),
        "type": "STUDENT",
        "created_at": str(date.today())
    }

    users.append(new_user)
    save_json("users.json", users)

    return True, f"Registo efetuado com sucesso! Bem-vindo(a), {new_user['name']}."


def update_profile(user_id, name, email, current_password, new_password):
    """
    Atualiza o perfil de um utilizador (nome, email e/ou password).
    Retorna (sucesso: bool, mensagem: str, utilizador_atualizado: dict|None).
    """
    users = load_json("users.json")
    user = next((u for u in users if u["id"] == user_id), None)

    if not user:
        return False, "Utilizador não encontrado.", None

    if name and name.strip():
        user["name"] = name.strip()

    if email and email.strip():
        if not validate_email(email):
            return False, "Formato de e-mail inválido.", None
        existing = next((u for u in users if u["email"] == email.strip() and u["id"] != user_id), None)
        if existing:
            return False, "Já existe outro utilizador com este e-mail.", None
        user["email"] = email.strip()

    if new_password:
        if not current_password:
            return False, "Introduza a password atual para definir uma nova.", None
        if not check_password_hash(user["password"], current_password):
            return False, "A password atual está incorreta.", None
        valid, msg = validate_password(new_password)
        if not valid:
            return False, msg, None
        user["password"] = generate_password_hash(new_password)

    save_json("users.json", users)
    return True, "Perfil atualizado com sucesso.", user


def generate_reset_token(email, secret_key):
    """Gera um token seguro para recuperação de password."""
    s = URLSafeTimedSerializer(secret_key)
    return s.dumps(email, salt="password-reset")


def verify_reset_token(token, secret_key, max_age=3600):
    """Verifica o token de recuperação (válido por 1 hora por defeito). Retorna o email ou None."""
    s = URLSafeTimedSerializer(secret_key)
    try:
        email = s.loads(token, salt="password-reset", max_age=max_age)
    except Exception:
        return None
    return email


def reset_password(email, new_password):
    """Redefine a password de um utilizador a partir do email."""
    valid, msg = validate_password(new_password)
    if not valid:
        return False, msg

    users = load_json("users.json")
    user = next((u for u in users if u["email"] == email), None)
    if not user:
        return False, "Utilizador não encontrado."

    user["password"] = generate_password_hash(new_password)
    save_json("users.json", users)
    return True, "Password redefinida com sucesso."