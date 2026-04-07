// music_theory.js
// Pure theory helpers. No DOM access. No window.srs_state access at load time.

const music_theory = (() => {

  // ── Chromatic scale C2–C7 (VexFlow pitch strings) ────────────────────────
  const CHROMATIC_SCALE = [
    'C/2','C#/2','D/2','D#/2','E/2','F/2','F#/2','G/2','G#/2','A/2','A#/2','B/2',
    'C/3','C#/3','D/3','D#/3','E/3','F/3','F#/3','G/3','G#/3','A/3','A#/3','B/3',
    'C/4','C#/4','D/4','D#/4','E/4','F/4','F#/4','G/4','G#/4','A/4','A#/4','B/4',
    'C/5','C#/5','D/5','D#/5','E/5','F/5','F#/5','G/5','G#/5','A/5','A#/5','B/5',
    'C/6','C#/6','D/6','D#/6','E/6','F/6','F#/6','G/6','G#/6','A/6','A#/6','B/6',
    'C/7',
  ];

  // ── Key signature → VexFlow stave string ────────────────────────────────
  const KEY_SIG_TO_VEXFLOW = {
    sharps: { 0: 'C', 1: 'G', 2: 'D', 3: 'A', 4: 'E', 5: 'B', 6: 'F#' },
    flats:  { 0: 'C', 1: 'F', 2: 'Bb', 3: 'Eb', 4: 'Ab', 5: 'Db', 6: 'Gb' },
  };

  // ── Scale pitch classes per key ───────────────────────────────────────────
  const KEY_SCALES = {
    C:    ['C', 'D', 'E', 'F', 'G', 'A', 'B'],
    G:    ['G', 'A', 'B', 'C', 'D', 'E', 'F#'],
    D:    ['D', 'E', 'F#', 'G', 'A', 'B', 'C#'],
    A:    ['A', 'B', 'C#', 'D', 'E', 'F#', 'G#'],
    E:    ['E', 'F#', 'G#', 'A', 'B', 'C#', 'D#'],
    B:    ['B', 'C#', 'D#', 'E', 'F#', 'G#', 'A#'],
    'F#': ['F#', 'G#', 'A#', 'B', 'C#', 'D#', 'E#'],
    F:    ['F', 'G', 'A', 'Bb', 'C', 'D', 'E'],
    Bb:   ['Bb', 'C', 'D', 'Eb', 'F', 'G', 'A'],
    Eb:   ['Eb', 'F', 'G', 'Ab', 'Bb', 'C', 'D'],
    Ab:   ['Ab', 'Bb', 'C', 'Db', 'Eb', 'F', 'G'],
    Db:   ['Db', 'Eb', 'F', 'Gb', 'Ab', 'Bb', 'C'],
    Gb:   ['Gb', 'Ab', 'Bb', 'Cb', 'Db', 'Eb', 'F'],
  };

  // ── Duration → beats ─────────────────────────────────────────────────────
  const DURATION_BEATS = { w: 4, h: 2, q: 1, '8': 0.5, '16': 0.25 };

  // ── Rhythmic cell banks (cells sum exactly to one bar) ───────────────────
  const RHYTHMIC_CELLS = {
    '4/4': [
      ['q', 'q', 'q', 'q'],
      ['h', 'q', 'q'],
      ['q', 'h', 'q'],
      ['q', 'q', 'h'],
      ['h', 'h'],
      ['w'],
      ['8', '8', 'q', 'q', 'q'],
      ['q', '8', '8', 'q', 'q'],
      ['q', 'q', '8', '8', 'q'],
      ['16', '16', '16', '16', 'q', 'q', 'q'],
      ['q', '16', '16', '16', '16', 'q', 'q'],
      ['q', 'q', '16', '16', '16', '16', 'q'],
      ['q', 'q', 'q', '16', '16', '16', '16'],
      ['8', '16', '16', 'q', 'q', 'q'],
      ['q', '8', '16', '16', 'q', 'q'],
      ['q', 'q', '8', '16', '16', 'q'],
    ],
    '3/4': [
      ['q', 'q', 'q'],
      ['h', 'q'],
      ['q', 'h'],
      ['8', '8', 'q', 'q'],
      ['q', '8', '8', 'q'],
      ['16', '16', '16', '16', 'q', 'q'],
      ['q', '16', '16', '16', '16', 'q'],
      ['q', 'q', '16', '16', '16', '16'],
    ],
    '2/4': [
      ['q', 'q'],
      ['h'],
      ['8', '8', 'q'],
      ['q', '8', '8'],
      ['16', '16', '16', '16', 'q'],
      ['q', '16', '16', '16', '16'],
      ['8', '16', '16', 'q'],
    ],
  };

  // ── Note name → semitone offset ──────────────────────────────────────────
  const NOTE_SEMITONES = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4, 'Fb': 4, 'F': 5, 'E#': 5, 'F#': 6, 'Gb': 6,
    'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10,
    'B': 11, 'Cb': 11, 'B#': 0,
  };

  // ── Public API ────────────────────────────────────────────────────────────

  const getChromaticScale = () => CHROMATIC_SCALE.slice();

  const pitchToMidi = (pitchStr) => {
    // 'C/4' → 60, 'C#/4' → 61, 'A/4' → 69
    const [name, octStr] = pitchStr.split('/');
    let oct = parseInt(octStr, 10);
    if (name === 'Cb') oct -= 1;
    if (name === 'B#') oct += 1;
    return (oct + 1) * 12 + (NOTE_SEMITONES[name] ?? 0);
  };

  const getVexFlowKeyString = (type, count) => KEY_SIG_TO_VEXFLOW[type][count];

  const parseTimeSignature = (ts) => {
    const [num, denom] = ts.split('/').map(Number);
    return { beatsPerBar: num, beatUnit: denom };
  };

  const durationToBeats = (dur) => DURATION_BEATS[dur] ?? 1;

  const getScaleForKeySignature = (type, count) => {
    const key = KEY_SIG_TO_VEXFLOW[type][count];
    return (KEY_SCALES[key] || KEY_SCALES['C']).slice();
  };

  const getAllowedPitches = (settings) => {
    const scale   = getScaleForKeySignature(settings.key_sig_type, settings.key_sig_count);
    const minMidi = pitchToMidi(settings.min_note);
    const maxMidi = pitchToMidi(settings.max_note);

    const pitches = [];
    for (let oct = 2; oct <= 7; oct++) {
      for (const name of scale) {
        const pitch = `${name}/${oct}`;
        const midi = pitchToMidi(pitch);
        if (midi >= minMidi && midi <= maxMidi) {
          pitches.push(pitch);
        }
      }
    }

    // Sort strictly by MIDI pitch so stepwise motion works properly
    pitches.sort((a, b) => pitchToMidi(a) - pitchToMidi(b));
    return pitches;
  };

  const getValidRhythmicCells = (settings) => {
    const cells   = RHYTHMIC_CELLS[settings.time_signature] || [];
    const allowed = settings.durations;
    return cells.filter(cell => cell.every(d => allowed.includes(d)));
  };

  const flattenBars = (bars) => {
    const flat = [];
    let beatCursor = 0;
    bars.forEach((bar, barIndex) => {
      bar.notes.forEach(note => {
        const beats = durationToBeats(note.duration);
        flat.push({
          noteIndex:  flat.length,
          barIndex,
          pitch:      note.pitch,
          duration:   note.duration,
          beats,
          startBeat:  beatCursor,
          endBeat:    beatCursor + beats,
        });
        beatCursor += beats;
      });
    });
    return flat;
  };

  return {
    getChromaticScale,
    pitchToMidi,
    getVexFlowKeyString,
    parseTimeSignature,
    durationToBeats,
    getScaleForKeySignature,
    getAllowedPitches,
    getValidRhythmicCells,
    flattenBars,
  };
})();
