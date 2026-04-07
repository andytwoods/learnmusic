// metronome.js
// Schedules Web Audio API click sounds at precise timestamps.
// scheduleClick() uses the `when` argument for osc.start() — it never
// calls audioCtx.currentTime internally. The caller provides the timestamp.

const metronome = (() => {

  const scheduleClick = (audioCtx, when, isDownbeat) => {
    const osc  = audioCtx.createOscillator();
    const gain = audioCtx.createGain();

    osc.frequency.value = isDownbeat ? 1000 : 800;
    gain.gain.setValueAtTime(0.3, when);
    gain.gain.exponentialRampToValueAtTime(0.001, when + 0.05);

    osc.connect(gain);
    gain.connect(audioCtx.destination);

    osc.start(when);
    osc.stop(when + 0.06);
  };

  return { scheduleClick };
})();
