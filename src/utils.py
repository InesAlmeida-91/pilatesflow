"""
utils.py - Funções auxiliares (validações, etc.)
"""

import re


def validate_email(email):
    """Verifica se o email cumpre as regras de formato de e-mail."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """
    Valida a password:
    - Mínimo 7 caracteres
    - Pelo menos 1 maiúscula
    - Pelo menos 1 minúscula
    - Pelo menos 1 número
    - Pelo menos 1 carácter especial
    """
    if len(password) < 7:
        return False, "A password deve ter pelo menos 7 caracteres."
    if not re.search(r'[A-Z]', password):
        return False, "A password deve ter pelo menos 1 letra maiúscula."
    if not re.search(r'[a-z]', password):
        return False, "A password deve ter pelo menos 1 letra minúscula."
    if not re.search(r'[0-9]', password):
        return False, "A password deve ter pelo menos 1 número."
    if not re.search(r'[^a-zA-Z0-9]', password):
        return False, "A password deve ter pelo menos 1 carácter especial."
    return True, ""


def to_iso_date(date_str):
    """Converte data de DD/MM/AAAA para AAAA-MM-DD. Devolve sem alterações se já estiver em ISO."""
    if re.match(r'^\d{2}/\d{2}/\d{4}$', date_str):
        day, month, year = date_str.split('/')
        return f"{year}-{month}-{day}"
    return date_str


def from_iso_date(date_str):
    """Converte data de AAAA-MM-DD para DD/MM/AAAA. Devolve sem alterações se já estiver no formato europeu."""
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        year, month, day = date_str.split('-')
        return f"{day}/{month}/{year}"
    return date_str


def validate_datetime(date_str, time_str):
    """Valida formato de data (DD/MM/AAAA) e hora (HH:MM)."""
    date_pattern = r'^\d{2}/\d{2}/\d{4}$'
    time_pattern = r'^\d{2}:\d{2}$'
    
    if not re.match(date_pattern, date_str):
        return False, "Formato de data inválido. Use DD/MM/AAAA."
    if not re.match(time_pattern, time_str):
        return False, "Formato de hora inválido. Use HH:MM."
    
    parts = date_str.split("/")
    day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
    
    if month < 1 or month > 12:
        return False, "Mês inválido."
    if day < 1 or day > 31:
        return False, "Dia inválido."
    
    h_parts = time_str.split(":")
    hour, minute = int(h_parts[0]), int(h_parts[1])
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return False, "Hora inválida."
    
    return True, ""
