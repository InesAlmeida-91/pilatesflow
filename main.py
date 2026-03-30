"""
main.py - Ponto de entrada da aplicação Flask.
Sistema de gestão de estúdio de Pilates.
"""

import os
import io
import csv
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail, Message
from src.auth import login, register, update_profile, generate_reset_token, verify_reset_token, reset_password
from src.containers.class_service import (
    list_classes, create_class, edit_class, cancel_class,
    get_class_by_id, get_enrolled_students, search_reservations,
    get_instructor_stats
)
from src.containers.reservation_service import (
    list_available_classes, reserve_class, cancel_reservation,
    list_student_reservations, join_waitlist,
    get_student_notifications, mark_notifications_read
)
from src.utils import validate_datetime, from_iso_date, paginate

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback-dev-key")
csrf = CSRFProtect(app)

# Configuração Flask-Mail
app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS", "True").lower() in ("true", "1")
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME", "")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD", "")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@pilates.com")
mail = Mail(app)

@app.template_filter('format_schedule')
def format_schedule_filter(schedule):
    """Converte 'yyyy-mm-dd HH:MM' para 'dd/mm/yyyy HH:MM' para apresentação."""
    if not schedule or ' ' not in schedule:
        return schedule
    date_part, time_part = schedule.split(' ', 1)
    return f"{from_iso_date(date_part)} {time_part}"


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
    email = ""
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

    return render_template("login.html", email=email)


@app.route("/register", methods=["GET", "POST"])
def register_page():
    name = ""
    email = ""
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

    return render_template("register.html", name=name, email=email)


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Sessão terminada com sucesso.", "success")
    return redirect(url_for("login_page"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        from src.database import load_json
        users = load_json("users.json")
        user = next((u for u in users if u["email"] == email), None)

        if user:
            token = generate_reset_token(email, app.secret_key)
            reset_url = url_for("reset_password_page", token=token, _external=True)
            try:
                msg = Message(
                    "Recuperação de Password - Estúdio Pilates",
                    recipients=[email]
                )
                msg.html = f"""
                <h2>Recuperação de Password</h2>
                <p>Olá {user['name']},</p>
                <p>Clique no link abaixo para redefinir a sua password:</p>
                <p><a href="{reset_url}">{reset_url}</a></p>
                <p>Este link é válido por 1 hora.</p>
                <p>Se não solicitou esta recuperação, ignore este e-mail.</p>
                """
                mail.send(msg)
            except Exception:
                # Em desenvolvimento, imprimir o link na consola
                print(f"\n[DEV] Link de recuperação para {email}: {reset_url}\n")

        # Mensagem genérica para não revelar se o e-mail existe
        flash("Se o e-mail existir no sistema, receberá instruções de recuperação.", "success")
        return redirect(url_for("login_page"))

    return render_template("forgot_password.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password_page(token):
    email = verify_reset_token(token, app.secret_key)
    if not email:
        flash("Link de recuperação inválido ou expirado.", "error")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        success, msg = reset_password(email, password)
        flash(msg, "success" if success else "error")
        if success:
            return redirect(url_for("login_page"))

    return render_template("reset_password.html", token=token)


# ═══════════════════════════════════════
#  ROTAS DO INSTRUTOR
# ═══════════════════════════════════════

@app.route("/instructor")
@instructor_required
def instructor_dashboard():
    stats = get_instructor_stats(session["user"]["id"])
    return render_template("instructor/dashboard.html", user=session["user"], stats=stats)


@app.route("/instructor/classes")
@instructor_required
def instructor_list_classes():
    page = request.args.get("page", 1, type=int)
    classes_all = list_classes(instructor_id=session["user"]["id"])
    classes, total_pages, current_page = paginate(classes_all, page, 5)
    return render_template(
        "instructor/list_classes.html",
        classes=classes,
        user=session["user"],
        page_title="Minhas Aulas",
        history_mode=False,
        empty_message="Não tem aulas ativas. Crie uma nova aula para começar.",
        page_endpoint="instructor_list_classes",
        total_pages=total_pages,
        current_page=current_page
    )


@app.route("/instructor/classes/history")
@instructor_required
def instructor_class_history():
    page = request.args.get("page", 1, type=int)
    classes_all = list_classes(instructor_id=session["user"]["id"], history=True)
    classes, total_pages, current_page = paginate(classes_all, page, 5)
    return render_template(
        "instructor/list_classes.html",
        classes=classes,
        user=session["user"],
        page_title="Histórico de Aulas",
        history_mode=True,
        empty_message="Ainda não existem aulas passadas ou canceladas.",
        page_endpoint="instructor_class_history",
        total_pages=total_pages,
        current_page=current_page
    )


@app.route("/instructor/classes/create", methods=["GET", "POST"])
@instructor_required
def instructor_create_class():
    form_data = {}
    if request.method == "POST":
        form_data = {
            "name": request.form.get("name", ""),
            "schedule_date": request.form.get("schedule_date", ""),
            "schedule_time": request.form.get("schedule_time", ""),
            "duration": request.form.get("duration", "60"),
            "description": request.form.get("description", ""),
            "max_students": request.form.get("max_students", "10"),
        }

        valid, msg = validate_datetime(form_data["schedule_date"], form_data["schedule_time"])
        if not valid:
            flash(msg, "error")
            return render_template("instructor/create_class.html", user=session["user"], form_data=form_data)

        if not form_data["name"].strip():
            flash("O nome da aula não pode estar vazio.", "error")
            return render_template("instructor/create_class.html", user=session["user"], form_data=form_data)

        success, msg = create_class(
            form_data["name"], form_data["schedule_date"], form_data["schedule_time"],
            form_data["duration"], form_data["description"], form_data["max_students"],
            session["user"]["id"]
        )
        flash(msg, "success" if success else "error")
        if success:
            return redirect(url_for("instructor_list_classes"))

    return render_template("instructor/create_class.html", user=session["user"], form_data=form_data)


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
        class_data.update(kwargs)

        if kwargs["schedule_date"] and kwargs["schedule_time"]:
            valid, msg = validate_datetime(kwargs["schedule_date"], kwargs["schedule_time"])
            if not valid:
                flash(msg, "error")
                return render_template("instructor/edit_class.html", class_data=class_data, user=session["user"])

        success, msg = edit_class(class_id, session["user"]["id"], **kwargs)
        flash(msg, "success" if success else "error")
        if success:
            return redirect(url_for("instructor_list_classes"))
    else:
        # Separar schedule em data e hora para o formulário
        schedule_parts = class_data.get("schedule", " ").split(" ")
        class_data["schedule_date"] = from_iso_date(schedule_parts[0]) if len(schedule_parts) > 0 else ""
        class_data["schedule_time"] = schedule_parts[1] if len(schedule_parts) > 1 else ""

    return render_template("instructor/edit_class.html", class_data=class_data, user=session["user"])


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
    return render_template("instructor/class_students.html", class_data=class_data, students=students, user=session["user"])


@app.route("/instructor/classes/<int:class_id>/students/export")
@instructor_required
def instructor_export_students(class_id):
    class_data = get_class_by_id(class_id)
    if not class_data:
        flash("Aula não encontrada.", "error")
        return redirect(url_for("instructor_list_classes"))

    students = get_enrolled_students(class_id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Nome", "E-mail", "Data da Reserva"])
    for s in students:
        writer.writerow([s["id"], s["name"], s["email"], s["reservation_date"]])

    filename = f"alunos_{class_data['name'].replace(' ', '_')}_{class_id}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


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

    return render_template("instructor/search.html", results=results, query=query, user=session["user"])


# ═══════════════════════════════════════
#  ROTAS DO ALUNO
# ═══════════════════════════════════════

@app.route("/student")
@student_required
def student_dashboard():
    notifications = get_student_notifications(session["user"]["id"])
    return render_template("student/dashboard.html", user=session["user"], notifications=notifications)


@app.route("/student/classes")
@student_required
def student_available_classes():
    page = request.args.get("page", 1, type=int)
    filter_name = request.args.get("name", "").strip()
    filter_date = request.args.get("date", "").strip()
    filter_instructor = request.args.get("instructor", "").strip()

    # Converter data DD/MM/YYYY para ISO se necessário
    iso_date = None
    if filter_date:
        from src.utils import to_iso_date
        iso_date = to_iso_date(filter_date)

    classes_all = list_available_classes(
        session["user"]["id"],
        filter_name=filter_name or None,
        filter_date=iso_date or None,
        filter_instructor=filter_instructor or None
    )
    classes, total_pages, current_page = paginate(classes_all, page, 5)
    return render_template(
        "student/available_classes.html",
        classes=classes,
        user=session["user"],
        total_pages=total_pages,
        current_page=current_page,
        filter_name=filter_name,
        filter_date=filter_date,
        filter_instructor=filter_instructor
    )


@app.route("/student/reserve/<int:class_id>", methods=["POST"])
@student_required
def student_reserve(class_id):
    success, msg = reserve_class(session["user"]["id"], class_id)
    flash(msg, "success" if success else "error")
    return redirect(url_for("student_available_classes"))


@app.route("/student/waitlist/<int:class_id>", methods=["POST"])
@student_required
def student_join_waitlist(class_id):
    success, msg = join_waitlist(session["user"]["id"], class_id)
    flash(msg, "success" if success else "error")
    return redirect(url_for("student_available_classes"))


@app.route("/student/notifications/read", methods=["POST"])
@student_required
def student_dismiss_notifications():
    mark_notifications_read(session["user"]["id"])
    return redirect(url_for("student_dashboard"))


@app.route("/student/reservations")
@student_required
def student_reservations():
    page = request.args.get("page", 1, type=int)
    reservations_all = list_student_reservations(session["user"]["id"])
    reservations, total_pages, current_page = paginate(reservations_all, page, 5)
    return render_template(
        "student/reservations.html",
        reservations=reservations,
        user=session["user"],
        page_title="Minhas Reservas",
        history_mode=False,
        empty_message="Ainda não tem reservas ativas.",
        page_endpoint="student_reservations",
        total_pages=total_pages,
        current_page=current_page
    )


@app.route("/student/reservations/history")
@student_required
def student_reservations_history():
    page = request.args.get("page", 1, type=int)
    reservations_all = list_student_reservations(session["user"]["id"], history=True)
    reservations, total_pages, current_page = paginate(reservations_all, page, 5)
    return render_template(
        "student/reservations.html",
        reservations=reservations,
        user=session["user"],
        page_title="Histórico de Reservas",
        history_mode=True,
        empty_message="Ainda não existem reservas passadas ou canceladas.",
        page_endpoint="student_reservations_history",
        total_pages=total_pages,
        current_page=current_page
    )


@app.route("/student/reservations/<int:reservation_id>/cancel", methods=["POST"])
@student_required
def student_cancel_reservation(reservation_id):
    success, msg = cancel_reservation(reservation_id, session["user"]["id"])
    flash(msg, "success" if success else "error")
    return redirect(url_for("student_reservations"))


# ═══════════════════════════════════════
#  PERFIL DE UTILIZADOR
# ═══════════════════════════════════════

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        name = request.form.get("name", "")
        email = request.form.get("email", "")
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")

        success, msg, updated_user = update_profile(
            session["user"]["id"], name, email, current_password, new_password
        )
        flash(msg, "success" if success else "error")
        if success:
            session["user"] = updated_user

    return render_template("profile.html", user=session["user"])


# ═══════════════════════════════════════
if __name__ == "__main__":
    app.run(debug=True, port=5000)
