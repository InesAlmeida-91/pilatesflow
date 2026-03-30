"""
Funcionalidades das aulas:
- Criar aula.
- Editar aula.
- Apagar aula (cancelar).
- Listar aulas.
- Pesquisar.
"""

from datetime import date
from src.database import load_json, save_json, get_next_id
from src.utils import is_schedule_in_past, to_iso_date, validate_future_datetime

def _is_historical_class(class_data):
    return class_data["status"] == "cancelado" or is_schedule_in_past(class_data["schedule"])


def _serialize_class(class_data, history=False):
    serialized = {**class_data}
    if class_data["status"] == "cancelado":
        serialized["display_status"] = "Cancelada"
        serialized["status_variant"] = "danger"
    elif history:
        serialized["display_status"] = "Realizada"
        serialized["status_variant"] = "secondary"
    else:
        serialized["display_status"] = "Confirmada"
        serialized["status_variant"] = "success"
    return serialized


def list_classes(instructor_id=None, history=False):
    """Lista aulas ativas ou históricas. Se instructor_id for dado, filtra por instrutor."""
    classes = load_json("classes.json")
    if instructor_id:
        classes = [cls for cls in classes if cls["instructor_id"] == instructor_id]

    if history:
        classes = [_serialize_class(cls, history=True) for cls in classes if _is_historical_class(cls)]
        return sorted(classes, key=lambda c: c["schedule"], reverse=True)

    classes = [_serialize_class(cls) for cls in classes if not _is_historical_class(cls)]
    return sorted(classes, key=lambda c: c["schedule"])

def create_class(name, schedule_date, schedule_time, duration, description, max_students, instructor_id):
    """
    Cria uma nova aula. 
    Retorna (sucesso: bool, mensagem: str).
    """
    is_valid, msg = validate_future_datetime(schedule_date, schedule_time)
    if not is_valid:
        return False, msg

    classes = load_json("classes.json")

    new_class = {
        "id": get_next_id(classes),
        "name": name.strip(),
        "schedule": f"{to_iso_date(schedule_date)} {schedule_time}",
        "duration": int(duration),
        "description": description.strip() if description else "",
        "status": "confirmado",
        "max_students": int(max_students),
        "instructor_id": instructor_id,
        "created_at": str(date.today())
    }

    classes.append(new_class)
    save_json("classes.json", classes)

    return True, f"Aula '{name}' criada com sucesso (ID: {new_class['id']})."

def edit_class(class_id, instructor_id, **kwargs):
    """
    Edita os dados de uma aula existente.
    Apenas o instrutor que criou a aula pode editá-la.
    Retorna (sucesso: bool, mensagem: str).
    """
    classes = load_json("classes.json")
    reservations = load_json("reservations.json")
    
    editable_class = next((c for c in classes if c["id"] == class_id), None)
    
    if not editable_class:
        return False, "Aula não encontrada."

    if editable_class["instructor_id"] != instructor_id:
        return False, "Não tem permissão para editar esta aula."

    if "max_students" in kwargs:
        try:
            new_limit = int(kwargs["max_students"])
        except (ValueError, TypeError):
            return False, "O limite de alunos deve ser um número válido."
        
        current_enrolled = sum(1 for r in reservations if r["class_id"] == class_id and r["status"] == "confirmado")
        
        if new_limit < current_enrolled:
            return False, f"Não pode reduzir o limite para {new_limit}, pois já existem {current_enrolled} alunos inscritos."
        
        editable_class["max_students"] = new_limit

    editable_fields = ["name", "description", "duration"]
    for field in editable_fields:
        if field in kwargs and kwargs[field]:
            value = kwargs[field]
            
            if isinstance(value, str):
                editable_class[field] = value.strip()
            else:
                editable_class[field] = value

    new_date = kwargs.get("schedule_date")
    new_time = kwargs.get("schedule_time")
    
    if new_date or new_time:
        current_date, current_time = editable_class["schedule"].split(" ")
        final_date = to_iso_date(new_date) if new_date else current_date
        final_time = new_time if new_time else current_time

        is_valid, msg = validate_future_datetime(final_date, final_time)
        if not is_valid:
            return False, msg

        editable_class["schedule"] = f"{final_date} {final_time}"

    save_json("classes.json", classes)
    return True, f"Aula '{editable_class['name']}' editada com sucesso."

def cancel_class(class_id, instructor_id):
    """
    Cancela uma aula (muda o status para 'cancelado'). 
    Apenas o instrutor que criou a aula pode cancelá-la.
    Cancela todas as reservas associadas a esta aula.
    Retorna (sucesso: bool, mensagem: str).
    """
    classes = load_json("classes.json")

    cancelled_class = next((c for c in classes if c["id"] == class_id), None)

    if not cancelled_class:
        return False, "Aula não encontrada."

    if cancelled_class["instructor_id"] != instructor_id:
        return False, "Não tem permissão para cancelar esta aula."
    
    if cancelled_class["status"] == "cancelado":
        return False, "Esta aula já está cancelada."

    cancelled_class["status"] = "cancelado"
    save_json("classes.json", classes)

    reservations = load_json("reservations.json")
    for r in reservations:
        if r["class_id"] == class_id and r["status"] == "confirmado":
            r["status"] = "cancelado"
    save_json("reservations.json", reservations)

    return True, f"Aula '{cancelled_class['name']}' cancelada com sucesso."

def get_class_by_id(class_id):
    """Retorna uma aula pelo seu ID."""
    classes = load_json("classes.json")
    return next((c for c in classes if c["id"] == class_id), None)

def get_enrolled_students(class_id):
    """Retorna a lista de alunos inscritos numa aula."""
    reservations = load_json("reservations.json")
    users = load_json("users.json")

    user_map = {u["id"]: u for u in users}
    active_reservations = [r for r in reservations if r["class_id"] == class_id and r["status"] == "confirmado"]

    students = []
    for res in active_reservations:
        user_data = user_map.get(res["student_id"])
        
        if user_data:
            students.append({
                "id": user_data["id"],
                "name": user_data["name"],
                "email": user_data["email"],
                "reservation_date": res.get("created_at", "N/A")
            })

    return students

def search_reservations(query):
    """
    Pesquisa reservas por nome do aluno ou email de contacto.
    Retorna uma lista de reservas que correspondem ao critério de pesquisa, ordenadas pelo horário da aula.
    """
    reservations = load_json("reservations.json")
    users = load_json("users.json")
    classes = load_json("classes.json")

    query_lower = query.strip().lower()

    class_map = {c["id"]: c for c in classes}
    matching_students = {
        u["id"]: u for u in users 
        if query_lower in u["name"].lower() or query_lower in u["email"].lower()
    }

    results = []

    for res in reservations:
        student = matching_students.get(res["student_id"])
        
        if student:
            class_data = class_map.get(res["class_id"])
            
            if class_data:
                results.append({
                    "reservation_id": res["id"],
                    "student_name": student["name"],
                    "student_email": student["email"],
                    "class_name": class_data["name"],
                    "class_schedule": class_data["schedule"],
                    "status": res["status"]
                })

    return sorted(results, key=lambda x: x["class_schedule"], reverse=True)


def get_instructor_stats(instructor_id):
    """
    Retorna estatísticas do instrutor:
    - total_students: total de alunos inscritos nas aulas ativas
    - active_classes: número de aulas ativas
    - occupancy_rate: taxa de ocupação média (%)
    """
    classes = load_json("classes.json")
    reservations = load_json("reservations.json")

    active_classes = [
        c for c in classes
        if c["instructor_id"] == instructor_id
        and c["status"] != "cancelado"
        and not is_schedule_in_past(c["schedule"])
    ]

    total_students = 0
    total_capacity = 0

    for cls in active_classes:
        enrolled = sum(
            1 for r in reservations
            if r["class_id"] == cls["id"] and r["status"] == "confirmado"
        )
        total_students += enrolled
        total_capacity += cls["max_students"]

    occupancy_rate = round((total_students / total_capacity * 100), 1) if total_capacity > 0 else 0

    return {
        "total_students": total_students,
        "active_classes": len(active_classes),
        "occupancy_rate": occupancy_rate
    }