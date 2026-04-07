# SIGHTREADINGSPEED – implementation plan

## Overview

**SIGHTREADINGSPEED** is a new top-level Django app, alongside the existing training apps such as `notes`, `tuning`, and `intervals`.

It is a **frontend-only sight-reading speed trainer** for musicians. The app generates a passage of notated music, renders it on the page, and moves a visual playhead through the score in real time. The user reads and plays from the notation themselves.

### explicit constraints

This feature is intentionally narrow in scope:

- **No Django models**
- **No API endpoints**
- **No server-side persistence**
- **No user-account integration**
- **No score audio playback**
- **No synthesis of the written notes**
- **No HTMX interactions required for core behaviour**
- **No external music-generation service, AI model, or API**

Django’s role is only to:

- register the app
- serve the template
- serve static assets

All generation, rendering, timing, metronome clicks, and settings persistence happen in the browser.

---

## 1. Django app scaffolding

### files to create

```text
sightreadingspeed/
├── __init__.py
├── apps.py
├── urls.py
├── views.py
├── static/
│   └── sightreadingspeed/
│       └── js/
│           ├── settings_manager.js
│           ├── music_theory.js
│           ├── score_generator.js
│           ├── score_renderer.js
│           ├── playback_manager.js
│           └── metronome.js
└── templates/
    └── sightreadingspeed/
        └── index.html
```

### `apps.py`

```python
from django.apps import AppConfig

class SightreadingspeedConfig(AppConfig):
    name = "sightreadingspeed"
```

### `views.py`

```python
from django.shortcuts import render

def index(request):
    return render(request, "sightreadingspeed/index.html")
```

### `urls.py`

```python
from django.urls import path
from . import views

app_name = "sightreadingspeed"

urlpatterns = [
    path("", views.index, name="index"),
]
```

### root URL registration

Add to `config/urls.py`:

```python
path("sight-reading-speed/", include("sightreadingspeed.urls")),
```

### installed apps

Add to `config/settings/base.py`:

```python
"sightreadingspeed",
```

---

## 2. Core architecture

The app is split into small browser-side modules with clear responsibilities.

### modules

- `settings_manager.js` – load/save UI settings via localStorage
- `music_theory.js` – pitch data, key-signature helpers, MIDI conversion, duration helpers
- `score_generator.js` – generate musically plausible passages
- `score_renderer.js` – render notation with VexFlow and record note positions
- `playback_manager.js` – transport clock, lookahead scheduling, playhead, state transitions
- `metronome.js` – optional Web Audio click track
- `index.html` – static UI shell and bootstrap logic

### app-level state

Because the JS modules are real static files (not `{% include %}`d), they share no closure. All inter-module globals must be explicitly `window`-scoped.

`window.srs_state` is initialised in the inline bootstrap `<script>` in `index.html`. Static JS files must **not** read from or write to `window.srs_state` at file-evaluation time; they may only access it inside exported functions invoked after bootstrap completes.

```js
// Initialised in the inline bootstrap script (index.html).
// Static files access this only inside functions, never at module load time.
window.srs_state = {
  settings: null,
  bars: [],
  flatNotes: [],
  renderedPositions: [],
  playbackState: 'idle',
  generationVersion: 0,
};
```

All static files must use `window.srs_state` explicitly — do not rely on bare-name fallthrough to `window`. This makes shared-state access grep-able and unambiguous.

The `cache` global (from `project.js`, loaded in `base.html`) is similarly available as a `window`-scoped global and requires no extra declaration.

### shared state ownership rules

To keep mutations predictable, each field of `window.srs_state` has exactly one writer:

| field | only written by |
|---|---|
| `settings` | `regenerateScore()` (and `init()` on load) |
| `bars` | `regenerateScore()` |
| `flatNotes` | `regenerateScore()` |
| `renderedPositions` | `score_renderer.render()` |
| `playbackState` | the `srs_state_change` event handler in `bindControls()` |
| `generationVersion` | `regenerateScore()` |

No other function may write these fields. Readers may access any field freely.

---

## 3. Settings and persistence

Settings are persisted in `localStorage` using the existing global `cache` helper pattern already used elsewhere in the project.

### storage key

```js
const KEY = 'srs_settings';
```

### settings schema

| key | type | default | description |
|---|---:|---|---|
| `bpm` | int | `60` | quarter-note beats per minute |
| `clef` | string | `"treble"` | `"treble"` or `"bass"` |
| `min_note` | string | `"C/4"` | lowest pitch allowed |
| `max_note` | string | `"G/5"` | highest pitch allowed |
| `durations` | array | `["q"]` | allowed durations: `"w"`, `"h"`, `"q"`, `"8"` |
| `time_signature` | string | `"4/4"` | `"4/4"`, `"3/4"`, `"2/4"` |
| `metronome` | bool | `false` | metronome click on/off |
| `lead_in_bars` | int | `1` | number of count-in bars |
| `num_bars` | int | `16` | generated passage length |
| `key_sig_type` | string | `"sharps"` | `"sharps"` or `"flats"` |
| `key_sig_count` | int | `0` | number of sharps or flats, `0` to `6` |

### manager API

```js
const settings_manager = (() => {
  const KEY = 'srs_settings';

  const DEFAULTS = {
    bpm: 60,
    clef: 'treble',
    min_note: 'C/4',
    max_note: 'G/5',
    durations: ['q'],
    time_signature: '4/4',
    metronome: false,
    lead_in_bars: 1,
    num_bars: 16,
    key_sig_type: 'sharps',
    key_sig_count: 0,
  };

  const sanitise = (raw) => {
    const s = { ...DEFAULTS, ...(raw || {}) };

    if (!Array.isArray(s.durations) || s.durations.length === 0) {
      s.durations = ['q'];
    }

    s.bpm = Math.min(200, Math.max(20, parseInt(s.bpm, 10) || DEFAULTS.bpm));
    s.lead_in_bars = Math.min(4, Math.max(1, parseInt(s.lead_in_bars, 10) || DEFAULTS.lead_in_bars));
    s.num_bars = Math.min(32, Math.max(4, parseInt(s.num_bars, 10) || DEFAULTS.num_bars));
    s.key_sig_count = Math.min(6, Math.max(0, parseInt(s.key_sig_count, 10) || 0));

    return s;
  };

  const load = () => sanitise(cache.get(KEY, {}));
  const save = (s) => cache.save(KEY, sanitise(s));
  const get = () => load();

  return { get, save, sanitise };
})();
```

### validation rules

Always validate browser-side before generate/render:

- `min_note` must be at least a **perfect fourth** (5 semitones) below `max_note`, using `pitchToMidi()` — not string comparison. A smaller range produces a monotone melody and should show a UI warning with a prompt to widen the range.
- at least one duration selected
- `bpm` within allowed range
- `lead_in_bars` within allowed range
- `num_bars` within allowed range (cap at **32** — see §8 performance note)
- `key_sig_count` within `0..6`
- selected durations must be capable of filling the chosen time signature using valid rhythmic cells

If validation fails, block generation and show a clear UI warning with an option to restore safe defaults.

---

## 4. Music generation – how to make it sound good to play

The goal is **not** to generate “random notes inside a range”. That produces awkward, unidiomatic, and musically unsatisfying material.

Instead, v1 should generate **simple tonal exercises that feel playable and coherent**.

### core principle

Generate passages using **lightweight rule-based tonal constraints**, not pure randomness.

This gives material that:

- sits inside a recognisable key area
- has melodic contour
- avoids ugly repeated jumps
- contains phrase direction
- feels like an exercise a teacher might actually hand out

### what “good sounding” means here

For this trainer, “good sounding” means:

- mostly stepwise movement
- occasional small skips
- strong tendency towards notes belonging to the selected key signature
- phrase endings that feel settled
- moderate rhythmic variety
- enough repetition to feel patterned, but not so much that it becomes trivial

### generation strategy

#### 4.1 choose a tonal pitch pool from the selected key signature

The user chooses:

- `0–6 sharps`, or
- `0–6 flats`

Examples:

- `0 sharps/flats` → C major / A minor pitch collection
- `1 sharp` → G major / E minor
- `2 sharps` → D major / B minor
- `1 flat` → F major / D minor
- `2 flats` → B♭ major / G minor

For v1, use the **major-scale pitch collection implied by the key signature**. That is simple, familiar, and makes the notation cleaner.

#### 4.2 favour diatonic notes

Most generated notes should come from the active scale. Chromatic notes should be out of scope for v1.

This keeps the music readable and consistent with the user’s chosen key signature.

#### 4.3 generate by phrase, not by note alone

Instead of choosing every pitch independently, generate short phrase shapes such as:

- ascending
- descending
- arch
- inverted arch
- neighbour motion
- repeated pattern with variation

Each phrase can last 1–4 bars.

#### 4.4 constrain melodic movement

Suggested defaults:

- around **70–80% stepwise motion**
- around **15–25% small skips** such as thirds or fourths
- around **0–5% larger leaps**
- if a larger leap occurs, bias the next note towards stepwise recovery in the opposite direction

This single rule greatly improves musicality.

#### 4.5 control repetition

Allow some:

- repeated rhythmic cells
- repeated 2–4 note pitch patterns
- sequence-like motion

But avoid:

- long runs of identical notes
- repeated large leaps
- direction changes every single note

#### 4.6 shape bar endings and final cadences

Phrase and passage endings should feel stable.

Heuristics:

- prefer scale-degree `1`, `3`, or `5` at cadence points
- strongly favour scale-degree `1` for the final note
- reduce rhythmic density in the final bar when possible
- avoid ending on unstable non-chord tones unless deliberately doing an “open” phrase ending

#### 4.7 keep rhythms idiomatic

Use a small set of rhythmic patterns that fit each time signature.

Example rhythmic cells in `4/4`:

- `q q q q`
- `h q q`
- `q h q`
- `q q h`
- `8 8 q q q`
- `q 8 8 q q`

This is better than random duration packing.

### recommended v1 music model

For v1, generate passages as:

- **single-line melodies**
- **major-key, diatonic**
- **key signature selected by the user**
- **rule-based phrase construction**
- **no rests initially**, unless you explicitly want them
- **no tuplets**
- **no articulation**
- **no slurs**
- **no dynamics**

This is enough to produce useful practice material without overcomplicating the renderer.

---

## 5. Key signatures

The user must be able to choose how many sharps or flats they want, from `0` to `6`.

### UI inputs

Use:

- a select for signature type: `Sharps` / `Flats`
- a numeric input or select for signature count: `0..6`

### behaviour

The selected key signature determines:

- the default scale pitch collection used by the generator
- the key signature shown on the staff
- the accidental spelling used when notes are rendered

### v1 simplification

For v1, map the selected key signature to a major-key pitch collection:

#### sharps

| count | key |
|---:|---|
| 0 | C major |
| 1 | G major |
| 2 | D major |
| 3 | A major |
| 4 | E major |
| 5 | B major |
| 6 | F♯ major |

#### flats

| count | key |
|---:|---|
| 0 | C major |
| 1 | F major |
| 2 | B♭ major |
| 3 | E♭ major |
| 4 | A♭ major |
| 5 | D♭ major |
| 6 | G♭ major |

This is enough for coherent generation and staff rendering.

### VexFlow key signature strings

`stave.addKeySignature()` expects specific string values. The mapping from count/type to VexFlow string must live in `music_theory.js`:

```js
const KEY_SIG_TO_VEXFLOW = {
  sharps: { 0: 'C', 1: 'G', 2: 'D', 3: 'A', 4: 'E', 5: 'B', 6: 'F#' },
  flats:  { 0: 'C', 1: 'F', 2: 'Bb', 3: 'Eb', 4: 'Ab', 5: 'Db', 6: 'Gb' },
};

const getVexFlowKeyString = (type, count) => KEY_SIG_TO_VEXFLOW[type][count];
// e.g. getVexFlowKeyString('flats', 2) → 'Bb'
// Used as: stave.addKeySignature(getVexFlowKeyString(...))
```

Export `getVexFlowKeyString` from `music_theory.js`. The renderer calls it when drawing the opening stave.

### note spelling

Avoid enharmonic ambiguity by spelling notes according to the selected signature family.

Examples:

- in flat keys, prefer `B♭` not `A#`
- in sharp keys, prefer `F#` not `G♭`

This should be handled centrally in `music_theory.js`.

---

## 6. Pitch data and theory helpers

Create a small helper module to keep theory logic out of the generator.

### `music_theory.js` responsibilities

- define available pitch names by clef/range
- map key-signature settings to scale pitch classes
- provide VexFlow-friendly pitch strings
- convert pitch strings to numeric pitch values for logic
- parse time signatures
- convert durations to beats
- validate rhythmic configuration
- flatten bar/note structures for playback
- provide spelling helpers for sharps vs flats

### pitch range source

Use a static list covering at least `C/2` to `C/7`, since bass defaults may go below `C/3`.

Example:

```js
const CHROMATIC_SCALE = [
  "C/2","C#/2","D/2","D#/2","E/2","F/2","F#/2","G/2","G#/2","A/2","A#/2","B/2",
  "C/3","C#/3","D/3","D#/3","E/3","F/3","F#/3","G/3","G#/3","A/3","A#/3","B/3",
  "C/4","C#/4","D/4","D#/4","E/4","F/4","F#/4","G/4","G#/4","A/4","A#/4","B/4",
  "C/5","C#/5","D/5","D#/5","E/5","F/5","F#/5","G/5","G#/5","A/5","A#/5","B/5",
  "C/6","C#/6","D/6","D#/6","E/6","F/6","F#/6","G/6","G#/6","A/6","A#/6","B/6",
  "C/7"
];
```

### numeric pitch handling

All pitch comparisons must use numeric conversion, not lexical string comparison.

Add a required helper such as:

```js
const pitchToMidi = (pitchString) => {
  // "C/4" -> 60
};
```

Use numeric values for:

- range validation
- sorting
- melodic interval calculation
- leap detection
- phrase contour logic

Use spelled pitch strings only for rendering and display.

### flattened note structure

`flattenBars()` converts the bar/note tree into a flat timeline that playback can consume directly without knowing about bars or rhythmic cells.

**Canonical shape** of each entry in the `flatNotes` array:

```js
{
  noteIndex: 0,       // absolute index across the entire passage
  barIndex:  0,       // which bar this note belongs to
  pitch:    "C/4",    // VexFlow pitch string
  duration: "q",      // VexFlow duration string
  beats:     1,       // numeric beat count (from durationToBeats())
  startBeat: 0,       // passage-relative beat at which this note begins
  endBeat:   1,       // passage-relative beat at which this note ends
}
```

`startBeat` and `endBeat` are accumulated across all previous bars and notes. The playback manager converts them to seconds using `beatDuration = 60 / bpm`.

### helper API sketch

```js
const music_theory = (() => {
  const pitchToMidi = (pitchString) => {};
  const parseTimeSignature = (ts) => ({ beatsPerBar: 4, beatUnit: 4 });
  const durationToBeats = (dur) => ({ 'w': 4, 'h': 2, 'q': 1, '8': 0.5 }[dur]);
  const getScaleForKeySignature = (type, count) => {};
  const getVexFlowKeyString = (type, count) => {};
  const getAllowedPitches = (settings) => {};
  const getValidRhythmicCells = (settings) => {};
  const flattenBars = (bars) => { /* returns flatNotes[] per canonical shape above */ };

  return {
    pitchToMidi,
    parseTimeSignature,
    durationToBeats,
    getScaleForKeySignature,
    getVexFlowKeyString,
    getAllowedPitches,
    getValidRhythmicCells,
    flattenBars,
  };
})();
```

---

## 7. Score generation

### output format

Generate an array of bars:

```js
[
  {
    notes: [
      { pitch: "C/4", duration: "q" },
      { pitch: "D/4", duration: "q" },
      { pitch: "E/4", duration: "h" }
    ]
  }
]
```

### generator rules

#### 7.1 rhythm generation

Do not fill bars using unconstrained random duration picks. Instead, choose from prebuilt rhythmic cells appropriate to the time signature and selected allowed durations.

Example approach:

1. build a bank of valid rhythmic cells for `2/4`, `3/4`, and `4/4`
2. filter cells to those using only enabled durations
3. if no valid cells remain, block generation and show a UI warning
4. assemble bars from compatible cells

For v1:

- every rhythmic cell must sum **exactly** to one bar
- **no ties across barlines**
- **no tuplets**

This gives much better results than raw random packing.

#### 7.2 pitch generation

For each phrase or bar:

1. choose a contour type
2. choose a starting note inside range
3. move mostly by scale step
4. allow occasional skips
5. avoid immediate repeated pitches unless rhythmically meaningful
6. recover after larger leaps
7. end important phrase points on stable notes

#### 7.3 phrase templates

Recommended simple phrase templates:

- **ascending** – mostly rising, cadence at top or step down
- **descending** – mostly falling, cadence at bottom
- **arch** – rise then fall
- **wave** – small alternating up/down motion
- **sequence** – short repeated motif shifted by step
- **neighbour** – tonic/mediant-centred motion with neighbour notes

#### 7.4 difficulty shaping

The generator can implicitly shape difficulty via settings:

- narrower pitch range = easier
- quarter notes only = easier
- more bars = greater endurance demand
- higher BPM = greater speed demand
- more extreme keys = greater reading complexity

### API

```js
const score_generator = (() => {
  const generate = (settings) => {
    // returns bars[]
  };

  return { generate };
})();
```

---

## 8. Score rendering

Use **VexFlow 4.2.5** from the existing static asset.

### layout strategy

Render the full score once per generated passage. The notation remains static. Only the playhead moves.

### render flow

1. fully clear `#score-container`
2. create a single SVG renderer
3. compute bars-per-row from available width
4. render bars row by row
5. first bar of each row gets clef; first bar of the score gets time signature and key signature
6. create `VF.StaveNote` objects for each note
7. format and draw voice(s)
8. record visual note positions for playback

### key signature rendering

The renderer must add the current key signature to the opening stave.

### coordinate extraction and SVG-to-CSS alignment

`note.getAbsoluteX()` returns coordinates in **SVG user-space**, not in CSS pixel space. The playhead is a CSS-positioned `<div>` overlaid on `#score-wrapper`. These two coordinate systems must be reconciled before writing `playhead.style.left`.

**Required approach:**

After rendering, read the SVG element's bounding rect to compute a scale factor:

```js
const svgEl = scoreContainer.querySelector('svg');
const svgRect = svgEl.getBoundingClientRect();
const wrapperRect = document.getElementById('score-wrapper').getBoundingClientRect();

// SVG viewBox width (user-space) vs rendered CSS width:
const svgViewBoxWidth = svgEl.viewBox.baseVal.width || svgEl.getAttribute('width');
const cssToSvgScale  = svgRect.width / svgViewBoxWidth;

// When positioning the playhead:
const cssX = note.getAbsoluteX() * cssToSvgScale
           + (svgRect.left - wrapperRect.left);
playhead.style.left = cssX + 'px';
```

Do **not** apply a VexFlow viewBox scale transform that differs from 1:1 — keep the renderer at native SVG pixels with no viewBox scaling to avoid the mismatch entirely where possible.

Store the `cssToSvgScale` and `svgLeft` offset at render time and reuse them in the playback loop. Recompute on every re-render (resize, new passage).

### recorded position data

Do not store only a note centre. Store richer layout info **in CSS pixels** (converted at record time, not at playback time):

```js
{
  noteIndex: 0,
  rowIndex: 0,
  xStart: 120,   // CSS px from left of #score-wrapper
  xCenter: 130,
  xEnd: 146,     // usually xStart of the next note; final note uses the fallback rule below
  yTop: 40,
  yBottom: 140,
}
```

**xEnd continuity rule:** After collecting all raw positions, set each note's `xEnd` to the `xStart` of the following note. For the final note, set `xEnd` to `xStart + (xCenter - xStart)`. This guarantees the playhead never jumps or stalls at barline boundaries — it glides continuously from one notehead to the next.

### responsive behaviour

On resize:

- automatically pause playback
- fully clear the old SVG
- re-render the existing bars
- recompute note positions
- require the user to resume manually

Attempting live coordinate correction during playback is out of scope for v1.

### performance cap

Cap `num_bars` at **32**. At 20 BPM in 4/4, 32 bars = ~384 seconds, which is already a very long exercise. Beyond 32 bars, VexFlow SVG rendering becomes slow (large DOM, many nodes) and the SVG height grows to the point of breaking scrolling. The validation in `settings_manager` must enforce this; the UI select/input must not offer values above 32.

### dynamic spacing

Where practical, allow formatter width or bar spacing to respond to rhythmic density so that whole-note bars are not overly stretched and denser bars are not cramped.

This is a quality goal for v1, but must not block a working first implementation.

### position ownership

The renderer is the **sole owner** of note position data. It stores positions internally and also writes them into shared state so the playback manager can access them without coupling to the renderer's API:

```js
// Inside render(), after computing all positions:
window.srs_state.renderedPositions = notePositions;
```

The playback manager reads positions via `window.srs_state.renderedPositions[i]` — not via a renderer getter. This means `playback_manager.js` never imports or calls `score_renderer` directly.

### API

```js
const score_renderer = (() => {
  let notePositions = [];

  const render = (bars, settings) => {
    // draw score, compute positions, then:
    notePositions = computedPositions;
    window.srs_state.renderedPositions = notePositions;
  };
  const getNoteCount = () => notePositions.length;

  return { render, getNoteCount };
})();
```

---

## 9. Playback manager

The playback manager drives timing, metronome scheduling, playhead movement, and state transitions.

### transport principle

During active playback, **`AudioContext.currentTime` is the single source of truth** for:

- beat timing
- note timing
- playhead interpolation

`requestAnimationFrame` is used only as a render/update loop for DOM and UI changes.

This avoids drift between audio timing and visual timing.

### states

```text
idle → lead_in → playing → paused → playing → finished
   ↘──────────── reset ─────────────↗
```

Recommended enum values:

- `idle`
- `lead_in`
- `playing`
- `paused`
- `finished`

### timing model

Quarter-note beat duration in seconds:

```js
60 / bpm
```

### lookahead scheduler

Use a short lookahead scheduler pattern:

- a scheduler loop checks `AudioContext.currentTime`
- if a beat boundary is approaching within the lookahead window, schedule the metronome click in advance
- update internal transport timing from the same audio clock
- interpolate the playhead from the same timing model

The DOM event system is not sample-accurate, so `srs_beat` should be treated as an application signal, not the fundamental timing authority.

### pause and resume

`AudioContext.currentTime` is monotonic and cannot be paused or reset. The playback manager must maintain an explicit offset to support mid-passage pause/resume.

```js
// Internal transport variables:
let startTime    = null;  // audioCtx.currentTime when beat 0 began
let pausedOffset = 0;     // how many seconds into the passage we paused

// On play/resume:
startTime = audioCtx.currentTime - pausedOffset;

// Transport position at any moment during playback:
const transportSeconds = audioCtx.currentTime - startTime;

// On pause:
pausedOffset = audioCtx.currentTime - startTime;
// (do NOT clear startTime — keep it for debugging if needed)

// On reset:
pausedOffset = 0;
startTime    = null;
```

Every beat-boundary check and every playhead interpolation reads `transportSeconds = audioCtx.currentTime - startTime`. After resume, `startTime` is reset so the expression gives the correct passage-relative time immediately.

### note timing

Use `durationToBeats()` from `music_theory.js`.

### playback start

Playback starts immediately at beat 0 when the Play button is pressed.

### playhead movement

The playhead should move **continuously**, not only jump note-to-note.

For each active note:

1. find the note’s start and end x-position
2. compute fraction of note duration elapsed from the transport clock
3. interpolate current x-position
4. position the playhead at the current row

This gives a proper reading-guide effect.

### scrolling

Avoid calling `scrollIntoView({ behavior: 'smooth' })` on every frame.

Instead:

- detect row changes
- scroll only when entering a new row, or when the playhead approaches the visible lower boundary

### beat events

At each beat boundary, dispatch:

```js
document.dispatchEvent(new CustomEvent('srs_beat', {
  detail: { beatInBar, isDownbeat }
}));
```

The metronome and UI flash logic can listen to this.

### teardown and race-condition safety

The playback manager must guarantee that only one active playback session exists at a time.

Maintain explicit handles such as:

- current animation frame ID
- current scheduler handle or timer
- current transport session token / version number

Whenever `play()`, `pause()`, `reset()`, `generate()`, or settings-triggered regeneration occurs:

- cancel the previous animation frame
- cancel or invalidate the previous scheduler loop
- ignore stale callbacks using the current session token
- prevent duplicate metronome clicks and ghost playheads

### defensive guard in play()

Before starting playback, `play()` must check that the score is ready:

```js
const play = () => {
  if (!window.srs_state.flatNotes.length || !window.srs_state.renderedPositions.length) {
    showSrsWarning('No passage is ready. Press Generate first.');
    return;
  }
  // ... proceed
};
```

In normal use this cannot happen because of auto-generation on load, but it protects against edge cases such as the user pressing Play before the initial render completes.

### API

```js
const playback_manager = (() => {
  const play  = () => {};
  const pause = () => {};
  const reset = () => {};
  // getState() is retained for debugging only.
  // Button visibility is driven by srs_state_change events, not polling.
  const getState = () => state;

  return { play, pause, reset, getState };
})();
```

---

## 10. Metronome

The metronome uses the **Web Audio API** only.

### explicit scope

The metronome is the **only audio in the feature**.

There is **no playback of the score notes**.

### click synthesis

Use a short oscillator click:

```js
const click = (audioCtx, when, isDownbeat) => {
  const osc = audioCtx.createOscillator();
  const gain = audioCtx.createGain();

  osc.frequency.value = isDownbeat ? 1000 : 800;
  gain.gain.setValueAtTime(0.3, when);
  gain.gain.exponentialRampToValueAtTime(0.001, when + 0.05);

  osc.connect(gain).connect(audioCtx.destination);
  osc.start(when);
  osc.stop(when + 0.05);
};
```

### integration

The metronome must **not** listen to `srs_beat` for click scheduling. `srs_beat` is a DOM CustomEvent and is not sample-accurate. Scheduling audio from it will produce audible jitter.

Instead, the metronome is called **directly from the playback manager's lookahead scheduler loop**, which runs on `AudioContext.currentTime`. The scheduler passes the precise `when` timestamp to the metronome:

```js
// Inside playback_manager's scheduler loop:
if (nextBeatTime < audioCtx.currentTime + LOOKAHEAD) {
  if (settings_manager.get().metronome) {
    metronome.scheduleClick(audioCtx, nextBeatTime, isDownbeat);
  }
  // Also dispatch srs_beat for visual-only listeners (flash, status label):
  document.dispatchEvent(new CustomEvent('srs_beat', {
    detail: { beatInBar, isDownbeat, when: nextBeatTime }
  }));
  nextBeatTime += beatDuration;
}
```

`metronome.scheduleClick(audioCtx, when, isDownbeat)` uses the `when` argument for `osc.start(when)` and `osc.stop(when + 0.05)`. It never reads `audioCtx.currentTime` internally.

`srs_beat` events are for UI-only use (beat flash, countdown label). They must never drive audio.

- create the `AudioContext` lazily after a user gesture (first call to `play()`)
- only schedule clicks if `settings_manager.get().metronome === true`

---

## 11. UI template

### structure

`index.html` extends `base.html`.

The page is static and self-contained.

### layout

Use Bootstrap 5.

Main sections:

1. page title and short description
2. collapsible settings panel
3. status area
4. score area
5. transport controls

### controls

#### settings controls

- BPM slider
- clef select
- time signature select
- minimum note select
- maximum note select
- duration checkboxes
- metronome toggle
- number of bars input
- key signature type select: `Sharps` / `Flats`
- key signature count input or select: `0..6`
- explicit **Generate** button

#### transport controls

- Play
- Pause
- Reset

### recommended control logic

- **Generate** – create a new passage and render it
- **Play** – start the currently visible passage; never regenerates
- **Pause** – pause the current passage
- **Reset** – return to the beginning of the current passage without generating a new one

**Auto-generate rule:**
- The page auto-generates **once on initial load** so the user always arrives with a ready passage.
- After that, **Play always uses the currently visible passage** unless the user explicitly presses Generate.
- Changing a setting does **not** trigger auto-regeneration; it only becomes effective when Generate is pressed next.

This makes the UX predictable: what you see is always what Play will perform.

### validation warning area

All validation errors and configuration warnings must appear in a single dedicated Bootstrap alert area above the score. Never use `alert()` or `console.error()` alone.

Add to the template:

```html
<div id="srs-warning" class="alert alert-warning d-none" role="alert"></div>
```

Define two global helper functions in the inline bootstrap script:

```js
function showSrsWarning(message) {
  const el = document.getElementById('srs-warning');
  el.textContent = message;
  el.classList.remove('d-none');
}

function clearSrsWarning() {
  const el = document.getElementById('srs-warning');
  el.textContent = '';
  el.classList.add('d-none');
}
```

Call `clearSrsWarning()` at the start of `regenerateScore()`. Call `showSrsWarning(message)` in any validation check that blocks generation, then `return` early.

### lead-in UI

```html
<div id="lead-in-bar" class="d-none">
  <div class="progress">
    <div id="lead-in-progress" class="progress-bar bg-info" style="width:0%"></div>
  </div>
  <p id="lead-in-text" class="text-center mb-0">Lead-in: beat 1</p>
</div>
```

### score area

```html
<div id="score-wrapper" class="position-relative">
  <div id="score-container"></div>
  <div id="playhead"></div>
</div>
```

Recommended playhead CSS:

```css
#playhead {
  position: absolute;
  top: 0;
  left: 0;
  width: 2px;
  background: red;
  opacity: 0.7;
  pointer-events: none;
}
```

### status label

Add a simple text label:

- `Idle`
- `Lead-in`
- `Playing`
- `Paused`
- `Finished`

This is helpful for both users and debugging.

### optional visual metronome cue

Add a subtle visual cue on beats, especially the downbeat, such as a brief border or glow on the score wrapper. This is helpful when users play loud instruments and cannot easily hear the click.

---

## 12. Script loading

Prefer real static JS files over template-included JS fragments.

At the bottom of `index.html`:

```django
{% load static %}
<script src="{% static 'js/vexflow.js' %}"></script>
<script src="{% static 'sightreadingspeed/js/settings_manager.js' %}"></script>
<script src="{% static 'sightreadingspeed/js/music_theory.js' %}"></script>
<script src="{% static 'sightreadingspeed/js/score_generator.js' %}"></script>
<script src="{% static 'sightreadingspeed/js/score_renderer.js' %}"></script>
<script src="{% static 'sightreadingspeed/js/metronome.js' %}"></script>
<script src="{% static 'sightreadingspeed/js/playback_manager.js' %}"></script>
```

Then the inline bootstrap script. All helper functions below are defined in this same `<script>` block (not in any static file) and are therefore `window`-scoped globals accessible to the static modules:

```html
<script>
  // ── Shared state (window-scoped so static-file modules can read it) ──────
  window.srs_state = {
    settings: null,
    bars: [],
    flatNotes: [],
    renderedPositions: [],
    playbackState: 'idle',
    generationVersion: 0,
  };

  // ── UI helpers ────────────────────────────────────────────────────────────

  // Read all form controls and return a raw settings object.
  function gatherSettingsFromUI() {
    return {
      bpm:           parseInt(document.getElementById('srs-bpm').value, 10),
      clef:          document.getElementById('srs-clef').value,
      time_signature:document.getElementById('srs-timesig').value,
      min_note:      document.getElementById('srs-min-note').value,
      max_note:      document.getElementById('srs-max-note').value,
      durations:     [...document.querySelectorAll('.srs-duration:checked')]
                       .map(el => el.value),
      metronome:     document.getElementById('srs-metronome').checked,
      lead_in_bars:  parseInt(document.getElementById('srs-leadin').value, 10),
      num_bars:      parseInt(document.getElementById('srs-numbars').value, 10),
      key_sig_type:  document.getElementById('srs-keysig-type').value,
      key_sig_count: parseInt(document.getElementById('srs-keysig-count').value, 10),
    };
  }

  // Write a settings object back to all form controls.
  function applySettingsToUI(s) {
    document.getElementById('srs-bpm').value          = s.bpm;
    document.getElementById('srs-clef').value         = s.clef;
    document.getElementById('srs-timesig').value      = s.time_signature;
    document.getElementById('srs-min-note').value     = s.min_note;
    document.getElementById('srs-max-note').value     = s.max_note;
    document.getElementById('srs-metronome').checked  = s.metronome;
    document.getElementById('srs-leadin').value       = s.lead_in_bars;
    document.getElementById('srs-numbars').value      = s.num_bars;
    document.getElementById('srs-keysig-type').value  = s.key_sig_type;
    document.getElementById('srs-keysig-count').value = s.key_sig_count;
    document.querySelectorAll('.srs-duration').forEach(el => {
      el.checked = s.durations.includes(el.value);
    });
  }

  // Set button visibility to match transport state.
  function updateTransportButtons(state) {
    const play  = document.getElementById('btn-play');
    const pause = document.getElementById('btn-pause');
    const reset = document.getElementById('btn-reset');
    play.classList.toggle('d-none',  state === 'lead_in' || state === 'playing');
    pause.classList.toggle('d-none', state !== 'lead_in' && state !== 'playing');
    reset.classList.toggle('d-none', state === 'idle');
  }

  // Wire Generate, Play, Pause, Reset, and settings-change handlers.
  function bindControls() {
    document.getElementById('btn-generate').addEventListener('click', regenerateScore);
    document.getElementById('btn-play').addEventListener('click', () => playback_manager.play());
    document.getElementById('btn-pause').addEventListener('click', () => playback_manager.pause());
    document.getElementById('btn-reset').addEventListener('click', () => playback_manager.reset());

    // Transport button state mirrors playback_manager state transitions.
    document.addEventListener('srs_state_change', e => {
      updateTransportButtons(e.detail.state);
      window.srs_state.playbackState = e.detail.state;
    });
  }

  // ── Core actions ──────────────────────────────────────────────────────────

  function regenerateScore() {
    clearSrsWarning();
    playback_manager.reset();
    const settings = settings_manager.sanitise(gatherSettingsFromUI());

    // Validate before doing anything else.
    const minMidi = music_theory.pitchToMidi(settings.min_note);
    const maxMidi = music_theory.pitchToMidi(settings.max_note);
    if (maxMidi - minMidi < 5) {
      showSrsWarning('Note range is too narrow. Please choose a range of at least a perfect fourth (5 semitones).');
      return;
    }
    if (!music_theory.getValidRhythmicCells(settings).length) {
      showSrsWarning('The selected durations cannot fill a complete bar. Please enable at least one compatible duration.');
      return;
    }

    settings_manager.save(settings);
    window.srs_state.settings = settings;
    window.srs_state.generationVersion += 1;
    const bars      = score_generator.generate(settings);
    const flatNotes = music_theory.flattenBars(bars);
    window.srs_state.bars      = bars;
    window.srs_state.flatNotes = flatNotes;
    score_renderer.render(bars, settings);
  }

  // ── Init ─────────────────────────────────────────────────────────────────

  (function init() {
    const settings = settings_manager.get();
    window.srs_state.settings = settings;
    applySettingsToUI(settings);

    // Auto-generate on page load so the user always arrives with a ready
    // passage — they do not need to press Generate before pressing Play.
    regenerateScore();

    bindControls();
    updateTransportButtons('idle');
  })();
</script>
```

`playback_manager` dispatches `srs_state_change` (a CustomEvent with `{ detail: { state } }`) whenever its state machine transitions. This is the only channel `updateTransportButtons` uses — it never polls `playback_manager.getState()` on a timer.

---

## 13. Accessibility and UX

### minimum accessibility requirements

- proper `<label>` elements for all form controls
- keyboard focus states visible
- buttons operable by keyboard
- `aria-live` region for status changes if practical
- sensible contrast for playhead and countdown bar

### keyboard shortcuts

Optional but desirable:

- `Space` – play/pause
- `R` – reset
- `G` – generate new passage

### metronome accessibility

The downbeat/upbeat pitch distinction is useful, but should not be the only feedback channel forever. A small visual beat flash is recommended.

---

## 14. Implementation order

1. scaffold Django app and register URLs
2. build `index.html` skeleton and Bootstrap layout
3. implement `settings_manager.js`
4. implement `music_theory.js`, including `pitchToMidi()` and rhythm validation
5. implement `score_generator.js`
6. verify generation output in browser console
7. implement `score_renderer.js`
8. implement `music_theory.flattenBars()` and renderer position recording
9. implement `metronome.js`
10. implement `playback_manager.js` with a single-clock transport and lookahead scheduling
11. wire transport/button state
12. polish responsive layout and edge cases

---

## 15. Edge cases to handle

- one selected duration only
- invalid duration/time-signature combinations
- very slow BPM such as `20`
- very fast BPM such as `200`
- small note ranges — enforce minimum 5-semitone span between `min_note` and `max_note`; block generation with a UI warning if violated
- accidental-heavy key signatures
- 1-row versus many-row layout
- resetting during lead-in
- changing settings while paused
- pressing Generate repeatedly
- pressing Play repeatedly
- resizing the window after rendering

Recommended behaviour on window resize:

- pause playback
- re-render the current bars
- recompute note positions
- require the user to resume manually

---

## 16. Non-goals for v1

These are explicitly out of scope:

- Django models
- REST or JSON APIs
- server-side storage
- user accounts integration
- score-note audio playback
- MIDI export
- live performance capture
- mic input / pitch detection
- adaptive difficulty based on performance history
- instrument transposition
- minor-mode selection
- rests
- articulations, slurs, dynamics, ornaments
- tuplets
- polyphony
- harmony generation
- AI-generated music
- external music APIs

---

## 17. Summary of the musical and technical approach

To generate material that sounds good for users to play, use a **rule-based tonal melody generator** with these principles:

- respect the user-selected key signature
- use a diatonic pitch pool
- generate by phrase shape
- prefer stepwise motion
- use only occasional small skips
- resolve larger leaps by opposite-direction recovery
- use stable notes at phrase endings
- build rhythms from a bank of valid musical cells rather than raw randomness

To keep transport behaviour robust, use these technical principles:

- `AudioContext.currentTime` is the single timing authority during playback
- `requestAnimationFrame` is for rendering only
- schedule audio using a short lookahead window
- use numeric pitch values for all musical logic
- fully re-render and recalculate positions on resize
- ensure strict teardown so only one playback session can exist at a time

That gives passages that feel coherent, readable, and satisfying without requiring models, APIs, score audio, or server logic.
