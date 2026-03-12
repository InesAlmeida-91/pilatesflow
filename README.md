# PilatesFlow – Sistema de Gestão de Aulas de Pilates

## Descrição do Projeto

O **PilatesFlow** é uma aplicação simples desenvolvida em Python para gestão de aulas de pilates.
O sistema permite que os **instrutores façam a criação a gestão de aulas** e que **alunos façam reservas nessas aulas**.

Este projeto foi desenvolvido como exercício prático da UFCD de **Projeto de tecnologias e programação de sistemas de informação**.

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
(em progresso)
```

### Descrição das Pastas

(em progresso)

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

Bernardo Lagos @blagos1806

Guilherme Silva @guilhermesilva3692

Inês Almeida

---
