// score_generator.js
// Generates a musically coherent passage of bars using rule-based melodic logic.
// Depends on: music_theory (loaded before this file).

const score_generator = (() => {

  const pickRandom = (arr) => arr[Math.floor(Math.random() * arr.length)];

  const generateBar = (pitches, cells, prevPitchIdx) => {
    const cell = pickRandom(cells);
    const notes = [];
    let currentIdx = prevPitchIdx !== null ? prevPitchIdx : Math.floor(pitches.length / 2);
    // Clamp in case prevPitchIdx came from a different range
    currentIdx = Math.max(0, Math.min(pitches.length - 1, currentIdx));

    cell.forEach(duration => {
      const r = Math.random();
      let delta;
      if (r < 0.70) {
        delta = Math.random() < 0.5 ? 1 : -1;   // step
      } else if (r < 0.90) {
        delta = Math.random() < 0.5 ? 2 : -2;   // skip (third)
      } else {
        delta = 0;                                // repeat — avoided below
      }

      let nextIdx = currentIdx + delta;
      // Clamp to pitch range
      nextIdx = Math.max(0, Math.min(pitches.length - 1, nextIdx));
      // Avoid consecutive repeated pitch where possible
      if (nextIdx === currentIdx && pitches.length > 1) {
        nextIdx = currentIdx + (delta >= 0 ? 1 : -1);
        nextIdx = Math.max(0, Math.min(pitches.length - 1, nextIdx));
      }

      currentIdx = nextIdx;
      notes.push({ pitch: pitches[currentIdx], duration });
    });

    return { notes, lastIdx: currentIdx };
  };

  const generate = (settings) => {
    const pitches = music_theory.getAllowedPitches(settings);
    const cells   = music_theory.getValidRhythmicCells(settings);
    if (!pitches.length || !cells.length) return [];

    const scale    = music_theory.getScaleForKeySignature(
      settings.key_sig_type, settings.key_sig_count
    );
    const keyRoot  = scale[0];

    const bars    = [];
    let prevIdx   = null;

    for (let i = 0; i < settings.num_bars; i++) {
      const isLastBar = i === settings.num_bars - 1;
      const result    = generateBar(pitches, cells, prevIdx);

      if (isLastBar) {
        // End on a tonic pitch: prefer the one closest to the middle of the range
        const tonicPitches = pitches.filter(p => p.split('/')[0] === keyRoot);
        if (tonicPitches.length) {
          const midIdx     = Math.floor(tonicPitches.length / 2);
          const lastNote   = result.notes[result.notes.length - 1];
          lastNote.pitch   = tonicPitches[midIdx];
        }
      }

      bars.push({ notes: result.notes });
      prevIdx = result.lastIdx;
    }

    return bars;
  };

  return { generate };
})();
