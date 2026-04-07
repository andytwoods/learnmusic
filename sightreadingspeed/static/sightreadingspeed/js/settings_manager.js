// settings_manager.js
// Loads and saves user settings via the global `cache` helper (from project.js).
// Must not access window.srs_state at file-evaluation time.

const settings_manager = (() => {
  const KEY = 'srs_settings';

  const DEFAULTS = {
    bpm:            60,
    clef:           'treble',
    min_note:       'C/4',
    max_note:       'G/5',
    durations:      ['q'],
    time_signature: '4/4',
    metronome:      false,
    num_bars:       16,
    key_sig_type:   'sharps',
    key_sig_count:  0,
    score_scale:    1.0,
  };

  const sanitise = (raw) => {
    const s = Object.assign({}, DEFAULTS, raw || {});

    if (!Array.isArray(s.durations) || s.durations.length === 0) {
      s.durations = ['q'];
    }

    s.bpm           = Math.min(200, Math.max(20, parseInt(s.bpm,           10) || DEFAULTS.bpm));
    s.num_bars      = Math.min(100, Math.max(4,  parseInt(s.num_bars,      10) || DEFAULTS.num_bars));
    s.key_sig_count = Math.min(6,   Math.max(0,  parseInt(s.key_sig_count, 10) || 0));
    s.score_scale   = Math.min(2.0, Math.max(0.5, parseFloat(s.score_scale) || 1.0));

    if (!['treble', 'bass'].includes(s.clef))               s.clef           = DEFAULTS.clef;
    if (!['sharps', 'flats'].includes(s.key_sig_type))      s.key_sig_type   = DEFAULTS.key_sig_type;
    if (!['4/4', '3/4', '2/4'].includes(s.time_signature))  s.time_signature = DEFAULTS.time_signature;

    return s;
  };

  const get  = () => sanitise(cache.get(KEY, {}));
  const save = (s) => cache.save(KEY, sanitise(s));

  return { get, save, sanitise };
})();
