# Django Guidelines

You are an expert in Python, Django, and scalable web apps. Write secure, maintainable, performant code.

## Python
- Follow PEP 8 (120 char limit), double quotes, `isort`, f-strings.

### Exception handling
- **Never use catch-all exceptions**:
  - Do not use bare `except:` or `except Exception:` anywhere in the codebase.
  - Always catch the **most specific** exception you can genuinely handle.
  - If meaningful recovery is not possible, let the exception propagate so it fails loudly.
  - Use logging instead of `print()` when reporting errors.
- **Static analysis**
  - Configure linting (e.g. Ruff/flake8) to *error on*:
    - bare `except:`
    - `except Exception:`
    - unused exception variables

## Django
- Use built-ins before third-party.
- Prioritise security; use ORM over raw SQL.
- Use signals sparingly.

## Models
- Always add `__str__`.
- Use `related_name` when helpful.
- `blank=True` for forms, `null=True` for DB.

## Views
- Validate/sanitise input.
- Prefer `get_object_or_404`.
- Paginate lists.

## URLs
- Descriptive names, end with `/`.

## Forms
- Prefer ModelForms.
- Use crispy-forms (or similar).

## Templates
- Use inheritance.
- Keep logic minimal.
- Always `{% load static %}`, enable CSRF.

## Settings
- Use env vars, never commit secrets.

## Database
- Always use migrations.
- Optimise queries (`select_related`, `prefetch_related`).
- Index frequent lookups.

## Tasks (Framework-Agnostic)

### Task layout
- Each app’s `tasks.py` must **only** contain task-decorated functions for the chosen task-queue system.
- No business logic, utility functions, or classes should be placed in `tasks.py`.
- Task functions should:
  - accept and validate raw input;
  - call helper functions that contain the actual business logic;
  - handle only queue-specific concerns such as scheduling, retries, or metadata.

### Task helpers
- Create a dedicated module for task-related logic, e.g. `helpers/task_helpers.py` (project-wide or per-app).
- All business/domain logic used by tasks must live in `task_helpers.py`, not in `tasks.py`.
- Helper functions should be:
  - reusable by views, management commands, and tasks;
  - clear about side-effects;
  - written to be as idempotent as reasonably possible (safe for retries).

## Testing
- Write unit tests for new features.
- Cover both success and failure paths.
