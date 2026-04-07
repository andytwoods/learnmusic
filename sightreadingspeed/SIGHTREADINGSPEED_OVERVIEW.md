# SIGHTREADINGSPEED – LLM Action Plan

This document is a phased, step-by-step build guide. Each phase has a clear goal, exact file actions, and acceptance criteria. Complete phases in order. Do not skip ahead. Do not add anything not listed.

---

## Ground rules

- All JS is classic browser script (no ES modules, no bundler).
- All static JS files are loaded via `{% static %}` in `index.html`.
- Static JS files must never read or write `window.srs_state` at file-evaluation time — only inside functions called after bootstrap.
- All access to shared state uses `window.srs_state` explicitly — no bare-name fallthrough.
- The `cache` global (from `project.js`) is available everywhere because `base.html` loads it.
- `VF` refers to the global `Vex.Flow` object exposed by `vexflow.js`.
- Do not add features, error handling, or abstractions not described in this plan.

---

## Canonical data structures

Memorise these. Every module uses them.

### `window.srs_state`
```js
{
  settings:          null,   // current sanitised settings object
  bars:              [],     // array of bar objects from score_generator
  flatNotes:         [],     // flat array of note objects from music_theory.flattenBars
  renderedPositions: [],     // array of position objects from score_renderer
  playbackState:     'idle', // string: idle | lead_in | playing | paused | finished
  generationVersion: 0,      // incremented on each Generate
}
```

### settings object (stored in localStorage under key `srs_settings`)
```js
{
  bpm:           60,        // int 20–200
  clef:          'treble',  // 'treble' | 'bass'
  min_note:      'C/4',     // VexFlow pitch string
  max_note:      'G/5',     // VexFlow pitch string
  durations:     ['q'],     // subset of ['w','h','q','8']
  time_signature:'4/4',     // '4/4' | '3/4' | '2/4'
  metronome:     false,     // bool
  lead_in_bars:  1,         // int 1–4
  num_bars:      16,        // int 4–64
  key_sig_type:  'sharps',  // 'sharps' | 'flats'
  key_sig_count: 0,         // int 0–6
}
```

### bar object (element of `bars` array)
```js
{
  notes: [
    { pitch: 'C/4', duration: 'q' },
    // ...
  ]
}
```

### flatNote object (element of `flatNotes` array)
```js
{
  noteIndex:  0,      // absolute index across whole passage
  barIndex:   0,      // which bar
  pitch:      'C/4',  // VexFlow pitch string
  duration:   'q',    // VexFlow duration string
  beats:      1,      // numeric beat count
  startBeat:  0,      // passage-relative beat where this note begins
  endBeat:    1,      // passage-relative beat where this note ends
}
```

### renderedPosition object (element of `renderedPositions` array)
```js
{
  noteIndex: 0,
  rowIndex:  0,
  xStart:    120,  // CSS px from left of #score-wrapper
  xCenter:   130,
  xEnd:      146,  // usually xStart of next note; see final-note fallback rule
  yTop:      40,   // CSS px from top of #score-wrapper
  yBottom:   140,
}
```

### state ownership (one writer per field)
| field | only written by |
|---|---|
| `settings` | `regenerateScore()` and `init()` |
| `bars` | `regenerateScore()` |
| `flatNotes` | `regenerateScore()` |
| `renderedPositions` | `score_renderer.render()` |
| `playbackState` | `srs_state_change` event handler in `bindControls()` |
| `generationVersion` | `regenerateScore()` |

---

## Phase 0 — Django scaffolding

**Goal:** The URL `/sight-reading-speed/` serves a page. Nothing else works yet.

### Actions

**0.1** Create directory `sightreadingspeed/` at the project root (alongside `notes/`, `tuning/`).

**0.2** Create `sightreadingspeed/__init__.py` — empty file.

**0.3** Create `sightreadingspeed/apps.py`:
```python
from django.apps import AppConfig

class SightreadingspeedConfig(AppConfig):
    name = "sightreadingspeed"
```

**0.4** Create `sightreadingspeed/views.py`:
```python
from django.shortcuts import render

def index(request):
    return render(request, "sightreadingspeed/index.html")
```

**0.5** Create `sightreadingspeed/urls.py`:
```python
from django.urls import path
from . import views

app_name = "sightreadingspeed"

urlpatterns = [
    path("", views.index, name="index"),
]
```

**0.6** In `config/urls.py`, add inside `urlpatterns`:
```python
path("sight-reading-speed/", include("sightreadingspeed.urls")),
```
Add `include` to the imports if not already present.

**0.7** In `config/settings/base.py`, add to `INSTALLED_APPS`:
```python
"sightreadingspeed",
```

**0.8** Create directory tree:
```
sightreadingspeed/
├── static/
│   └── sightreadingspeed/
│       └── js/            ← empty for now
└── templates/
    └── sightreadingspeed/
        └── index.html     ← create this now (Phase 1)
```

### Acceptance criteria
- `python manage.py check` passes.
- `/sight-reading-speed/` does not 404 (once `index.html` exists).

---

## Phase 1 — `index.html` skeleton

**Goal:** The page loads with Bootstrap layout, all controls present, score area present, no JS logic yet. VexFlow and the app JS files are loaded. The inline bootstrap script defines `window.srs_state` and all helper functions but does not call `init()` yet.

**File:** `sightreadingspeed/templates/sightreadingspeed/index.html`

### Structure

```django
{% extends "base.html" %}
{% load static %}

{% block title %}Sight Reading Speed{% endblock %}

{% block content %}
<div class="container py-4">

  <h1 class="mb-1">Sight Reading Speed</h1>
  <p class="text-muted mb-4">Generate a passage, press Play, and read.</p>

  <!-- Warning area -->
  <div id="srs-warning" class="alert alert-warning d-none" role="alert"></div>

  <!-- Settings panel -->
  <div class="card mb-4">
    <div class="card-header d-flex justify-content-between align-items-center">
      <span>Settings</span>
      <button class="btn btn-sm btn-outline-secondary"
              type="button"
              data-bs-toggle="collapse"
              data-bs-target="#srs-settings-body">
        Toggle
      </button>
    </div>
    <div id="srs-settings-body" class="card-body collapse show">
      <div class="row g-3">

        <div class="col-sm-6 col-md-3">
          <label class="form-label" for="srs-bpm">BPM</label>
          <div class="d-flex align-items-center gap-2">
            <input type="range" class="form-range flex-grow-1"
                   id="srs-bpm" min="20" max="200" value="60">
            <span id="srs-bpm-label" class="text-nowrap">60</span>
          </div>
        </div>

        <div class="col-sm-6 col-md-3">
          <label class="form-label" for="srs-clef">Clef</label>
          <select class="form-select" id="srs-clef">
            <option value="treble">Treble</option>
            <option value="bass">Bass</option>
          </select>
        </div>

        <div class="col-sm-6 col-md-3">
          <label class="form-label" for="srs-timesig">Time Signature</label>
          <select class="form-select" id="srs-timesig">
            <option value="4/4">4/4</option>
            <option value="3/4">3/4</option>
            <option value="2/4">2/4</option>
          </select>
        </div>

        <div class="col-sm-6 col-md-3">
          <label class="form-label" for="srs-keysig-type">Key Signature</label>
          <div class="d-flex gap-2">
            <select class="form-select" id="srs-keysig-type">
              <option value="sharps">Sharps</option>
              <option value="flats">Flats</option>
            </select>
            <select class="form-select" id="srs-keysig-count">
              <option value="0">0</option>
              <option value="1">1</option>
              <option value="2">2</option>
              <option value="3">3</option>
              <option value="4">4</option>
              <option value="5">5</option>
              <option value="6">6</option>
            </select>
          </div>
        </div>

        <div class="col-sm-6 col-md-3">
          <label class="form-label" for="srs-min-note">Lowest Note</label>
          <select class="form-select" id="srs-min-note"></select>
        </div>

        <div class="col-sm-6 col-md-3">
          <label class="form-label" for="srs-max-note">Highest Note</label>
          <select class="form-select" id="srs-max-note"></select>
        </div>

        <div class="col-sm-6 col-md-3">
          <label class="form-label" for="srs-leadin">Lead-in Bars</label>
          <input type="number" class="form-control"
                 id="srs-leadin" min="1" max="4" value="1">
        </div>

        <div class="col-sm-6 col-md-3">
          <label class="form-label" for="srs-numbars">Total Bars</label>
          <select class="form-select" id="srs-numbars">
            <option value="4">4 Bars</option>
            <option value="8">8 Bars</option>
            <option value="12">12 Bars</option>
            <option value="16" selected>16 Bars</option>
            <option value="20">20 Bars</option>
            <option value="24">24 Bars</option>
            <option value="32">32 Bars</option>
            <option value="48">48 Bars</option>
            <option value="64">64 Bars</option>
          </select>
        </div>

        <div class="col-12">
          <label class="form-label d-block">Note Durations</label>
          <div class="d-flex gap-3 flex-wrap">
            <div class="form-check">
              <input class="form-check-input srs-duration" type="checkbox"
                     id="dur-w" value="w">
              <label class="form-check-label" for="dur-w">Semibreve</label>
            </div>
            <div class="form-check">
              <input class="form-check-input srs-duration" type="checkbox"
                     id="dur-h" value="h">
              <label class="form-check-label" for="dur-h">Minim</label>
            </div>
            <div class="form-check">
              <input class="form-check-input srs-duration" type="checkbox"
                     id="dur-q" value="q" checked>
              <label class="form-check-label" for="dur-q">Crotchet</label>
            </div>
            <div class="form-check">
              <input class="form-check-input srs-duration" type="checkbox"
                     id="dur-8" value="8">
              <label class="form-check-label" for="dur-8">Quaver</label>
            </div>
            <div class="form-check">
              <input class="form-check-input srs-duration" type="checkbox"
                     id="dur-16" value="16">
              <label class="form-check-label" for="dur-16">Semiquaver</label>
            </div>
          </div>
        </div>

        <div class="col-12">
          <div class="form-check form-switch">
            <input class="form-check-input" type="checkbox"
                   id="srs-metronome" role="switch">
            <label class="form-check-label" for="srs-metronome">Metronome</label>
          </div>
        </div>

      </div><!-- /.row -->
    </div><!-- /#srs-settings-body -->
  </div><!-- /.card -->

  <!-- Lead-in countdown -->
  <div id="srs-leadin-bar" class="mb-3 d-none">
    <div class="progress" style="height: 8px;">
      <div id="srs-leadin-progress"
           class="progress-bar bg-info" style="width: 0%"></div>
    </div>
    <p id="srs-leadin-text" class="text-center text-muted small mt-1 mb-0">
      Lead-in: beat 1
    </p>
  </div>

  <!-- Status label -->
  <p id="srs-status" class="text-muted small mb-2">Idle</p>

  <!-- Score -->
  <div id="score-wrapper" class="position-relative border rounded mb-4"
       style="overflow-x: auto; min-height: 120px;">
    <div id="score-container"></div>
    <div id="playhead" style="
      position: absolute; top: 0; left: 0;
      width: 2px; height: 100%;
      background: red; opacity: 0.7;
      pointer-events: none;
      display: none;
    "></div>
  </div>

  <!-- Transport controls -->
  <div class="d-flex gap-2 flex-wrap mb-4">
    <button id="btn-generate" class="btn btn-outline-primary">
      <i class="fas fa-music"></i> Generate
    </button>
    <button id="btn-play" class="btn btn-success btn-lg">
      <i class="fas fa-play"></i> Play
    </button>
    <button id="btn-pause" class="btn btn-warning btn-lg d-none">
      <i class="fas fa-pause"></i> Pause
    </button>
    <button id="btn-reset" class="btn btn-secondary d-none">
      <i class="fas fa-undo"></i> Reset
    </button>
  </div>

</div><!-- /.container -->
{% endblock %}

{% block javascript %}
<!-- VexFlow (must come before app JS) -->
<script src="{% static 'js/vexflow.js' %}"></script>

<!-- App modules (order matters) -->
<script src="{% static 'sightreadingspeed/js/settings_manager.js' %}"></script>
<script src="{% static 'sightreadingspeed/js/music_theory.js' %}"></script>
<script src="{% static 'sightreadingspeed/js/score_generator.js' %}"></script>
<script src="{% static 'sightreadingspeed/js/score_renderer.js' %}"></script>
<script src="{% static 'sightreadingspeed/js/metronome.js' %}"></script>
<script src="{% static 'sightreadingspeed/js/playback_manager.js' %}"></script>

<!-- Bootstrap (inline script runs after all static files) -->
<script>
  // ── Shared state ─────────────────────────────────────────────────────────
  window.srs_state = {
    settings:          null,
    bars:              [],
    flatNotes:         [],
    renderedPositions: [],
    playbackState:     'idle',
    generationVersion: 0,
  };

  // ── Warning helpers ───────────────────────────────────────────────────────
  function showSrsWarning(message) {
    var el = document.getElementById('srs-warning');
    el.textContent = message;
    el.classList.remove('d-none');
  }
  function clearSrsWarning() {
    var el = document.getElementById('srs-warning');
    el.textContent = '';
    el.classList.add('d-none');
  }

  // ── UI read/write ─────────────────────────────────────────────────────────
  function gatherSettingsFromUI() {
    return {
      bpm:            parseInt(document.getElementById('srs-bpm').value, 10),
      clef:           document.getElementById('srs-clef').value,
      time_signature: document.getElementById('srs-timesig').value,
      min_note:       document.getElementById('srs-min-note').value,
      max_note:       document.getElementById('srs-max-note').value,
      durations:      Array.from(
                        document.querySelectorAll('.srs-duration:checked')
                      ).map(function(el) { return el.value; }),
      metronome:      document.getElementById('srs-metronome').checked,
      lead_in_bars:   parseInt(document.getElementById('srs-leadin').value, 10),
      num_bars:       parseInt(document.getElementById('srs-numbars').value, 10),
      key_sig_type:   document.getElementById('srs-keysig-type').value,
      key_sig_count:  parseInt(document.getElementById('srs-keysig-count').value, 10),
    };
  }

  function applySettingsToUI(s) {
    document.getElementById('srs-bpm').value           = s.bpm;
    document.getElementById('srs-bpm-label').textContent = s.bpm;
    document.getElementById('srs-clef').value          = s.clef;
    document.getElementById('srs-timesig').value       = s.time_signature;
    document.getElementById('srs-min-note').value      = s.min_note;
    document.getElementById('srs-max-note').value      = s.max_note;
    document.getElementById('srs-metronome').checked   = s.metronome;
    document.getElementById('srs-leadin').value        = s.lead_in_bars;
    document.getElementById('srs-numbars').value       = s.num_bars;
    document.getElementById('srs-keysig-type').value   = s.key_sig_type;
    document.getElementById('srs-keysig-count').value  = s.key_sig_count;
    document.querySelectorAll('.srs-duration').forEach(function(el) {
      el.checked = s.durations.indexOf(el.value) !== -1;
    });
  }

  function setStatus(text) {
    document.getElementById('srs-status').textContent = text;
  }

  function updateTransportButtons(state) {
    var play  = document.getElementById('btn-play');
    var pause = document.getElementById('btn-pause');
    var reset = document.getElementById('btn-reset');
    var isActive = state === 'lead_in' || state === 'playing';
    play.classList.toggle('d-none',  isActive);
    pause.classList.toggle('d-none', !isActive);
    reset.classList.toggle('d-none', state === 'idle');
    var labels = {
      idle: 'Idle', lead_in: 'Lead-in',
      playing: 'Playing', paused: 'Paused', finished: 'Finished'
    };
    setStatus(labels[state] || state);
  }

  // ── Note range selects ────────────────────────────────────────────────────
  function populateNoteSelects() {
    // music_theory is loaded; get the full chromatic list from it.
    var pitches = music_theory.getChromaticScale();
    ['srs-min-note', 'srs-max-note'].forEach(function(id) {
      var sel = document.getElementById(id);
      sel.innerHTML = '';
      pitches.forEach(function(p) {
        var opt = document.createElement('option');
        opt.value = p;
        opt.textContent = p.replace('/', '');
        sel.appendChild(opt);
      });
    });
  }

  // ── Core action ───────────────────────────────────────────────────────────
  function regenerateScore() {
    clearSrsWarning();
    playback_manager.reset();

    var settings = settings_manager.sanitise(gatherSettingsFromUI());

    // Validate range
    var minMidi = music_theory.pitchToMidi(settings.min_note);
    var maxMidi = music_theory.pitchToMidi(settings.max_note);
    if (maxMidi - minMidi < 5) {
      showSrsWarning(
        'Note range is too narrow. Choose a range of at least a perfect fourth (5 semitones).'
      );
      return;
    }

    // Validate rhythmic cells
    if (!music_theory.getValidRhythmicCells(settings).length) {
      showSrsWarning(
        'The selected durations cannot fill a complete bar. Enable at least one compatible duration.'
      );
      return;
    }

    settings_manager.save(settings);
    window.srs_state.settings = settings;
    window.srs_state.generationVersion += 1;

    var bars      = score_generator.generate(settings);
    var flatNotes = music_theory.flattenBars(bars);
    window.srs_state.bars      = bars;
    window.srs_state.flatNotes = flatNotes;

    score_renderer.render(bars, settings);
    // score_renderer.render() writes window.srs_state.renderedPositions internally.
  }

  // ── Control wiring ────────────────────────────────────────────────────────
  function bindControls() {
    // BPM slider live label
    document.getElementById('srs-bpm').addEventListener('input', function() {
      document.getElementById('srs-bpm-label').textContent = this.value;
    });

    document.getElementById('btn-generate').addEventListener('click', regenerateScore);
    document.getElementById('btn-play').addEventListener('click', function() {
      playback_manager.play();
    });
    document.getElementById('btn-pause').addEventListener('click', function() {
      playback_manager.pause();
    });
    document.getElementById('btn-reset').addEventListener('click', function() {
      playback_manager.reset();
    });

    // State transitions from playback_manager
    document.addEventListener('srs_state_change', function(e) {
      window.srs_state.playbackState = e.detail.state;
      updateTransportButtons(e.detail.state);
    });

    // Lead-in UI
    document.addEventListener('srs_beat', function(e) {
      var d = e.detail;
      if (d.phase === 'lead_in') {
        document.getElementById('srs-leadin-bar').classList.remove('d-none');
        document.getElementById('srs-leadin-text').textContent =
          'Lead-in: beat ' + d.beatInBar;
        var pct = (d.leadInBeatsDone / d.leadInBeatsTotal) * 100;
        document.getElementById('srs-leadin-progress').style.width = pct + '%';
      } else {
        document.getElementById('srs-leadin-bar').classList.add('d-none');
        document.getElementById('srs-leadin-progress').style.width = '0%';
      }
    });
  }

  // ── Init ──────────────────────────────────────────────────────────────────
  (function init() {
    populateNoteSelects();

    var settings = settings_manager.get();
    window.srs_state.settings = settings;
    applySettingsToUI(settings);

    // Auto-generate on load so the user arrives with a ready passage.
    regenerateScore();

    bindControls();
    updateTransportButtons('idle');
  })();
</script>
{% endblock %}
```

**Note on `{% block javascript %}`:** Check `base.html` for the exact block name used for extra scripts at the bottom of the page. Use whatever name that template defines. If it uses `{% block extra_js %}` or similar, match it.

### Acceptance criteria
- Page loads without JS errors.
- All controls render.
- Score area is visible (empty at this stage since JS modules are stubs).

---

## Phase 2 — `settings_manager.js`

**File:** `sightreadingspeed/static/sightreadingspeed/js/settings_manager.js`

**Depends on:** `cache` global (from `project.js` via `base.html`).

### Full implementation

```js
var settings_manager = (function() {
  var KEY = 'srs_settings';

  var DEFAULTS = {
    bpm:            60,
    clef:           'treble',
    min_note:       'C/4',
    max_note:       'G/5',
    durations:      ['q'],
    time_signature: '4/4',
    metronome:      false,
    lead_in_bars:   1,
    num_bars:       16,
    key_sig_type:   'sharps',
    key_sig_count:  0,
  };

  function sanitise(raw) {
    var s = Object.assign({}, DEFAULTS, raw || {});

    if (!Array.isArray(s.durations) || s.durations.length === 0) {
      s.durations = ['q'];
    }

    s.bpm           = Math.min(200, Math.max(20,  parseInt(s.bpm,           10) || DEFAULTS.bpm));
    s.lead_in_bars  = Math.min(4,   Math.max(1,   parseInt(s.lead_in_bars,  10) || DEFAULTS.lead_in_bars));
    s.num_bars      = Math.min(32,  Math.max(4,   parseInt(s.num_bars,      10) || DEFAULTS.num_bars));
    s.key_sig_count = Math.min(6,   Math.max(0,   parseInt(s.key_sig_count, 10) || 0));

    if (['treble','bass'].indexOf(s.clef) === -1)           s.clef           = DEFAULTS.clef;
    if (['sharps','flats'].indexOf(s.key_sig_type) === -1)  s.key_sig_type   = DEFAULTS.key_sig_type;
    if (['4/4','3/4','2/4'].indexOf(s.time_signature) === -1) s.time_signature = DEFAULTS.time_signature;

    return s;
  }

  function get() {
    return sanitise(cache.get(KEY, {}));
  }

  function save(s) {
    cache.save(KEY, sanitise(s));
  }

  return { get: get, save: save, sanitise: sanitise };
})();
```

### Acceptance criteria
- `settings_manager.get()` returns a valid settings object.
- `settings_manager.sanitise({ bpm: 999 }).bpm === 200`.
- `settings_manager.sanitise({}).durations` equals `['q']`.

---

## Phase 3 — `music_theory.js`

**File:** `sightreadingspeed/static/sightreadingspeed/js/music_theory.js`

**Depends on:** nothing.

### Full implementation

```js
var music_theory = (function() {

  // ── Chromatic scale C2–C7 (VexFlow pitch strings) ────────────────────────
  var CHROMATIC_SCALE = [
    'C/2','C#/2','D/2','D#/2','E/2','F/2','F#/2','G/2','G#/2','A/2','A#/2','B/2',
    'C/3','C#/3','D/3','D#/3','E/3','F/3','F#/3','G/3','G#/3','A/3','A#/3','B/3',
    'C/4','C#/4','D/4','D#/4','E/4','F/4','F#/4','G/4','G#/4','A/4','A#/4','B/4',
    'C/5','C#/5','D/5','D#/5','E/5','F/5','F#/5','G/5','G#/5','A/5','A#/5','B/5',
    'C/6','C#/6','D/6','D#/6','E/6','F/6','F#/6','G/6','G#/6','A/6','A#/6','B/6',
    'C/7',
  ];

  // ── Key signature → VexFlow string ───────────────────────────────────────
  var KEY_SIG_TO_VEXFLOW = {
    sharps: { 0:'C', 1:'G', 2:'D', 3:'A', 4:'E', 5:'B', 6:'F#' },
    flats:  { 0:'C', 1:'F', 2:'Bb', 3:'Eb', 4:'Ab', 5:'Db', 6:'Gb' },
  };

  // ── Scale pitch classes per key ───────────────────────────────────────────
  // Each value is an array of the 7 pitch-class names (no octave) in the key.
  // Spelling matches the key family (sharps use #, flats use b).
  var KEY_SCALES = {
    C:  ['C','D','E','F','G','A','B'],
    G:  ['G','A','B','C','D','E','F#'],
    D:  ['D','E','F#','G','A','B','C#'],
    A:  ['A','B','C#','D','E','F#','G#'],
    E:  ['E','F#','G#','A','B','C#','D#'],
    B:  ['B','C#','D#','E','F#','G#','A#'],
    'F#':['F#','G#','A#','B','C#','D#','E#'],
    F:  ['F','G','A','Bb','C','D','E'],
    Bb: ['Bb','C','D','Eb','F','G','A'],
    Eb: ['Eb','F','G','Ab','Bb','C','D'],
    Ab: ['Ab','Bb','C','Db','Eb','F','G'],
    Db: ['Db','Eb','F','Gb','Ab','Bb','C'],
    Gb: ['Gb','Ab','Bb','Cb','Db','Eb','F'],
  };

  // ── Duration → beats ─────────────────────────────────────────────────────
  var DURATION_BEATS = { w: 4, h: 2, q: 1, '8': 0.5 };

  // ── Rhythmic cell banks ───────────────────────────────────────────────────
  // Each cell is an array of VexFlow duration strings summing to one bar.
  var RHYTHMIC_CELLS = {
    '4/4': [
      ['q','q','q','q'],
      ['h','q','q'],
      ['q','h','q'],
      ['q','q','h'],
      ['h','h'],
      ['w'],
      ['8','8','q','q','q'],
      ['q','8','8','q','q'],
      ['q','q','8','8','q'],
    ],
    '3/4': [
      ['q','q','q'],
      ['h','q'],
      ['q','h'],
      ['8','8','q','q'],
      ['q','8','8','q'],
    ],
    '2/4': [
      ['q','q'],
      ['h'],
      ['8','8','q'],
      ['q','8','8'],
    ],
  };

  // ── Public helpers ────────────────────────────────────────────────────────

  function getChromaticScale() {
    return CHROMATIC_SCALE.slice();
  }

  function pitchToMidi(pitchStr) {
    // 'C/4' → 60, 'C#/4' → 61, etc.
    var parts = pitchStr.split('/');
    var name  = parts[0];   // e.g. 'C#'
    var oct   = parseInt(parts[1], 10);
    var NOTE_MAP = {
      'C':0,'C#':1,'Db':1,'D':2,'D#':3,'Eb':3,
      'E':4,'Fb':4,'F':5,'E#':5,'F#':6,'Gb':6,
      'G':7,'G#':8,'Ab':8,'A':9,'A#':10,'Bb':10,
      'B':11,'Cb':11,'B#':0,
    };
    return (oct + 1) * 12 + NOTE_MAP[name];
  }

  function getVexFlowKeyString(type, count) {
    return KEY_SIG_TO_VEXFLOW[type][count];
  }

  function parseTimeSignature(ts) {
    var parts = ts.split('/');
    return { beatsPerBar: parseInt(parts[0], 10), beatUnit: parseInt(parts[1], 10) };
  }

  function durationToBeats(dur) {
    return DURATION_BEATS[dur];
  }

  function getScaleForKeySignature(type, count) {
    var key = KEY_SIG_TO_VEXFLOW[type][count];
    return KEY_SCALES[key].slice();
  }

  function getAllowedPitches(settings) {
    // Returns array of VexFlow pitch strings within [min_note, max_note]
    // filtered to the scale of the selected key signature.
    var scale   = getScaleForKeySignature(settings.key_sig_type, settings.key_sig_count);
    var minMidi = pitchToMidi(settings.min_note);
    var maxMidi = pitchToMidi(settings.max_note);

    return CHROMATIC_SCALE.filter(function(p) {
      var midi = pitchToMidi(p);
      if (midi < minMidi || midi > maxMidi) return false;
      var name = p.split('/')[0];
      return scale.indexOf(name) !== -1;
    });
  }

  function getValidRhythmicCells(settings) {
    var cells = RHYTHMIC_CELLS[settings.time_signature] || [];
    var allowed = settings.durations;
    return cells.filter(function(cell) {
      return cell.every(function(d) { return allowed.indexOf(d) !== -1; });
    });
  }

  function flattenBars(bars) {
    var flat = [];
    var beatCursor = 0;
    bars.forEach(function(bar, barIndex) {
      bar.notes.forEach(function(note, localIndex) {
        var beats = durationToBeats(note.duration);
        flat.push({
          noteIndex:  flat.length,
          barIndex:   barIndex,
          pitch:      note.pitch,
          duration:   note.duration,
          beats:      beats,
          startBeat:  beatCursor,
          endBeat:    beatCursor + beats,
        });
        beatCursor += beats;
      });
    });
    return flat;
  }

  return {
    getChromaticScale:     getChromaticScale,
    pitchToMidi:           pitchToMidi,
    getVexFlowKeyString:   getVexFlowKeyString,
    parseTimeSignature:    parseTimeSignature,
    durationToBeats:       durationToBeats,
    getScaleForKeySignature: getScaleForKeySignature,
    getAllowedPitches:      getAllowedPitches,
    getValidRhythmicCells: getValidRhythmicCells,
    flattenBars:           flattenBars,
  };
})();
```

### Acceptance criteria
- `music_theory.pitchToMidi('C/4') === 60`
- `music_theory.pitchToMidi('A/4') === 69`
- `music_theory.getVexFlowKeyString('flats', 2) === 'Bb'`
- `music_theory.getValidRhythmicCells({ time_signature:'4/4', durations:['q'] })` returns at least one cell.
- `music_theory.flattenBars([{ notes:[{pitch:'C/4',duration:'q'}] }])[0].startBeat === 0`

---

## Phase 4 — `score_generator.js`

**File:** `sightreadingspeed/static/sightreadingspeed/js/score_generator.js`

**Depends on:** `music_theory`.

### Full implementation

```js
var score_generator = (function() {

  var CONTOURS = ['ascending', 'descending', 'arch', 'wave'];

  function pickRandom(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
  }

  function generateBar(pitches, cells, prevPitch, settings) {
    var cell      = pickRandom(cells);
    var notes     = [];
    var current   = prevPitch || pickRandom(pitches);
    var currentIdx = pitches.indexOf(current);
    if (currentIdx === -1) currentIdx = Math.floor(pitches.length / 2);

    cell.forEach(function(duration) {
      // Step movement preference (70% step, 20% skip, 10% stay)
      var r = Math.random();
      var delta;
      if (r < 0.70) {
        delta = (Math.random() < 0.5) ? 1 : -1;          // step
      } else if (r < 0.90) {
        delta = (Math.random() < 0.5) ? 2 : -2;          // skip (third)
      } else {
        delta = 0;                                         // repeat (avoid if possible)
      }

      var nextIdx = currentIdx + delta;
      // Clamp to available pitch range
      nextIdx = Math.max(0, Math.min(pitches.length - 1, nextIdx));
      // Avoid same pitch twice in a row unless there is only one pitch
      if (nextIdx === currentIdx && pitches.length > 1) {
        nextIdx = currentIdx + (delta >= 0 ? 1 : -1);
        nextIdx = Math.max(0, Math.min(pitches.length - 1, nextIdx));
      }

      currentIdx = nextIdx;
      notes.push({ pitch: pitches[currentIdx], duration: duration });
    });

    return { notes: notes, lastPitch: pitches[currentIdx] };
  }

  function generate(settings) {
    var pitches = music_theory.getAllowedPitches(settings);
    var cells   = music_theory.getValidRhythmicCells(settings);
    if (!pitches.length || !cells.length) return [];

    var bars     = [];
    var prevPitch = null;

    for (var i = 0; i < settings.num_bars; i++) {
      var isLastBar = (i === settings.num_bars - 1);
      var result    = generateBar(pitches, cells, prevPitch, settings);

      if (isLastBar) {
        // End on tonic (first scale degree): the lowest available pitch
        // that is the root of the key, or fallback to the last pitch.
        var keyRoot = music_theory.getScaleForKeySignature(
          settings.key_sig_type, settings.key_sig_count
        )[0];
        var tonicPitches = pitches.filter(function(p) {
          return p.split('/')[0] === keyRoot;
        });
        if (tonicPitches.length) {
          var lastNote = result.notes[result.notes.length - 1];
          lastNote.pitch = tonicPitches[Math.floor(tonicPitches.length / 2)];
        }
      }

      bars.push({ notes: result.notes });
      prevPitch = result.lastPitch;
    }

    return bars;
  }

  return { generate: generate };
})();
```

### Acceptance criteria
- `score_generator.generate(settings)` returns an array of `num_bars` bar objects.
- Each bar's notes' duration values are all within `settings.durations`.
- The last bar's last note is a tonic pitch where possible.

---

## Phase 5 — `score_renderer.js`

**File:** `sightreadingspeed/static/sightreadingspeed/js/score_renderer.js`

**Depends on:** `VF` (VexFlow global), `music_theory`, `window.srs_state`.

### Responsibilities
1. Clear and re-draw the SVG in `#score-container`.
2. Record CSS-space note positions into `window.srs_state.renderedPositions`.

### Full implementation

```js
var score_renderer = (function() {

  var BARS_PER_ROW = 4;
  var ROW_HEIGHT   = 120;  // px per stave row
  var STAVE_TOP    = 20;   // px from top of row to stave
  var LEFT_MARGIN  = 10;
  var BAR_WIDTH;           // computed at render time

  function render(bars, settings) {
    var container = document.getElementById('score-container');
    container.innerHTML = '';

    if (!bars || !bars.length) return;

    var containerWidth = container.clientWidth || 800;
    BAR_WIDTH = Math.floor((containerWidth - LEFT_MARGIN) / BARS_PER_ROW);

    var numRows    = Math.ceil(bars.length / BARS_PER_ROW);
    var totalHeight = numRows * ROW_HEIGHT + 20;

    var VF       = Vex.Flow;
    var renderer = new VF.Renderer(container, VF.Renderer.Backends.SVG);
    renderer.resize(containerWidth, totalHeight);
    var context  = renderer.getContext();

    var keyStr  = music_theory.getVexFlowKeyString(settings.key_sig_type, settings.key_sig_count);
    var timeSig = settings.time_signature;
    var clef    = settings.clef;

    var rawPositions = [];  // {noteIndex, xAbsSvg, rowIndex, yTop, yBottom}

    var noteCounter = 0;

    for (var rowIdx = 0; rowIdx < numRows; rowIdx++) {
      var rowBars    = bars.slice(rowIdx * BARS_PER_ROW, (rowIdx + 1) * BARS_PER_ROW);
      var rowY       = rowIdx * ROW_HEIGHT + STAVE_TOP;

      rowBars.forEach(function(bar, colIdx) {
        var isFirstBar    = (rowIdx === 0 && colIdx === 0);
        var isFirstInRow  = (colIdx === 0);
        var xStart        = LEFT_MARGIN + colIdx * BAR_WIDTH;

        var stave = new VF.Stave(xStart, rowY, BAR_WIDTH);
        if (isFirstInRow) stave.addClef(clef);
        if (isFirstBar)   { stave.addKeySignature(keyStr); stave.addTimeSignature(timeSig); }
        stave.setContext(context).draw();

        // Build VexFlow notes
        var vfNotes = bar.notes.map(function(n) {
          return new VF.StaveNote({
            keys:     [n.pitch],
            duration: n.duration,
            clef:     clef,
          });
        });

        // Apply accidentals for the key
        var voice = new VF.Voice({
          num_beats:  parseInt(timeSig.split('/')[0], 10),
          beat_value: parseInt(timeSig.split('/')[1], 10),
        }).setMode(VF.Voice.Mode.SOFT);
        voice.addTickables(vfNotes);

        VF.Accidental.applyAccidentals([voice], keyStr);

        new VF.Formatter().joinVoices([voice]).format([voice], BAR_WIDTH - 20);
        voice.draw(context, stave);

        // Record raw SVG-space x positions
        vfNotes.forEach(function(vfNote) {
          rawPositions.push({
            noteIndex: noteCounter++,
            rowIndex:  rowIdx,
            xAbsSvg:   vfNote.getAbsoluteX(),
            yTop:      rowY,
            yBottom:   rowY + ROW_HEIGHT,
          });
        });
      });
    }

    // Convert SVG-space x to CSS-space x relative to #score-wrapper
    var svgEl      = container.querySelector('svg');
    var svgRect    = svgEl.getBoundingClientRect();
    var wrapper    = document.getElementById('score-wrapper');
    var wrapperRect = wrapper.getBoundingClientRect();
    var viewBoxW   = svgEl.viewBox.baseVal.width || parseFloat(svgEl.getAttribute('width')) || containerWidth;
    var scale      = svgRect.width / viewBoxW;
    var svgOffsetX = svgRect.left - wrapperRect.left;

    var positions = rawPositions.map(function(rp) {
      var cssX = rp.xAbsSvg * scale + svgOffsetX;
      return {
        noteIndex: rp.noteIndex,
        rowIndex:  rp.rowIndex,
        xStart:    cssX,
        xCenter:   cssX,
        xEnd:      cssX,  // filled in below
        yTop:      rp.yTop,
        yBottom:   rp.yBottom,
      };
    });

    // xEnd continuity rule
    for (var i = 0; i < positions.length - 1; i++) {
      positions[i].xEnd = positions[i + 1].xStart;
    }
    // Final note fallback
    if (positions.length) {
      var last = positions[positions.length - 1];
      last.xEnd = last.xStart + (last.xCenter - last.xStart) + 20;
    }

    // Write to shared state (sole writer)
    window.srs_state.renderedPositions = positions;

    // Show playhead at start position
    if (positions.length) {
      var ph = document.getElementById('playhead');
      ph.style.display = 'block';
      ph.style.left    = positions[0].xStart + 'px';
      ph.style.top     = positions[0].yTop   + 'px';
      ph.style.height  = (positions[0].yBottom - positions[0].yTop) + 'px';
    }
  }

  function getNoteCount() {
    return window.srs_state.renderedPositions.length;
  }

  return { render: render, getNoteCount: getNoteCount };
})();
```

### Acceptance criteria
- Score SVG appears in `#score-container` after calling `score_renderer.render(bars, settings)`.
- `window.srs_state.renderedPositions` has one entry per note.
- Each entry has `xStart`, `xEnd`, `yTop`, `yBottom` as numbers.
- `positions[i].xEnd === positions[i+1].xStart` for all non-final notes.

---

## Phase 6 — `metronome.js`

**File:** `sightreadingspeed/static/sightreadingspeed/js/metronome.js`

**Depends on:** nothing.

### Full implementation

```js
var metronome = (function() {

  function scheduleClick(audioCtx, when, isDownbeat) {
    var osc  = audioCtx.createOscillator();
    var gain = audioCtx.createGain();

    osc.frequency.value = isDownbeat ? 1000 : 800;
    gain.gain.setValueAtTime(0.3, when);
    gain.gain.exponentialRampToValueAtTime(0.001, when + 0.05);

    osc.connect(gain);
    gain.connect(audioCtx.destination);

    osc.start(when);
    osc.stop(when + 0.06);
  }

  return { scheduleClick: scheduleClick };
})();
```

### Notes
- `scheduleClick` uses the `when` argument for `osc.start()`. It never calls `audioCtx.currentTime` internally.
- The caller (playback_manager) passes the precise scheduled timestamp.

### Acceptance criteria
- `metronome.scheduleClick` is a callable function.
- No audio output at file-load time.

---

## Phase 7 — `playback_manager.js`

**File:** `sightreadingspeed/static/sightreadingspeed/js/playback_manager.js`

**Depends on:** `music_theory`, `metronome`, `settings_manager`, `window.srs_state`.

This is the most complex module. Read the full spec before writing.

### Responsibilities
- Own the `AudioContext` (created lazily on first `play()`).
- Run a lookahead scheduler loop to schedule metronome clicks at accurate timestamps.
- Run a `requestAnimationFrame` loop to move the playhead and update UI.
- Manage state transitions and dispatch `srs_state_change` events.
- Dispatch `srs_beat` events for visual UI only (not used for audio timing).

### Transport variables (internal, not exported)
```js
var audioCtx    = null;
var state       = 'idle';       // idle|lead_in|playing|paused|finished
var startTime   = null;         // audioCtx.currentTime when beat 0 of this segment began
var pausedOffset = 0;           // seconds into passage when paused
var rafId       = null;         // requestAnimationFrame handle
var schedulerTimer = null;      // setInterval handle for lookahead scheduler
var sessionToken = 0;           // incremented on each play/reset; stale callbacks check this
```

### Pause/resume math (critical — do not change)
```
On play/resume:
  startTime = audioCtx.currentTime - pausedOffset

Transport position at any moment:
  transportSeconds = audioCtx.currentTime - startTime

On pause:
  pausedOffset = audioCtx.currentTime - startTime

On reset:
  pausedOffset = 0
  startTime    = null
```

### Full implementation

```js
var playback_manager = (function() {

  var audioCtx      = null;
  var state         = 'idle';
  var startTime     = null;
  var pausedOffset  = 0;
  var rafId         = null;
  var schedulerTimer = null;
  var sessionToken  = 0;

  var LOOKAHEAD_S   = 0.1;   // seconds ahead to schedule audio
  var SCHEDULER_MS  = 25;    // ms between scheduler calls

  // ── Internal helpers ──────────────────────────────────────────────────────

  function setState(newState) {
    state = newState;
    document.dispatchEvent(new CustomEvent('srs_state_change', {
      detail: { state: newState }
    }));
  }

  function ensureAudioCtx() {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx.state === 'suspended') audioCtx.resume();
  }

  function getSettings() {
    return window.srs_state.settings || settings_manager.get();
  }

  function getBeatDuration() {
    return 60 / getSettings().bpm;
  }

  function getBeatsPerBar() {
    return music_theory.parseTimeSignature(getSettings().time_signature).beatsPerBar;
  }

  function getLeadInBeats() {
    return getSettings().lead_in_bars * getBeatsPerBar();
  }

  // ── Scheduler (audio clock) ───────────────────────────────────────────────

  var nextBeatTime   = 0;  // absolute audioCtx timestamp of next beat
  var nextBeatIndex  = 0;  // 0-based; negative = lead-in beat

  function startScheduler(myToken) {
    var beatDur      = getBeatDuration();
    var beatsPerBar  = getBeatsPerBar();
    var leadInBeats  = getLeadInBeats();
    var settings     = getSettings();
    var flatNotes    = window.srs_state.flatNotes;
    var totalBeats   = flatNotes.length
      ? flatNotes[flatNotes.length - 1].endBeat
      : 0;

    schedulerTimer = setInterval(function() {
      if (sessionToken !== myToken) { clearInterval(schedulerTimer); return; }

      while (nextBeatTime < audioCtx.currentTime + LOOKAHEAD_S) {
        var relBeat = nextBeatIndex;  // negative → lead-in

        if (relBeat < 0) {
          // Lead-in beat
          var beatInBar   = ((relBeat % beatsPerBar) + beatsPerBar) % beatsPerBar;
          var isDownbeat  = (beatInBar === 0);
          if (settings.metronome) {
            metronome.scheduleClick(audioCtx, nextBeatTime, isDownbeat);
          }
          var leadInDone  = leadInBeats + relBeat + 1;
          document.dispatchEvent(new CustomEvent('srs_beat', {
            detail: {
              phase:            'lead_in',
              beatInBar:        beatInBar + 1,
              isDownbeat:       isDownbeat,
              when:             nextBeatTime,
              leadInBeatsDone:  leadInDone,
              leadInBeatsTotal: leadInBeats,
            }
          }));
        } else {
          // Score beat
          var beatInBar2 = relBeat % beatsPerBar;
          var isDown2    = (beatInBar2 === 0);
          if (settings.metronome) {
            metronome.scheduleClick(audioCtx, nextBeatTime, isDown2);
          }
          document.dispatchEvent(new CustomEvent('srs_beat', {
            detail: {
              phase:      'playing',
              beatInBar:  beatInBar2 + 1,
              isDownbeat: isDown2,
              when:       nextBeatTime,
            }
          }));
        }

        nextBeatIndex++;
        nextBeatTime += beatDur;
      }
    }, SCHEDULER_MS);
  }

  function stopScheduler() {
    clearInterval(schedulerTimer);
    schedulerTimer = null;
  }

  // ── RAF loop (visual updates) ─────────────────────────────────────────────

  function startRaf(myToken) {
    var beatDur   = getBeatDuration();
    var leadInS   = getLeadInBeats() * beatDur;
    var positions = window.srs_state.renderedPositions;
    var flatNotes = window.srs_state.flatNotes;
    var ph        = document.getElementById('playhead');
    var lastRowIdx = -1;

    function frame() {
      if (sessionToken !== myToken) return;
      rafId = requestAnimationFrame(frame);

      if (!startTime) return;
      var transport = audioCtx.currentTime - startTime;

      // Still in lead-in
      if (transport < leadInS) return;

      // Score-relative seconds
      var scoreS    = transport - leadInS;
      var scoreBeat = scoreS / beatDur;

      // Find current note index
      var noteIdx = flatNotes.length - 1;
      for (var i = 0; i < flatNotes.length; i++) {
        if (flatNotes[i].startBeat <= scoreBeat && scoreBeat < flatNotes[i].endBeat) {
          noteIdx = i;
          break;
        }
      }

      // Check finished
      if (scoreBeat >= flatNotes[flatNotes.length - 1].endBeat) {
        ph.style.display = 'none';
        stopRaf();
        stopScheduler();
        setState('finished');
        return;
      }

      var note     = flatNotes[noteIdx];
      var pos      = positions[noteIdx];
      if (!pos) return;

      // Interpolate x within the note
      var noteFrac = (scoreBeat - note.startBeat) / note.beats;
      noteFrac     = Math.min(1, Math.max(0, noteFrac));
      var x        = pos.xStart + (pos.xEnd - pos.xStart) * noteFrac;

      ph.style.left   = x + 'px';
      ph.style.top    = pos.yTop + 'px';
      ph.style.height = (pos.yBottom - pos.yTop) + 'px';
      ph.style.display = 'block';

      // Scroll on row change
      if (pos.rowIndex !== lastRowIdx) {
        lastRowIdx = pos.rowIndex;
        ph.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }

    rafId = requestAnimationFrame(frame);
  }

  function stopRaf() {
    cancelAnimationFrame(rafId);
    rafId = null;
  }

  // ── Public API ────────────────────────────────────────────────────────────

  function play() {
    // Defensive guard
    var positions = window.srs_state.renderedPositions;
    var flatNotes = window.srs_state.flatNotes;
    if (!flatNotes.length || !positions.length) {
      showSrsWarning('No passage is ready. Press Generate first.');
      return;
    }

    if (state === 'playing' || state === 'lead_in') return;

    ensureAudioCtx();

    if (state === 'paused') {
      // Resume
      startTime = audioCtx.currentTime - pausedOffset;
    } else {
      // Fresh start (idle or finished)
      pausedOffset = 0;
      startTime    = audioCtx.currentTime;
      // Set nextBeatIndex to start of lead-in (negative offset)
      nextBeatIndex = -getLeadInBeats();
      nextBeatTime  = audioCtx.currentTime;
      setState('lead_in');
    }

    var myToken = ++sessionToken;
    startScheduler(myToken);
    startRaf(myToken);

    // Transition from lead_in to playing after lead-in duration
    var leadInS = getLeadInBeats() * getBeatDuration();
    setTimeout(function() {
      if (sessionToken === myToken && state === 'lead_in') {
        setState('playing');
      }
    }, leadInS * 1000);
  }

  function pause() {
    if (state !== 'playing' && state !== 'lead_in') return;
    pausedOffset = audioCtx.currentTime - startTime;
    stopRaf();
    stopScheduler();
    setState('paused');
  }

  function reset() {
    stopRaf();
    stopScheduler();
    sessionToken++;   // invalidate any running callbacks
    pausedOffset = 0;
    startTime    = null;
    nextBeatIndex = 0;
    nextBeatTime  = 0;

    var ph = document.getElementById('playhead');
    var positions = window.srs_state.renderedPositions;
    if (positions && positions.length) {
      ph.style.left    = positions[0].xStart + 'px';
      ph.style.top     = positions[0].yTop   + 'px';
      ph.style.height  = (positions[0].yBottom - positions[0].yTop) + 'px';
      ph.style.display = 'block';
    } else {
      ph.style.display = 'none';
    }

    document.getElementById('srs-leadin-bar').classList.add('d-none');

    if (state !== 'idle') setState('idle');
  }

  function getState() {
    // Retained for debugging. Button state is driven by srs_state_change events.
    return state;
  }

  return { play: play, pause: pause, reset: reset, getState: getState };
})();
```

### Acceptance criteria
- Pressing Play dispatches `srs_state_change` with `state: 'lead_in'`.
- After lead-in, `srs_state_change` fires with `state: 'playing'`.
- Playhead moves across the score.
- Pressing Pause freezes the playhead; pressing Play resumes from the same position.
- Pressing Reset returns playhead to note 0 and dispatches `state: 'idle'`.
- At the end of the passage, state becomes `'finished'`.
- Metronome clicks (if enabled) are audible during both lead-in and playing.

---

## Phase 8 — Integration check

**No new files.** Verify the whole system works end-to-end.

### Checklist

- [ ] `/sight-reading-speed/` loads without JS errors in the browser console.
- [ ] Settings load from localStorage on page refresh.
- [ ] Generate produces a visible score.
- [ ] Changing clef and generating shows the correct clef.
- [ ] Key signature shown on staff matches the selected count and type.
- [ ] Selecting an invalid range (min ≥ max − 4 semitones) shows the warning div; no score is drawn.
- [ ] Deselecting all durations shows the warning div; no score is drawn.
- [ ] Pressing Play starts the playback immediately.
- [ ] Playhead moves continuously left-to-right across notes.
- [ ] Playhead moves to the next row when a new row begins.
- [ ] Pressing Pause freezes the playhead.
- [ ] Pressing Play again resumes from the same position (not from the start).
- [ ] Pressing Reset returns the playhead to the first note.
- [ ] Metronome toggle: when on, clicks are audible; when off, silence.
- [ ] Downbeat click is higher-pitched than upbeat click.
- [ ] Passage finishes, state becomes Finished, playhead disappears.
- [ ] Resizing the window while paused: pressing Generate re-renders correctly.
- [ ] Keyboard: Space → play/pause, R → reset, G → generate (implement as a final polish step in the inline script).

### Keyboard shortcuts (add to `bindControls()`)
```js
document.addEventListener('keydown', function(e) {
  // Ignore if focus is inside an input or select
  if (['INPUT','SELECT','TEXTAREA'].indexOf(e.target.tagName) !== -1) return;
  if (e.key === ' ') {
    e.preventDefault();
    var ps = window.srs_state.playbackState;
    if (ps === 'playing' || ps === 'lead_in') {
      playback_manager.pause();
    } else if (ps === 'paused' || ps === 'idle' || ps === 'finished') {
      playback_manager.play();
    }
  }
  if (e.key === 'r' || e.key === 'R') playback_manager.reset();
  if (e.key === 'g' || e.key === 'G') regenerateScore();
});
```

---

## Dependency and load order

```
base.html loads:
  project.js          ← provides window.cache
  vendor/bootstrap.bundle.min.js

index.html loads (in this order):
  js/vexflow.js                          ← provides window.Vex
  sightreadingspeed/js/settings_manager.js
  sightreadingspeed/js/music_theory.js
  sightreadingspeed/js/score_generator.js
  sightreadingspeed/js/score_renderer.js
  sightreadingspeed/js/metronome.js
  sightreadingspeed/js/playback_manager.js
  <inline bootstrap script>              ← defines window.srs_state, calls init()
```

Every module is a var-scoped IIFE that exposes a single `var` into the global scope.

---

## What NOT to do

- Do not add error boundaries, try/catch, or logging beyond what is listed.
- Do not add CSS files; use Bootstrap utility classes and inline styles as shown.
- Use `const` and `let` — the existing project uses modern JS throughout (verified in `notes/templates/js/stave_manager.js`). Arrow functions are fine.
- Do not add Django models, migrations, admin registrations, or API views.
- Do not add rests, tuplets, ties across barlines, dynamics, or articulations.
- Do not add instrument transposition.
- Do not add minor-mode selection.
