"""
Sistema de teste das funcionalidades do PilatesFlow
Menu interativo para testar operações de aulas e reservas no terminal
"""

from src.containers.class_service import (
    create_class, list_classes, edit_class, cancel_class, 
    get_class_by_id, get_enrolled_students
)
from src.containers.reservation_service import (
    list_available_classes, list_student_reservations, 
    reserve_class, cancel_reservation
)
from src.database import load_json, save_json

# Utilizadores de teste
TEST_INSTRUCTOR_ID = 1
TEST_STUDENT_ID = 2
TEST_INSTRUCTOR_NAME = "Instrutor 1"
TEST_STUDENT_NAME = "Aluno 1"


def print_menu(user_type=None):
    """Exibe o menu principal ou menu do utilizador autenticado."""
    print("\n" + "="*50)
    print("🧘 BEM-VINDO AO PILATESFLOW - MENU DE TESTES".center(50))
    print("="*50 + "\n")
    
    if not user_type:
        print("1. Aceder como Instrutor")
        print("2. Aceder como Aluno")
        print("0. Sair")
    elif user_type == "INSTRUCTOR":
        print(f"👨‍🏫 Utilizador: {TEST_INSTRUCTOR_NAME}\n")
        print("--- GESTÃO DE AULAS ---")
        print("1. Criar aula")
        print("2. Listar minhas aulas")
        print("3. Editar aula")
        print("4. Cancelar aula")
        print("5. Ver alunos inscritos numa aula")
        print("0. Sair")
    elif user_type == "STUDENT":
        print(f"👩‍🎓 Utilizador: {TEST_STUDENT_NAME}\n")
        print("--- RESERVAS ---")
        print("1. Listar aulas disponíveis")
        print("2. Reservar aula")
        print("3. Minhas reservas")
        print("4. Cancelar reserva")
        print("0. Sair")
    
    print()


def test_instrutor():
    """Menu para testar funcionalidades de instrutor."""
    while True:
        print_menu("INSTRUCTOR")
        opcao = input("Escolha uma opção: ").strip()
        
        if opcao == "1":
            criar_aula()
        elif opcao == "2":
            listar_minhas_aulas()
        elif opcao == "3":
            editar_aula()
        elif opcao == "4":
            cancelar_aula()
        elif opcao == "5":
            ver_alunos_inscritos()
        elif opcao == "0":
            print("\nEncerrando...")
            break
        else:
            print("❌ Opção inválida!")


def test_aluno():
    """Menu para testar funcionalidades de aluno."""
    while True:
        print_menu("STUDENT")
        opcao = input("Escolha uma opção: ").strip()
        
        if opcao == "1":
            listar_aulas_disponiveis()
        elif opcao == "2":
            reservar_aula()
        elif opcao == "3":
            listar_minhas_reservas()
        elif opcao == "4":
            cancelar_reserva()
        elif opcao == "0":
            print("\nEncerrando...")
            break
        else:
            print("❌ Opção inválida!")


# ============ FUNCIONALIDADES DO INSTRUTOR ============

def criar_aula():
    """Cria uma nova aula."""
    print("\n📝 CRIAR AULA")
    print("-" * 40)
    
    nome = input("Nome da aula: ").strip()
    if not nome:
        print("❌ Nome não pode estar vazio!")
        return
    
    data = input("Data (YYYY-MM-DD): ").strip()
    hora = input("Hora (HH:MM): ").strip()
    duracao = input("Duração (minutos): ").strip()
    descricao = input("Descrição: ").strip()
    max_alunos = input("Máximo de alunos: ").strip()
    
    try:
        sucesso, mensagem = create_class(
            nome, data, hora, duracao, descricao, max_alunos, TEST_INSTRUCTOR_ID
        )
        if sucesso:
            print(f"✅ {mensagem}")
        else:
            print(f"❌ {mensagem}")
    except Exception as e:
        print(f"❌ Erro ao criar aula: {e}")


def listar_minhas_aulas():
    """Lista todas as aulas do instrutor."""
    print("\n📋 MINHAS AULAS")
    print("-" * 40)
    
    aulas = list_classes(TEST_INSTRUCTOR_ID)
    
    if not aulas:
        print("Nenhuma aula registada.")
        return
    
    for aula in aulas:
        status_emoji = "✅" if aula["status"] == "confirmado" else "❌"
        print(f"\n{status_emoji} ID: {aula['id']}")
        print(f"   Nome: {aula['name']}")
        print(f"   Horário: {aula['schedule']}")
        print(f"   Duração: {aula['duration']} min")
        print(f"   Vagas: {aula['max_students']}")
        print(f"   Descrição: {aula.get('description', 'N/A')}")
        print(f"   Status: {aula['status']}")


def editar_aula():
    """Edita uma aula existente."""
    print("\n✏️  EDITAR AULA")
    print("-" * 40)
    
    listar_minhas_aulas()
    
    try:
        class_id = int(input("\nID da aula a editar: ").strip())
    except ValueError:
        print("❌ ID inválido!")
        return
    
    aula = get_class_by_id(class_id)
    if not aula:
        print("❌ Aula não encontrada!")
        return
    
    if aula["instructor_id"] != TEST_INSTRUCTOR_ID:
        print("❌ Você não tem permissão para editar esta aula!")
        return
    
    print("\nDeixe em branco para não alterar:")
    nome = input("Novo nome: ").strip()
    data = input("Nova data (YYYY-MM-DD): ").strip()
    hora = input("Nova hora (HH:MM): ").strip()
    duracao = input("Nova duração (minutos): ").strip()
    descricao = input("Nova descrição: ").strip()
    max_alunos = input("Novo máximo de alunos: ").strip()
    
    kwargs = {}
    if nome:
        kwargs["name"] = nome
    if data:
        kwargs["schedule_date"] = data
    if hora:
        kwargs["schedule_time"] = hora
    if duracao:
        kwargs["duration"] = int(duracao)
    if descricao:
        kwargs["description"] = descricao
    if max_alunos:
        kwargs["max_students"] = int(max_alunos)
    
    try:
        sucesso, mensagem = edit_class(class_id, TEST_INSTRUCTOR_ID, **kwargs)
        if sucesso:
            print(f"✅ {mensagem}")
        else:
            print(f"❌ {mensagem}")
    except Exception as e:
        print(f"❌ Erro ao editar aula: {e}")


def cancelar_aula():
    """Cancela uma aula."""
    print("\n❌ CANCELAR AULA")
    print("-" * 40)
    
    listar_minhas_aulas()
    
    try:
        class_id = int(input("\nID da aula a cancelar: ").strip())
    except ValueError:
        print("❌ ID inválido!")
        return
    
    confirma = input("Tem certeza? (S/N): ").strip().upper()
    if confirma != "S":
        print("Operação cancelada.")
        return
    
    try:
        sucesso, mensagem = cancel_class(class_id, TEST_INSTRUCTOR_ID)
        if sucesso:
            print(f"✅ {mensagem}")
        else:
            print(f"❌ {mensagem}")
    except Exception as e:
        print(f"❌ Erro ao cancelar aula: {e}")


def ver_alunos_inscritos():
    """Mostra os alunos inscritos numa aula."""
    print("\n👥 ALUNOS INSCRITOS")
    print("-" * 40)
    
    listar_minhas_aulas()
    
    try:
        class_id = int(input("\nID da aula: ").strip())
    except ValueError:
        print("❌ ID inválido!")
        return
    
    alunos = get_enrolled_students(class_id)
    
    if not alunos:
        print("Nenhum aluno inscrito nesta aula.")
        return
    
    print(f"\nTotal: {len(alunos)} aluno(s)\n")
    for aluno in alunos:
        print(f"• {aluno['name']}")
        print(f"  Email: {aluno['email']}")
        print(f"  Inscrito em: {aluno['reservation_date']}\n")


# ============ FUNCIONALIDADES DO ALUNO ============

def listar_aulas_disponiveis():
    """Lista todas as aulas disponíveis."""
    print("\n📚 AULAS DISPONÍVEIS")
    print("-" * 40)
    
    aulas = list_available_classes()
    
    if not aulas:
        print("Nenhuma aula disponível.")
        return
    
    for aula in aulas:
        print(f"\n📅 ID: {aula['id']}")
        print(f"   Nome: {aula['name']}")
        print(f"   Instrutor: {aula['instructor_name']}")
        print(f"   Horário: {aula['schedule']}")
        print(f"   Duração: {aula['duration']} min")
        print(f"   Vagas disponíveis: {aula['spots_left']}/{aula['max_students']}")
        print(f"   Descrição: {aula.get('description', 'N/A')}")


def reservar_aula():
    """Reserva uma aula."""
    print("\n🎫 RESERVAR AULA")
    print("-" * 40)
    
    listar_aulas_disponiveis()
    
    try:
        class_id = int(input("\nID da aula a reservar: ").strip())
    except ValueError:
        print("❌ ID inválido!")
        return
    
    try:
        sucesso, mensagem = reserve_class(TEST_STUDENT_ID, class_id)
        if sucesso:
            print(f"✅ {mensagem}")
        else:
            print(f"❌ {mensagem}")
    except Exception as e:
        print(f"❌ Erro ao fazer reserva: {e}")


def listar_minhas_reservas():
    """Lista as reservas do aluno."""
    print("\n📋 MINHAS RESERVAS")
    print("-" * 40)
    
    reservas = list_student_reservations(TEST_STUDENT_ID)
    
    if not reservas:
        print("Nenhuma reserva ativa.")
        return
    
    for reserva in reservas:
        print(f"\n✅ ID: {reserva['reservation_id']}")
        print(f"   Aula: {reserva['class_name']}")
        print(f"   Horário: {reserva['schedule']}")
        print(f"   Duração: {reserva['duration']} min")
        print(f"   Reservado em: {reserva['reserved_at']}")


def cancelar_reserva():
    """Cancela uma reserva."""
    print("\n❌ CANCELAR RESERVA")
    print("-" * 40)
    
    listar_minhas_reservas()
    
    try:
        reserva_id = int(input("\nID da reserva a cancelar: ").strip())
    except ValueError:
        print("❌ ID inválido!")
        return
    
    confirma = input("Tem certeza? (S/N): ").strip().upper()
    if confirma != "S":
        print("Operação cancelada.")
        return
    
    try:
        sucesso, mensagem = cancel_reservation(reserva_id, TEST_STUDENT_ID)
        if sucesso:
            print(f"✅ {mensagem}")
        else:
            print(f"❌ {mensagem}")
    except Exception as e:
        print(f"❌ Erro ao cancelar reserva: {e}")


# ============ MENU PRINCIPAL ============

def main():
    """Menu principal de autenticação."""
    while True:
        print_menu()
        opcao = input("Escolha uma opção: ").strip()
        
        if opcao == "1":
            print(f"\n✅ Acedido como {TEST_INSTRUCTOR_NAME} (Instrutor)")
            test_instrutor()
        elif opcao == "2":
            print(f"\n✅ Acedido como {TEST_STUDENT_NAME} (Aluno)")
            test_aluno()
        elif opcao == "0":
            print("\n👋 Até à próxima!")
            break
        else:
            print("❌ Opção inválida!")


if __name__ == "__main__":
    main()