# LearnMusic

Behold My Awesome Project!

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## Settings

Moved to [settings](https://cookiecutter-django.readthedocs.io/en/latest/1-getting-started/settings.html).

## Basic Commands

### Setting Up Your Users

- To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

- To create a **superuser account**, use this command:

      $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

### Type checks

Running type checks with mypy:

    $ mypy learnmusic

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

#### Running tests with pytest

    $ python manage.py test

### JavaScript Testing

The project includes comprehensive tests for JavaScript files, particularly for `learning_manager.js`.

#### Manual Testing in Browser

A dedicated test page has been set up to test JavaScript functionality in the browser:

1. Start the Django development server:
   ```
   python manage.py runserver
   ```

2. Navigate to the test page:
   ```
   http://localhost:8000/notes/test-js/
   ```

#### Automated Testing with Jest

Jest tests have been set up for thorough testing of JavaScript functions:

1. Install Node.js dependencies:
   ```
   npm install
   ```

2. Run the tests:
   ```
   npm test
   ```

For more details about JavaScript testing, see the [JavaScript tests README](learnmusic/static/js/tests/README.md).
