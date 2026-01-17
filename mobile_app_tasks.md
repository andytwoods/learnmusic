**Test Specification – Django + HTMX + Bulma → Capacitor App (Android & iOS)

This document defines mandatory tests the agent must implement or execute.
A task is not complete unless all its tests pass.

Architecture:

Django renders HTML

HTMX handles interactivity

Bulma provides styling

Capacitor is a native wrapper using a WebView

Authentication uses Django sessions

Push notifications via FCM/APNs

The app loads the live Django site via server.url (no bundled frontend)

Reference Repo:
https://github.com/andytwoods/pubtime

Tests are grouped as:

🧪 Backend tests (Django)

📱 Mobile/Runtime tests (Capacitor / JS / Native)

🔁 End-to-end tests (Cross-layer)

T01 – Health & Auth Endpoints

File Targets

pubtime/urls.py (or config/urls.py)

core/views.py (or equivalent app)

🧪 Tests

GET /health/:

status 200

body exactly ok

GET /whoami/:

unauthenticated → { authenticated: false }

authenticated → { authenticated: true, username: <value> }

🔁 Acceptance

curl request passes

Browser request passes

Response identical in WebView

T02 – Native-Shell Detection (User-Agent + Session Flag)

Guiding Rule

Native-shell detection MUST NOT rely on custom headers injected into every request.
Instead, use:

a custom User-Agent suffix set by Capacitor

a server-side Django session flag to persist state

File Targets

core/middleware.py (new middleware)

pubtime/settings.py (middleware registration)

templates/base.html

Implementation Rules

Capacitor app appends UA suffix:
PubtimeApp/<version> (<platform>)

Django middleware logic:

if request User-Agent contains PubtimeApp/:

set request.is_native_shell = True

set request.session["is_native_shell"] = True

else if session flag exists:

set request.is_native_shell = True

else:

set request.is_native_shell = False

Base template adds class when in native shell (ensure django.template.context_processors.request is enabled):

<html class="{% if request.is_native_shell %}is-native-shell{% endif %}">


🧪 Tests

Browser request (no UA suffix):

<html> does NOT include is-native-shell

App request (UA suffix present):

<html> DOES include is-native-shell

Session persistence:

first request sets session flag

subsequent requests without UA suffix but with session cookie still render is-native-shell

🔁 Acceptance

Conditional UI behaves correctly (e.g. hide “Get the App” banners)

No flash of non-native UI on first load

Behaviour identical on Android and iOS

T03 – HTMX CSRF Injection & Domain-Based Trust

Guiding Rule

Because the WebView loads the live Django site, CSRF is domain-based, not capacitor://-based.

File Targets

pubtime/settings.py

templates/base.html

Implementation Rules

CSRF_TRUSTED_ORIGINS includes:

https://pubtime.pro

https://www.pubtime.pro (if applicable)

Do not include capacitor://localhost unless switching to a bundled frontend model

Add global HTMX hook to inject CSRF header (preferred over hx-headers on body for better token rotation support):

document.addEventListener("htmx:configRequest", (event) => {
  const csrfToken = document.cookie.match(/csrftoken=([^;]+)/)?.[1];
  if (csrfToken) {
    event.detail.headers["X-CSRFToken"] = csrfToken;
  }
});

🧪 Tests

HTMX POST request includes X-CSRFToken

CSRF middleware does not reject POST from WebView

Canonical host redirects (www ↔ apex) do not break CSRF

🔁 Acceptance

HTMX POST succeeds in:

Desktop browser

Android WebView (Release build)

iOS WebView (Device/TestFlight)

T04 – Session Persistence

File Targets

pubtime/settings.py

Required Settings

SESSION_COOKIE_SECURE = True (prod)

SESSION_COOKIE_SAMESITE = "Lax" (or None if OAuth requires)

SESSION_COOKIE_HTTPONLY = True

🧪 Tests

Login creates session cookie with correct flags

📱 Runtime Tests

Login in app

Background app (≥ 5 minutes)

Force-kill app

Relaunch app

🔁 Acceptance

/whoami/ reports authenticated after relaunch

No unexpected redirect to login

T05 – Push Device Model

File Targets

core/models.py

core/admin.py

🧪 Tests

ORM create persists all fields

Unique constraint on token enforced (upsert logic)

Token update modifies existing row

Deleting user cleans up or disables related devices

🔁 Acceptance

Django admin shows accurate device state

T06 – Push Registration API

File Targets

core/views.py or core/api.py

🧪 Tests

POST /api/push/register/ with valid payload → 200 { ok: true }

Posting same token twice → single DB row

Authenticated call:

device linked to user

Anonymous call:

device.user is null (or rejected per policy)

🔁 Acceptance

No duplicate device rows for same physical device

T07 – Push Sending Service

File Targets

core/services.py

requirements.txt (e.g. firebase-admin, huey)

🧪 Tests

Payload includes:

title

body

data.url

FCM/APNs API accepts payload (mock or sandbox)

🔁 Acceptance

No exceptions in Huey consumer

Success logged

T08 – Admin Test Push

File Targets

core/admin.py

🧪 Tests

Non-staff user → 403 Forbidden

Staff user → push sent

🔁 Acceptance

Push delivered to physical test device

T09 – Capacitor Project Integrity

File Targets

project root

capacitor.config.ts or .json

📱 Tests

npx cap sync succeeds

android/ and ios/ directories exist

server.url switches correctly between dev/prod

🔁 Acceptance

App builds in Xcode and Android Studio without errors

T10 – Remote WebView Loading & Offline Fallback

File Targets

capacitor.config.ts

Offline fallback HTML or JS handler

📱 Tests

App loads Django home page

Offline scenario:

disable network

launch app

custom “Connection Lost” screen shown

retry reload works

🔁 Acceptance

No generic WebView error pages

No blank white screen

T11 – Native-Shell Signal (User-Agent Configuration)

File Targets

capacitor.config.ts

Android WebView config

iOS WKWebView config

📱 Tests

UA string includes PubtimeApp/<version>

Server logs confirm UA suffix

🔁 Acceptance

Django reliably detects app traffic

T12 – Push Registration (Mobile Client)

File Targets

Capacitor native push code

Optional JS bridge logic

Django /api/push/register/

🧪 Tests

Token acquired via native plugin

Persistent device_id (UUID) stored

Registration POST retries on network failure

Token rotation updates backend

🔁 Acceptance

Backend reflects current valid token

Push sending works

T13 – Push Delivery

📱 Tests

App foreground → receives push

App background → system notification

App killed → system notification

🔁 Acceptance

Notification visible in OS tray

T14 – Push Tap Routing (Deep Linking)

File Targets

Capacitor notification handlers

🔁 End-to-End Test

Send push with data.url="/my-account/"

Kill app

Tap notification

🔁 Acceptance

App opens

WebView navigates to /my-account/

Session preserved

Security Tests

Reject data.url values that are:

absolute URLs

protocol-relative (//)

non-HTTP schemes

Implementation: use django.utils.http.url_has_allowed_host_and_scheme(url, allowed_hosts={request.get_host()})

T15 – Android Firebase

File Targets

android/app/google-services.json

Gradle config

📱 Tests

Push delivered to physical Android device

🔁 Acceptance

No FCM auth errors in Logcat

T16 – iOS APNs

File Targets

GoogleService-Info.plist

AppDelegate.swift

📱 Tests

Push delivered to physical iOS device

🔁 Acceptance

Notification visible

Tap opens app

T17 – UI Polish (Safe Areas)

File Targets

static/css/*.css

📱 Tests

Top notch padding applied

Bottom safe area respected

Keyboard does not hide inputs

Implementation: Add CSS env(safe-area-inset-*) to body/navbar in project.css:
body {
  padding: env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left);
}
.navbar.is-fixed-top {
  top: env(safe-area-inset-top);
}

🔁 Acceptance

Content fully visible on modern iOS/Android devices

T18 – HTMX Regression Suite

File Targets

Existing HTMX templates

🧪 Tests

Create / Update / Delete flows

HX-Redirect works in WebView

🔁 Acceptance

No 403 errors

No broken swaps

T19 – External Link Handling

File Targets

JS click interception logic

📱 Tests

Internal links → open in WebView

External links → open in system browser

🔁 Acceptance

User never trapped inside third-party site

T20 – Android Hardware Back Button

File Targets

Capacitor App listener logic

📱 Tests

Back navigates WebView history

App exits only from root screen

🔁 Acceptance

Native-feeling navigation

T21 – App Store Compliance (Account Deletion)

File Targets

Account settings template

Delete-account view

🧪 Tests

User can delete account

User logged out afterward

Device tokens deleted from DB

🔁 Acceptance

Meets Apple App Store Review Guideline 5.1.1(v)

All push registration data for the user is wiped from backend

Global Test Rules

Tests must be repeatable

Push tests must use real devices

Fail fast – do not continue on partial success

Agent must output error logs before attempting fixes

Definition of Done

All tests pass

App functions without dev tools

Django remains single source of truth

App ready for TestFlight / Play Console internal testing

Domain change ready: CSRF_TRUSTED_ORIGINS and server.url are configurable via env vars
