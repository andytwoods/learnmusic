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
- [Contributing](#contributing)
  - [Contributing Instruction Sheets](#contributing-instruction-sheets)
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

## 🤝 Contributing

We welcome contributions of all kinds — issues, docs, bug fixes, and especially help expanding our instrument instruction sheets. Any help is sincerely appreciated. If you're unsure about anything, please reach out to the project maintainers — opening a GitHub issue is perfect and we’re happy to guide you.

### Contributing Instruction Sheets

Instruction sheets power the practice experience for each instrument. They live as JSON files in:

- [notes/static/instruments/](https://github.com/andytwoods/learnmusic/blob/master/notes/static/instruments/)

A good example to follow is [notes/static/instruments/trumpet.json](https://github.com/andytwoods/learnmusic/blob/master/notes/static/instruments/trumpet.json).

#### What is an instruction sheet?

It’s a JSON file that describes an instrument’s metadata and playable range at different skill levels, along with any fingering charts (when applicable).

Notes on fields:
- name: Display name of the instrument (e.g., "Trumpet").
- ui_template: The name of a UI template for the instrument if a custom layout is needed (existing templates can be reused).
- clefs: One or more clefs this instrument commonly uses (e.g., ["TREBLE"]).
- common_keys: A shortlist of keys the instrument commonly plays in (e.g., ["Bb", "C"]).
- skill_levels:
  - Beginner: Either a semicolon-separated list of notes in the format "NOTE ALTER OCTAVE" (e.g., "C 0 4").
  - Intermediate/Advanced: Use lowest_note and highest_note to define range (same note format).
- fingerings: Optional per-note fingering references, especially helpful for brass/woodwinds (keys like "C/4"). Empty string ("") can indicate "open" or no valves/keys pressed.

Tip: See [notes/static/instruments/trumpet.json](https://github.com/andytwoods/learnmusic/blob/master/notes/static/instruments/trumpet.json) for an example, including alternate fingerings and references.

#### Naming and formatting
- File name: lowercase, hyphen-free JSON file matching the instrument (e.g., flute.json, alto_sax.json). If unsure, just pick something sensible — we can rename during review.
- Use valid JSON (double quotes, commas, etc.).
- Keep lines under ~120 characters when possible.

#### Validate your JSON
- Use any JSON linter/formatter (e.g., jsonlint.com or your editor’s formatter).
- Run the project locally to ensure the instrument loads:
  ```bash
  python manage.py runserver
  ```

#### Try it in the app
Open a practice page using one of these URLs (adjust instrument, clef, key, level as needed):
- Without absolute pitch:
  /notes/practice-try/Trumpet/Treble/Bb/Beginner/0/0/
- With absolute pitch:
  /notes/practice-try/Trumpet/Treble/Bb/Bb/Beginner/0/0/

If your instrument is named differently, substitute the path segment accordingly (e.g., Flute/Treble/C/Beginner/0/0/).

#### How to submit
1) Fork the repository and create a branch.
2) Add your JSON file to notes/static/instruments/ and commit.
3) Optionally, add a short note in the README proposing any special considerations for your instrument.
4) Open a Pull Request. We’ll review promptly and help with any tweaks.

#### Not sure or have questions?
- Create a feature request or question on GitHub: https://github.com/andythomaswoods/learnmusic/issues/new
- Or open a draft PR with your work-in-progress; we’ll jump in and help.

Thank you — any help is appreciated and makes LearnMusic better for everyone!

## 📄 License

This project is licensed under the MIT License with Commons Clause - see the [LICENSE](LICENSE) file for details.
