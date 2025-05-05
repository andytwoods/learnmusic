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

### Setting Up Tailwind CSS

This project uses Tailwind CSS for styling. Follow these steps to set up the Tailwind CLI:

1. Install Node.js and npm if you haven't already (https://nodejs.org/)

2. Install the project dependencies:

    ```
    $ npm install
    ```

3. Build the CSS (one-time build):

    ```
    $ npm run build
    ```

4. Or watch for changes during development:

    ```
    $ npm run watch
    ```

The Tailwind configuration is in `tailwind.config.js`, and the input CSS file is at `./learnmusic/static/css/tailwind.css`. The compiled output is generated at `./learnmusic/static/css/project.css`.
