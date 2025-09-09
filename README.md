# 🎵 LearnMusic

> An interactive platform for learning music theory and instrument practice

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Django](https://img.shields.io/badge/Django-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![HTMX](https://img.shields.io/badge/HTMX-3366CC?logo=htmx&logoColor=white)](https://htmx.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
    
[![CI](https://github.com/andytwoods/learnmusic/actions/workflows/ci.yml/badge.svg)](https://github.com/andytwoods/learnmusic/actions/workflows/ci.yml)
[![License: MIT with Commons Clause](https://img.shields.io/badge/License-MIT%20with%20Commons%20Clause-blue.svg)](https://github.com/andythomaswoods/learnmusic/blob/main/LICENSE)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Setting Up Users](#setting-up-users)
  - [Development Commands](#development-commands)
- [Testing](#testing)
  - [Python Tests](#python-tests)
  - [JavaScript Tests](#javascript-tests)
- [Project Settings](#project-settings)
- [License](#license)

## 🔍 Overview

LearnMusic is a web application designed to help users learn music theory and practice various instruments. The platform provides interactive lessons, exercises, and tools to enhance the learning experience for musicians of all levels.

## ✨ Features

- Interactive music theory lessons
- Instrument-specific practice modules
- Progress tracking and personalized learning paths
- User authentication and profile management
- Responsive design for desktop and mobile devices

## 🚀 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/andythomaswoods/learnmusic.git
   cd learnmusic
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Apply migrations:
   ```bash
   python manage.py migrate
   ```

5. Start the development server:
   ```bash
   python manage.py runserver
   ```

## 🔧 Usage

### Setting Up Users

- **Normal User Account**: Go to Sign Up and fill out the form. Once submitted, you'll see a "Verify Your E-mail Address" page. Check your console for a simulated email verification message, copy the link into your browser, and your email will be verified.

- **Superuser Account**: Create an admin user with the following command:
  ```bash
  python manage.py createsuperuser
  ```

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

### Development Commands

- **Run the server**:
  ```bash
  python manage.py runserver
  ```

- **Type checks with mypy**:
  ```bash
  mypy learnmusic
  ```

## 🧪 Testing

### Python Tests

To run the tests, check your test coverage, and generate an HTML coverage report:

```bash
coverage run -m pytest
coverage html
```

Then open `htmlcov/index.html` in your browser to view the coverage report.

You can also run tests with Django's test runner:

```bash
python manage.py test
```

### JavaScript Tests

The project includes comprehensive tests for JavaScript files, particularly for `learning_manager.js`.

#### Manual Testing in Browser

A dedicated test page has been set up to test JavaScript functionality in the browser:

1. Start the Django development server:
   ```bash
   python manage.py runserver
   ```

2. Navigate to the test page:
   ```
   http://localhost:8000/notes/test-js/
   ```

#### Automated Testing with Jest

Jest tests have been set up for thorough testing of JavaScript functions:

1. Install Node.js dependencies:
   ```bash
   npm install
   ```

2. Run the tests:
   ```bash
   npm test
   ```

For more details about JavaScript testing, see the [JavaScript tests README](learnmusic/static/js/tests/README.md).

## ⚙️ Project Settings

The project includes multiple Django settings modules to support different environments:

- Default local development: `config.settings.local` (used by manage.py and docs by default)
- Explicit local SQLite: `config.settings.local_sqlite` (imports from `local` and pins SQLite DB)
- Test/CI: `config.settings.test` (used in CI workflows)
- Production: `config.settings.production`

Base settings (config/settings/base.py) already use SQLite by default. The `local_sqlite` settings module exists to make this explicit and to allow you to easily switch from any other local configuration back to SQLite.

### Using local_sqlite settings

You can run Django commands with the `local_sqlite` settings in two ways:

1) Temporarily via the command line:

```bash
# macOS/Linux
DJANGO_SETTINGS_MODULE=config.settings.local_sqlite python manage.py runserver

# Windows (PowerShell)
$Env:DJANGO_SETTINGS_MODULE = "config.settings.local_sqlite"; python manage.py runserver
```

2) Persistently via a .env file in the project root:

```
DJANGO_SETTINGS_MODULE=config.settings.local_sqlite
```

After switching settings, run migrations and start the server:

```bash
python manage.py migrate
python manage.py runserver
```

By default, `local_sqlite` stores the database file at `BASE_DIR / "local_db.sqlite3"`. If you prefer the default `db.sqlite3` from base settings, you can continue using `config.settings.local` instead.

For detailed information about Cookiecutter Django settings, refer to the official docs: https://cookiecutter-django.readthedocs.io/en/latest/1-getting-started/settings.html

## 📄 License

This project is licensed under the MIT License with Commons Clause - see the [LICENSE](LICENSE) file for details.
