"""
main.py - Ponto de entrada da aplicação Flask.
Sistema de gestão de estúdio de Pilates.
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
from src.auth import login, register
from src.containers.aulas_service import (
    list_classes, create_class, edit_class, cancel_class,
    get_class_by_id, get_enrolled_students, search_reservations
)
from src.containers.reservas_service import (
    list_available_classes, reserve_class, cancel_reservation,
    list_student_reservations
)
from src.utils import validate_datetime

app = Flask(__name__)
app.secret_key = "pilates_studio_secret_key_2025"


# ─── Decorador para verificar login ───
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            flash("Por favor, faça login primeiro.", "error")
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated


def instructor_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session or session["user"]["type"] != "INSTRUCTOR":
            flash("Acesso restrito a instrutores.", "error")
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated


def student_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session or session["user"]["type"] != "STUDENT":
            flash("Acesso restrito a alunos.", "error")
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated


# ═══════════════════════════════════════
#  ROTAS PÚBLICAS
# ═══════════════════════════════════════

@app.route("/")
def index():
    if "user" in session:
        if session["user"]["type"] == "INSTRUCTOR":
            return redirect(url_for("instructor_dashboard"))
        return redirect(url_for("student_dashboard"))
    return redirect(url_for("login_page"))


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = login(email, password)
        if user:
            session["user"] = user
            flash(f"Bem-vindo(a), {user['name']}!", "success")
            if user["type"] == "INSTRUCTOR":
                return redirect(url_for("instructor_dashboard"))
            return redirect(url_for("student_dashboard"))
        else:
            flash("Credenciais inválidas. Verifique o e-mail e a password.", "error")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "POST":
        name = request.form.get("name", "")
        email = request.form.get("email", "")
        password = request.form.get("password", "")

        success, msg = register(name, email, password)
        if success:
            flash(msg, "success")
            return redirect(url_for("login_page"))
        else:
            flash(msg, "error")

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Sessão terminada com sucesso.", "success")
    return redirect(url_for("login_page"))


# ═══════════════════════════════════════
#  ROTAS DO INSTRUTOR
# ═══════════════════════════════════════

@app.route("/instructor")
@instructor_required
def instructor_dashboard():
    return render_template("instructor/dashboard.html", user=session["user"])


@app.route("/instructor/classes")
@instructor_required
def instructor_list_classes():
    classes = list_classes(instructor_id=session["user"]["id"])
    return render_template("instructor/list_classes.html", classes=classes, user=session["user"])


@app.route("/instructor/classes/create", methods=["GET", "POST"])
@instructor_required
def instructor_create_class():
    if request.method == "POST":
        name = request.form.get("name", "")
        schedule_date = request.form.get("schedule_date", "")
        schedule_time = request.form.get("schedule_time", "")
        duration = request.form.get("duration", "60")
        description = request.form.get("description", "")
        max_students = request.form.get("max_students", "10")

        valid, msg = validate_datetime(schedule_date, schedule_time)
        if not valid:
            flash(msg, "error")
            return render_template("instructor/create_class.html", user=session["user"])

        if not name.strip():
            flash("O nome da aula não pode estar vazio.", "error")
            return render_template("instructor/create_class.html", user=session["user"])

        success, msg = create_class(
            name, schedule_date, schedule_time,
            duration, description, max_students,
            session["user"]["id"]
        )
        flash(msg, "success" if success else "error")
        if success:
            return redirect(url_for("instructor_list_classes"))

    return render_template("instructor/create_class.html", user=session["user"])


@app.route("/instructor/classes/<int:class_id>/edit", methods=["GET", "POST"])
@instructor_required
def instructor_edit_class(class_id):
    class_data = get_class_by_id(class_id)
    if not class_data:
        flash("Aula não encontrada.", "error")
        return redirect(url_for("instructor_list_classes"))

    if request.method == "POST":
        kwargs = {
            "name": request.form.get("name", ""),
            "schedule_date": request.form.get("schedule_date", ""),
            "schedule_time": request.form.get("schedule_time", ""),
            "duration": request.form.get("duration", ""),
            "description": request.form.get("description", ""),
            "max_students": request.form.get("max_students", ""),
        }

        if kwargs["schedule_date"] and kwargs["schedule_time"]:
            valid, msg = validate_datetime(kwargs["schedule_date"], kwargs["schedule_time"])
            if not valid:
                flash(msg, "error")
                return render_template("instructor/edit_class.html",
                                       class_data=class_data, user=session["user"])

        success, msg = edit_class(class_id, session["user"]["id"], **kwargs)
        flash(msg, "success" if success else "error")
        if success:
            return redirect(url_for("instructor_list_classes"))

    # Separar schedule em data e hora para o formulário
    schedule_parts = class_data.get("schedule", " ").split(" ")
    class_data["schedule_date"] = schedule_parts[0] if len(schedule_parts) > 0 else ""
    class_data["schedule_time"] = schedule_parts[1] if len(schedule_parts) > 1 else ""

    return render_template("instructor/edit_class.html",
                           class_data=class_data, user=session["user"])


@app.route("/instructor/classes/<int:class_id>/cancel", methods=["POST"])
@instructor_required
def instructor_cancel_class(class_id):
    success, msg = cancel_class(class_id, session["user"]["id"])
    flash(msg, "success" if success else "error")
    return redirect(url_for("instructor_list_classes"))


@app.route("/instructor/classes/<int:class_id>/students")
@instructor_required
def instructor_class_students(class_id):
    class_data = get_class_by_id(class_id)
    if not class_data:
        flash("Aula não encontrada.", "error")
        return redirect(url_for("instructor_list_classes"))

    students = get_enrolled_students(class_id)
    return render_template("instructor/class_students.html",
                           class_data=class_data, students=students, user=session["user"])


@app.route("/instructor/search", methods=["GET", "POST"])
@instructor_required
def instructor_search():
    results = []
    query = ""
    if request.method == "POST":
        query = request.form.get("query", "")
        if query.strip():
            results = search_reservations(query)
        else:
            flash("Introduza um termo de pesquisa.", "error")

    return render_template("instructor/search.html",
                           results=results, query=query, user=session["user"])


# ═══════════════════════════════════════
#  ROTAS DO ALUNO
# ═══════════════════════════════════════

@app.route("/student")
@student_required
def student_dashboard():
    return render_template("student/dashboard.html", user=session["user"])


@app.route("/student/classes")
@student_required
def student_available_classes():
    classes = list_available_classes()
    return render_template("student/available_classes.html",
                           classes=classes, user=session["user"])


@app.route("/student/reserve/<int:class_id>", methods=["POST"])
@student_required
def student_reserve(class_id):
    success, msg = reserve_class(session["user"]["id"], class_id)
    flash(msg, "success" if success else "error")
    return redirect(url_for("student_available_classes"))


@app.route("/student/reservations")
@student_required
def student_reservations():
    reservations = list_student_reservations(session["user"]["id"])
    return render_template("student/reservations.html",
                           reservations=reservations, user=session["user"])


@app.route("/student/reservations/<int:reservation_id>/cancel", methods=["POST"])
@student_required
def student_cancel_reservation(reservation_id):
    success, msg = cancel_reservation(reservation_id, session["user"]["id"])
    flash(msg, "success" if success else "error")
    return redirect(url_for("student_reservations"))


# ═══════════════════════════════════════
if __name__ == "__main__":
    app.run(debug=True, port=5000)
