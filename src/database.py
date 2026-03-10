"""
Funções de acesso aos ficheiros JSON usados para armazenar dados de aulas, reservas e utilizadores.
Estas funções permitem carregar e guardar dados de forma simples.
"""

import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

def load_json(filename):
    """Carrega dados a partir de um ficheiro JSON na pasta 'data'."""
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
def save_json(filename, data):
    """Guarda dados num ficheiro JSON na pasta 'data'."""
    path = os.path.join(DATA_DIR, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

def get_next_id(data_list):
    """Retorna o próximo ID disponível para uma lista de registos."""
    if not data_list:
        return 1
    return max(item["id"] for item in data_list) + 1