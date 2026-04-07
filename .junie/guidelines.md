# Project Guidelines

You are an expert in Python, Django, and scalable web apps. Write secure, maintainable, performant code.

---

## 1. Project Scaffold & Layout

Bootstrapped from [cookiecutter-django](https://github.com/cookiecutter/cookiecutter-django). Do not hand-roll structure it already provides.

**What is already in place — do not recreate:**
- Split settings: `config/settings/base.py`, `local.py`, `production.py`, `test.py`
- Custom `User` model at `<project_name>/users/models.py`; `AUTH_USER_MODEL = "users.User"` already set
- Whitenoise, Redis, django-allauth (with email verification), django-environ, argon2 passwords
- `pyproject.toml` with `uv` for dependency management (no `requirements/` folder)

**Layout rules:**
- Django apps directory: `<project_name>/` (`APPS_DIR = BASE_DIR / "<project_name>"`)
- All apps live under `<project_name>/`: e.g. `<project_name>/plunges/`, `<project_name>/tasks/`
- Register new apps in `LOCAL_APPS` in `config/settings/base.py` as `"<project_name>.<appname>"`
- Add dependencies with `uv add <package>`

---

## 2. Python Conventions

- PEP 8, 120-char line limit, double quotes, `isort`, f-strings
- Use built-in Django facilities before reaching for third-party libraries
- Prioritise security; use the ORM over raw SQL
- Use signals sparingly

### Exception handling
- **Never** use bare `except:` or `except Exception:` — catch the most specific exception you can genuinely handle
- If meaningful recovery is not possible, let exceptions propagate so failures are loud
- Use `logging` instead of `print()` for errors

---

## 3. User Model

- Login is **email-only** — no `username` field
- The model has a `name` CharField; no `first_name` or `last_name`
- Always reference via `get_user_model()` — never import the model directly
- New user-related profile models belong in `<project_name>/users/models.py`

---

## 4. Authentication

- Use **django-allauth** for all authentication. No custom auth backends.
- Social login providers: **Google** and **GitHub**
- Email/password is kept as a fallback only; allauth is configured to require email verification
- **User registration is disabled in production** (`ACCOUNT_ALLOW_REGISTRATION = False`) pending University Ethics approval. Do not re-enable without explicit instruction.

### User impersonation
- Use **django-hijack**; configure the hijack button in Django admin (user list and detail views)
- Only superusers and staff with explicit permission may hijack
- Show a visible warning banner for the duration of any hijacked session

### Consent middleware
- `ConsentRequiredMiddleware` blocks all authenticated views until the user accepts the current consent version
- To exempt a URL, add its `url_name` to the exempt list in the middleware (e.g. `users:deletion_complete`)
- For HTMX non-GET requests from non-consented users, respond with `HX-Redirect` to force a full-page reload so the consent modal appears

### Passkey (WebAuthn) setup

**Packages** (install with `uv add`):
- `django-allauth[mfa,webauthn]` — the `webauthn` extra pulls in `fido2`
- `webauthn>=2.7.1` — direct dependency required by allauth's WebAuthn implementation

**`INSTALLED_APPS`** (`base.py`):
```python
"allauth.account",
"allauth.mfa",
"allauth.mfa.webauthn",
```

**Settings by environment:**
```python
# base.py (all environments)
MFA_SUPPORTED_TYPES = ["webauthn", "recovery_codes"]
MFA_PASSKEY_LOGIN_ENABLED = True

# production.py only
MFA_PASSKEY_SIGNUP_ENABLED = True
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_ENABLED = True

# local.py only — never in production
MFA_WEBAUTHN_ALLOW_INSECURE_ORIGIN = True  # allows passkey testing over HTTP
```

### Passkey UX preferences
- Passkey is the **primary** sign-in method. Email/password is secondary.
- The login template (`account/login.html`) overrides allauth's default and must:
  - Show a prominent "Sign in with passkey (fingerprint / device PIN)" button **first**
  - Hide the email/password form in a native `<details>`/`<summary>` collapsed by default
- Use **WebAuthn Conditional UI** (`mediation: "conditional"`) so the browser surfaces stored passkeys in the email-field autofill without a button click:
  - On page load, check `PublicKeyCredential.isConditionalMediationAvailable()`
  - If available, set `autocomplete="username webauthn"` on the email input and start a background conditional credential request against allauth's `mfa_login_webauthn` endpoint
  - Use an `AbortController`; abort it in a **capture-phase** listener on the passkey button (allauth's handler runs in the bubble phase — this prevents "A request is already pending")
  - Swallow `AbortError` and `NotAllowedError` silently; log anything else
- The server cannot know if a visitor has a passkey before they identify — conditional UI is browser/OS-side. Do not attempt server-side passkey detection on the login page.

---

## 5. Models

- Always add `__str__`
- Use `related_name` where helpful
- `blank=True` for forms, `null=True` for DB nullability
- Always use migrations; optimise with `select_related`/`prefetch_related`; index frequent lookups

---

## 6. Views & URLs

- Validate and sanitise all input
- Prefer `get_object_or_404`
- Paginate lists
- URL names should be descriptive and end with `/`

---

## 7. Templates

- Templates live in the app that owns them: `<project_name>/<appname>/templates/<appname>/`
- Do **not** use a global `<project_name>/templates/` directory for app templates
- `base.html` lives at the project level; all app templates extend it
- HTMX partials: `<project_name>/<appname>/templates/<appname>/partials/_<name>.html`
- Use template inheritance; keep logic minimal; always `{% load static %}` and enable CSRF

### allauth template overrides
- Allauth UI elements are overridden with Bulma styling in `<project_name>/templates/allauth/elements/`
- `button.html` maps allauth tags to Bulma classes: `danger`→`is-danger`, `success`→`is-success`, `warning`→`is-warning`, `secondary`→`is-light`, `outline`→`is-outlined`, default→`is-primary`
- The entrance layout (`allauth/layouts/entrance.html`) extends `base.html`, centres content in a 5-tablet/4-desktop column, and injects `cap-mode` for Capacitor
- When overriding allauth templates, place them in `<project_name>/templates/account/` or `<project_name>/templates/mfa/` — allauth picks them up automatically

---

## 8. Forms

- Prefer ModelForms
- Use **crispy-forms** with the **Bulma** template pack (`crispy-bulma`). `CRISPY_TEMPLATE_PACK = "bulma"` in `base.py`.

---

## 9. Frontend

### CSS — Bulma
- **Bulma** is the only CSS framework. No Bootstrap, Tailwind, or others.
- Self-hosted at `<project_name>/static/css/bulma.min.css` (v1.0.3)
- Use Bulma classes in templates; write custom CSS only when Bulma has no suitable class
- Custom styles go in `<project_name>/static/css/project.css` (compiled from SCSS)

### Self-hosted static libraries
All JS/CSS dependencies are self-hosted in `<project_name>/static/`. Do not load them from CDNs. Exception: very large dependencies (e.g. **Pyodide**) may use a CDN when justified.

| File | Purpose |
|------|---------|
| `htmx.min.js` | AJAX navigation and partial updates |
| `sweetalert2.min.js` + `.min.css` | Modal dialogs and confirmations |
| `chart.umd.min.js` (v4.4.7) | Chart rendering |
| `bulma.min.css` (v1.0.3) | CSS framework |
| `fontawesome/css/all.min.css` | Icons |
| `project.js` / `project.css` | Project-wide behaviours and styles |

### JavaScript — modals and notifications
- Use **SweetAlert2** for modal dialogs/alerts/confirmations — never `alert()` or `confirm()`
- Use `window.showToast(message, type)` (defined in `project.js`) for transient client-side notifications
- Server-side Django messages are automatically rendered as toasts via `base.html`

### HTMX — when to use it
- Use **htmx** for all dynamic partial updates. No React, Vue, or other JS frameworks.
- **Same-endpoint pattern:** HTMX hits the same URL as the full page; the view detects HTMX via `request.headers.get("HX-Request")` and returns a partial template. Do **not** create separate URL routes for HTMX.
- Default to HTMX for: form submissions, consent/surveys/profile intake, session flow transitions, any server-rendered content swap

### HTMX — form validation responses
- Return **HTTP 422** with the partial form template when HTMX form validation fails. The project's HTMX config (`project.js`) swaps on 422. Do **not** return 200 for failed submissions.

### Vanilla JS — when to use it
Only for cases where HTMX genuinely does not apply:
- **Pyodide / code editor** — CodeMirror, Web Worker execution, timer, telemetry
- **Chart rendering** — Chart.js/Plotly.js consuming JSON from API endpoints

### JSON API endpoints
Acceptable only for:
- Aggregate chart data consumed by Chart.js/Plotly.js
- Pyodide test result submission (client posts JSON after local execution)

Do **not** create JSON endpoints for anything that could be an HTMX partial swap.

### Accessibility (a11y) widget
- A persistent accessibility panel is built into `base.html`, toggled via an "Accessibility" button in the navbar and footer. **Do not remove it.**
- Preferences are stored in `localStorage` under `a11yPrefs` and applied via `data-*` attributes on `<html>` before the DOM renders (prevents flash)
- The four axes:

| Axis | `data-*` attribute | Values |
|------|--------------------|--------|
| Theme | `data-theme` | `light` \| `dark` \| `system` |
| Contrast | `data-a11y-contrast` | `standard` \| `low` \| `high` |
| Text size | `data-a11y-text` | `standard` \| `large` \| `extra-large` |
| Motion | `data-a11y-motion` | `standard` \| `reduced` |

- Target `html[data-*]` selectors in `project.css` when writing preference-aware CSS (don't rely solely on `@media` queries)

### Radio button behaviour
Radio buttons are **deselectable** (clicking a selected radio unchecks it). This is intentional, handled in `project.js`. Do not override it.

---

## 10. Settings

- Use env vars; never commit secrets
- Settings split: `base.py` (all envs) / `local.py` (dev) / `production.py` (prod) — do not collapse them
- **Local dev:** SQLite database, console email backend
- **Production:** PostgreSQL, Brevo SMTP (`smtp-relay.brevo.com:587`) via `django-anymail`
- **Error tracking:** Rollbar in production (`django-rollbar`, `ROLLBAR_ACCESS_TOKEN` env var). Not in dev.

---

## 11. Background Tasks

- Use **Huey** with a Redis backend. **Never Celery.**
- `tasks.py` contains only task-decorated functions — no business logic
- Task functions: accept/validate raw input, call helpers, handle only queue concerns (scheduling, retries)
- All business logic lives in `helpers/` modules (e.g. `helpers/task_helpers.py`) — reusable by views, management commands, and tasks alike
- Write helpers to be idempotent where possible (safe for retries)

---

## 12. Phased Work (TASKS.md / ACTIONS.md)

When implementing work broken into phases in a `TASKS.md`, `ACTIONS.md`, or similar file:
- After completing each phase, commit all changes to git before starting the next phase
- Write a commit message that gives a clear synopsis of what the phase accomplished — not just "phase 2 done" but a meaningful summary of the actual changes (e.g. "Add WebAuthn passkey login with conditional UI and abort-controller fix")
- Use the standard commit format: short imperative subject line, then a blank line and bullet points for detail if the phase was substantial

## 13. Testing

- Write unit tests for all new features; cover success and failure paths
- Never hard-code URL paths in assertions — use `django.urls.reverse()` with named routes
- For redirect assertions that depend on the current URL, use `request.path` or `request.get_full_path()`
