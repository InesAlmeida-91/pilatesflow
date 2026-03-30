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
from src.utils import is_schedule_in_past


def _is_historical_reservation(reservation, class_info):
    if reservation["status"] == "cancelado":
        return True
    if class_info["status"] == "cancelado":
        return True
    return is_schedule_in_past(class_info["schedule"])


def _serialize_reservation(reservation, class_info, history=False):
    is_cancelled = reservation["status"] == "cancelado" or class_info["status"] == "cancelado"
    if is_cancelled:
        display_status = "Cancelada"
        status_variant = "danger"
    elif history:
        display_status = "Realizada"
        status_variant = "secondary"
    else:
        display_status = "Confirmada"
        status_variant = "success"

    return {
        "reservation_id": reservation["id"],
        "class_name": class_info["name"],
        "schedule": class_info["schedule"],
        "duration": class_info["duration"],
        "status": reservation["status"],
        "display_status": display_status,
        "status_variant": status_variant,
        "reserved_at": reservation["created_at"]
    }

def list_available_classes(student_id=None, filter_name=None, filter_date=None, filter_instructor=None):

    classes = load_json("classes.json")
    reservations = load_json("reservations.json")
    users = load_json("users.json")
    waitlist = load_json("waitlist.json")

    # Mapa de ids de utilizadores para nomes, para evitar múltiplas buscas
    user_map = {u["id"]: u["name"] for u in users}
    
    available_classes = []

    for c in classes:
        if c["status"] != "confirmado":
            continue
        if is_schedule_in_past(c["schedule"]):
            continue

        # Filtros
        if filter_name and filter_name.lower() not in c["name"].lower():
            continue
        if filter_date:
            class_date = c["schedule"].split(" ")[0]  # YYYY-MM-DD
            if class_date != filter_date:
                continue
        if filter_instructor:
            instructor_name = user_map.get(c["instructor_id"], "")
            if filter_instructor.lower() not in instructor_name.lower():
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

        # Verificar se o aluno já está na lista de espera
        on_waitlist = False
        if student_id is not None:
            on_waitlist = any(
                w["class_id"] == c["id"] and w["student_id"] == student_id
                for w in waitlist
            )

        available_classes.append({
            **c,
            "enrolled": active_count,
            "spots_left": c["max_students"] - active_count,
            "instructor_name": user_map.get(c["instructor_id"], "Desconhecido"),
            "already_reserved": reserved_by_user,
            "on_waitlist": on_waitlist
        })

    return sorted(available_classes, key=lambda c: c["schedule"])

def list_student_reservations(student_id, history=False):
    """Lista as reservas ativas ou históricas de um aluno."""
    reservations = load_json("reservations.json")
    classes = load_json("classes.json")

    # Mapa de ids de aulas para dados, para evitar múltiplas buscas
    class_map = {c["id"]: c for c in classes}

    result = []
    for res in reservations:
        if res["student_id"] != student_id:
            continue

        class_info = class_map.get(res["class_id"])
        if not class_info:
            continue

        is_history_item = _is_historical_reservation(res, class_info)
        if history != is_history_item:
            continue

        result.append(_serialize_reservation(res, class_info, history=history))

    return sorted(result, key=lambda r: r["schedule"], reverse=history)

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

    is_owner = reservation["student_id"] == student_id
    if not is_owner:
        return False, "Você não tem permissão para cancelar esta reserva."

    if reservation["status"] == "cancelado":
        return False, "Esta reserva já está cancelada."

    reservation["status"] = "cancelado"
    save_json("reservations.json", reservations)

    # Notificar o próximo aluno na lista de espera
    _notify_next_waitlisted(reservation["class_id"])

    return True, "Reserva cancelada com sucesso."


def join_waitlist(student_id, class_id):
    """Adiciona um aluno à lista de espera de uma aula cheia."""
    classes = load_json("classes.json")
    class_info = next((c for c in classes if c["id"] == class_id), None)
    if not class_info:
        return False, "Aula não encontrada."

    waitlist = load_json("waitlist.json")

    already_on = any(w["student_id"] == student_id and w["class_id"] == class_id for w in waitlist)
    if already_on:
        return False, "Já está na lista de espera desta aula."

    waitlist.append({
        "id": get_next_id(waitlist),
        "student_id": student_id,
        "class_id": class_id,
        "created_at": str(date.today())
    })
    save_json("waitlist.json", waitlist)

    return True, f"Adicionado à lista de espera da aula '{class_info['name']}'."


def _notify_next_waitlisted(class_id):
    """Quando uma vaga abre, notifica o próximo aluno na lista de espera."""
    waitlist = load_json("waitlist.json")
    candidates = [w for w in waitlist if w["class_id"] == class_id]
    if not candidates:
        return

    # Ordenar por data de entrada (FIFO)
    candidates.sort(key=lambda w: w["created_at"])
    next_student = candidates[0]

    # Criar notificação
    classes = load_json("classes.json")
    class_info = next((c for c in classes if c["id"] == class_id), None)
    class_name = class_info["name"] if class_info else "Aula"

    notifications = load_json("notifications.json")
    notifications.append({
        "id": get_next_id(notifications),
        "student_id": next_student["student_id"],
        "message": f"Abriu uma vaga na aula '{class_name}'! Reserve já o seu lugar.",
        "class_id": class_id,
        "read": False,
        "created_at": str(date.today())
    })
    save_json("notifications.json", notifications)

    # Remover da lista de espera
    waitlist = [w for w in waitlist if w["id"] != next_student["id"]]
    save_json("waitlist.json", waitlist)


def get_student_notifications(student_id):
    """Retorna notificações não lidas de um aluno."""
    notifications = load_json("notifications.json")
    return [n for n in notifications if n["student_id"] == student_id and not n["read"]]


def mark_notifications_read(student_id):
    """Marca todas as notificações de um aluno como lidas."""
    notifications = load_json("notifications.json")
    changed = False
    for n in notifications:
        if n["student_id"] == student_id and not n["read"]:
            n["read"] = True
            changed = True
    if changed:
        save_json("notifications.json", notifications)