# PilatesFlow – Sistema de Gestão de Aulas de Pilates

## Descrição do Projeto

O **PilatesFlow** é uma aplicação web construída em Python + Flask para gestão de um estúdio de pilates.

- Instrutores podem criar, editar, cancelar aulas e ver alunos inscritos.
- Alunos podem ver aulas disponíveis, fazer reservas, e cancelar reservas.

Esta app é um exercício para a UFCD de **Projeto de Tecnologias e Programação de Sistemas de Informação**.

---

## Funcionalidades

### Instrutor

* Criar aulas
* Listar aulas criadas
* Editar aulas
* Cancelar aulas
* Ver alunos inscritos numa aula

### Aluno

* Listar aulas disponíveis
* Reservar aulas
* Ver reservas feitas
* Cancelar reservas

---

## Estrutura do Projeto

```
main.py
README.md
requirements.txt
data/
  ├─ classes.json
  ├─ reservations.json
  └─ users.json
src/
  ├─ auth.py
  ├─ database.py
  ├─ utils.py
  ├─ containers/
  │   ├─ class_service.py
  │   └─ reservation_service.py
  └─ components/
      ├─ instructor.py
      └─ student.py
templates/
  ├─ base.html
  ├─ login.html
  ├─ register.html
  ├─ instructor/
  │   └─ ...
  └─ student/
      └─ ...
tests/
  ├─ test_classes.py
  ├─ test_login.py
  └─ test_reservations.py
```

### Descrição das Pastas

- `data/`: armazenamento em JSON de utilizadores, aulas e reservas.
- `src/`: lógica da aplicação e serviços.
- `templates/`: páginas HTML
- `tests/`: testes unitários.

---

## Tecnologias Utilizadas

* Python 3
* JSON para armazenamento de dados

---

## Como Executar o Projeto

1. Garantir que o **Python 3** está instalado.

2. Abrir o terminal na pasta do projeto.

3. Executar o programa:

```
python main.py
```
---

## Estrutura de Dados

O sistema utiliza ficheiros **JSON** para armazenar os dados:

### Classes

```
classes.json
```

Campos principais:

* id
* name
* schedule
* duration
* description
* status
* max_students
* instructor_id

---

### Reservas

```
reservations.json
```

Campos principais:

* id
* student_id
* class_id
* created_at
* status

---

## Regras de Negócio

O sistema aplica algumas regras básicas:

* Apenas aulas com estado **confirmado** podem ser reservadas.
* Um aluno não pode reservar a mesma aula duas vezes.
* Uma aula não pode ultrapassar o número máximo de alunos.
* Apenas o aluno que fez a reserva pode cancelá-la.

---


## Autores

Projeto para a unidade curricular de **Projeto de tecnologias e programação de sistemas de informação** desenvolvido por:

Bernardo Lagos [@blagos1806](https://github.com/blagos1806)

Guilherme Silva [@guilhermesilva3692](https://github.com/guilhermesilva3692)

Inês Almeida [@InesAlmeida-91](https://github.com/InesAlmeida-91)

---
