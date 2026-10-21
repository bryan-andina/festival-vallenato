# Sistema Web de Votaciones — Festival de la Leyenda Vallenata 2027
**Fundación Universitaria del Área Andina | Facultad de Ingenierías y Ciencias Básicas**  
**Asignatura:** Desarrollo Web | **Entrega 2:** Desarrollo Inicial del Sistema de Votaciones  

---

## 1. Overview & Architecture
This project is an enterprise-grade web application built using **Python**, **Django (MVT Architecture)**, and **MySQL** for the 60th Edition of the Vallenato Legend Festival 2027 in Valledupar, Colombia.

The codebase strictly adheres to **Clean Code**, **Twelve-Factor App**, and **SOLID Principles**:
* **Single Responsibility Principle (SRP):** Segregated apps (`apps.common`, `apps.accounts`, `apps.voting`), isolating domain entities from presentation and authentication workflows.
* **Open/Closed Principle (OCP):** Base `TimeStampedModel` abstraction and forward-compatible `Vote` model designed for future validation rules without altering existing entities.
* **Liskov Substitution Principle (LSP):** Strict compliance with Django Model and Class-Based View contracts.
* **Dependency Inversion Principle (DIP):** Decoupled environment settings (`.env`), driver-agnostic database configuration powered by `PyMySQL`.

```
Domain Hierarchy:
[EDITION] ──1:N──> [CATEGORY] ──1:N──> [VOTING] ──1:N──> [OPTION]
                                          ▲                  ▲
                                          │                  │
                                        [VOTE] ──────────────┘
                                          │
                                       [USER]
```

---

## 2. Tech Stack
* **Language:** Python 3.12+
* **Framework:** Django 5+ / 6+ (Model-View-Template pattern)
* **Database:** MySQL 8.4+ LTS (Driver: `PyMySQL` pure Python)
* **Styling & UI:** Bootstrap 5.3, Bootstrap Icons, Google Fonts (Montserrat & Open Sans)
* **Authentication:** Django Auth engine with customized registration and login forms

---

## 3. Team & Role Distribution (Grupo 4 Integrantes)

| Integrante | Rol Especializado | Responsabilidades Técnicas Asignadas |
| :--- | :--- | :--- |
| **Bryan Rincón Rodríguez** | Backend Core, Database & DevOps Lead | Setup del proyecto Django, configuración de MySQL, modelos ORM (`models.py`), migraciones, flujos de autenticación (`accounts`), setup de Git/GitHub y `README.md`. |
| **Yasmin Betancourt Contreras** | Frontend Lead & UX/UI (Templates MVT) | Arquitectura de plantillas (`base.html`), adaptación del prototipo Figma a Bootstrap 5, diseño responsivo de vistas públicas y formularios. |
| **Cristian Camilo Noreña Giraldo** | Admin Panel, Business Logic & QA | Customización de Django Admin (`inlines`, filtros, búsquedas), fixture/seed data del Festival Vallenato, pruebas funcionales de administración. |
| **Juan Manuel Mojica Ávila** | Views & Integration / Report & Video | Controladores CBV (`views.py`), enrutamiento (`urls.py`), consolidación del informe PDF oficial bajo rúbrica y coordinación del video demostrativo. |

---

## 4. Quickstart & Installation Guide

### Prerequisites
* Python 3.12 or higher installed.
* Docker Desktop (recommended) or MySQL Server 8.4+ local with a database named `vallenato_festival_db`.

### Step 1: Clone Repository
```bash
git clone https://github.com/bryan-andina/festival-vallenato.git
cd festival-vallenato
```

### Step 2: Start MySQL Database (Docker)
```bash
docker compose up -d
```
*(Spins up an isolated MySQL 8.4 LTS container on port 3306 with `vallenato_festival_db` ready).*

### Step 3: Create & Activate Virtual Environment
```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Environment Variables Setup
Copy the example environment file:
```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```
Ensure your database credentials in `.env` match your environment.

### Step 6: Execute Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 7: Load Initial Festival Data & Create Admin
Run the automated seed command to load the 60th Edition, categories, and contestants:
```bash
python manage.py seed_festival_data
```
To securely create your administrative credentials:
```bash
python manage.py createsuperuser
```
*(Note: Public voters can self-register directly through the web portal interface at `/accounts/register/`).*

### Step 8: Run Development Server
```bash
python manage.py runserver
```
* **Public Portal:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* **Admin Portal:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 5. Automated Testing Suite
Run the 9 test suites validating model integrity, business rules, and views:
```bash
python manage.py test
```
All unit tests should pass with `OK`.

---

## 6. Project Directory Structure
```
desarrollo-web/
├── apps/
│   ├── common/             # Base abstractions (TimeStampedModel)
│   ├── accounts/           # User authentication, registration, login/logout
│   │   ├── forms.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests.py
│   └── voting/             # Core Festival Domain
│       ├── models.py       # Edition, Category, Voting, Option, Vote
│       ├── views.py        # Public MVT views
│       ├── urls.py
│       ├── admin.py        # Django Admin customization & Inlines
│       ├── tests.py
│       └── management/commands/seed_festival_data.py
├── templates/
│   ├── base.html           # Master layout with Bootstrap 5
│   ├── accounts/           # login.html, register.html
│   └── voting/             # edition_list.html, category_list.html, voting_detail.html
├── vallenato_project/
│   ├── __init__.py         # PyMySQL registration hook
│   ├── settings.py         # Twelve-Factor configuration
│   ├── urls.py             # Root URL dispatcher
│   └── wsgi.py
├── docker-compose.yml       # MySQL 8.4 container configuration
├── .env.example
├── .gitignore
├── manage.py
├── requirements.txt
└── README.md
```
