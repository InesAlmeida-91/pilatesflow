"""
Funcionalidades das reservas:
- Listar aulas disponíveis.
- Listar reservas feitas. 
- Reservar aula.
- Cancelar reserva.
"""

from datetime import date
from src.database import load_json, save_json, get_next_id
from src.components.student import can_reserve

def list_available_classes(student_id=None):

    classes = load_json("classes.json")
    reservations = load_json("reservations.json")
    users = load_json("users.json")

    # Mapa de ids de utilizadores para nomes, para evitar múltiplas buscas
    user_map = {u["id"]: u["name"] for u in users}
    
    available_classes = []

    for c in classes:
        if c["status"] != "confirmado":
            continue

        active_count = sum(
            1 for r in reservations
            if r["class_id"] == c["id"] and r["status"] == "confirmado"
        )

        reserved_by_user = False
        if student_id is not None:
            reserved_by_user = any(
                r["class_id"] == c["id"] and r["student_id"] == student_id and r["status"] == "confirmado"
                for r in reservations
            )

        if not reserved_by_user and active_count >= c["max_students"]:
            continue

        available_classes.append({
            **c,
            "enrolled": active_count,
            "spots_left": c["max_students"] - active_count,
            "instructor_name": user_map.get(c["instructor_id"], "Desconhecido"),
            "already_reserved": reserved_by_user
        })

    return available_classes

def list_student_reservations(student_id):
    """Lista as reservas ativas de um aluno, incluindo nome da aula, data e status."""
    reservations = load_json("reservations.json")
    classes = load_json("classes.json")

    # Mapa de ids de aulas para dados, para evitar múltiplas buscas
    class_map = {c["id"]: c for c in classes}

    result = []
    for res in reservations:
        if res["student_id"] == student_id and res["status"] == "confirmado":
            # Obtem os dados da aula associada à reserva
            class_info = class_map.get(res["class_id"])
            
            if class_info:
                """Monta a estrutura da reserva para o frontend, incluindo nome da aula, data e status."""
                result.append({
                    "reservation_id": res["id"],
                    "class_name": class_info["name"],
                    "schedule": class_info["schedule"],
                    "duration": class_info["duration"],
                    "status": res["status"],
                    "reserved_at": res["created_at"]
                })

    return result

def reserve_class(student_id, class_id):
    """
    Reserva uma aula para um aluno, verificando regras de negócio.
    Retorna (sucesso: bool, mensagem: str).
    """
    classes = load_json("classes.json")
    reservations = load_json("reservations.json")

    class_info = next((c for c in classes if c["id"] == class_id), None)
    if not class_info:
        return False, "Aula não encontrada."
    
    is_eligible, msg = can_reserve(class_info, reservations, student_id)
    if not is_eligible:
        return False, msg

    # Cria nova reserva
    new_reservation = {
        "id": get_next_id(reservations),
        "student_id": student_id,
        "class_id": class_id,
        "created_at": str(date.today()),
        "status": "confirmado"
    }

    reservations.append(new_reservation)
    save_json("reservations.json", reservations)

    return True, f"Reserva realizada com sucesso na aula {class_info['name']}."

def cancel_reservation(reservation_id, student_id):
    """Cancela uma reserva, verificando se pertence ao aluno e se já não está cancelada."""
    reservations = load_json("reservations.json")

    reservation = next((r for r in reservations if r["id"] == reservation_id), None)
    if not reservation:
        return False, "Reserva não encontrada."

    is_instructor = reservation["student_id"] == student_id
    if not is_instructor:
        return False, "Você não tem permissão para cancelar esta reserva."

    if reservation["status"] == "cancelado":
        return False, "Esta reserva já está cancelada."

    reservation["status"] = "cancelado"
    save_json("reservations.json", reservations)

    return True, "Reserva cancelada com sucesso."