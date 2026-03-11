"""
Regras de negócio relacionadas aos instrutores.
"""

def can_manage_class(user, class_data):
    """Verifica se o instrutor é dono da aula."""
    return user["type"] == "INSTRUCTOR" and class_data["instructor_id"] == user["id"]