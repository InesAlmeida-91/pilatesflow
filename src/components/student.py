"""
Regras de negócio relacionadas aos alunos.
"""

def can_reserve(class_data, reservations, student_id):
    """
    Verifica se o aluno pode reservar uma aula.
    """
    if class_data["status"] == "cancelado":
        return False, "A aula foi cancelada."

    # Reservas ativas da aula
    active_reservations = [r for r in reservations if r["class_id"] == class_data["id"] and r["status"] == "confirmado"]

    if len(active_reservations) >= class_data["max_students"]:
        return False, "A aula atingiu o número máximo de alunos."

    # Verifica se o aluno já tem reserva ativa nesta aula
    is_already_registered = any(r["student_id"] == student_id for r in active_reservations)
    if is_already_registered:
        return False, "Já tem uma reserva ativa nesta aula."

    return True, ""