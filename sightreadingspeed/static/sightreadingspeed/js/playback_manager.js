// playback_manager.js
// Owns the AudioContext transport: lookahead scheduler, RAF visual loop,
// state machine, lead-in, and playhead movement.
//
// Depends on: music_theory, metronome, settings_manager, window.srs_state.
// showSrsWarning() is defined in the inline bootstrap script in index.html.
//
// Pause/resume math:
//   On play/resume:  startTime = audioCtx.currentTime - pausedOffset
//   Transport pos:   transportSeconds = audioCtx.currentTime - startTime
//   On pause:        pausedOffset = audioCtx.currentTime - startTime
//   On reset:        pausedOffset = 0, startTime = null

const playback_manager = (() => {

  const LOOKAHEAD_S  = 0.1;   // seconds ahead to schedule audio
  const SCHEDULER_MS = 25;    // ms between scheduler ticks

  let audioCtx       = null;
  let state          = 'idle';
  let startTime      = null;   // audioCtx time when beat-0 of this segment began
  let pausedOffset   = 0;      // seconds into passage when paused
  let rafId          = null;
  let schedulerTimer = null;
  let sessionToken   = 0;      // incremented on play/reset; stale callbacks compare this

  // Scheduler-local beat tracking (reset on each play)
  let nextBeatTime   = 0;
  let nextBeatIndex  = 0;

  // ── Helpers ───────────────────────────────────────────────────────────────

  const setState = (newState) => {
    state = newState;
    document.dispatchEvent(new CustomEvent('srs_state_change', {
      detail: { state: newState },
    }));
  };

  const ensureAudioCtx = async () => {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    // resume() is async — must await so currentTime is valid before we use it
    if (audioCtx.state === 'suspended') await audioCtx.resume();
  };

  const getSettings    = () => window.srs_state.settings || settings_manager.get();
  const getBeatDur     = () => 60 / getSettings().bpm;
  const getBeatsPerBar = () => music_theory.parseTimeSignature(getSettings().time_signature).beatsPerBar;

  // ── Lookahead scheduler ───────────────────────────────────────────────────
  // Runs on setInterval. Schedules metronome clicks ahead of time using
  // audioCtx timestamps for sample-accurate playback.
  // srs_beat events are dispatched here for VISUAL use only — never for audio.

  const startScheduler = (myToken) => {
    const beatDur     = getBeatDur();
    const beatsPerBar = getBeatsPerBar();
    // Note: metronome setting is read fresh each tick so toggling during
    // playback takes effect immediately without restarting.

    schedulerTimer = setInterval(() => {
      if (sessionToken !== myToken) { clearInterval(schedulerTimer); return; }

      const useMetronome = getSettings().metronome;

      while (nextBeatTime < audioCtx.currentTime + LOOKAHEAD_S) {
        const beatInBar  = ((nextBeatIndex % beatsPerBar) + beatsPerBar) % beatsPerBar;
        const isDownbeat = beatInBar === 0;

        // Score beat
        if (useMetronome) {
          metronome.scheduleClick(audioCtx, nextBeatTime, isDownbeat);
        }
        document.dispatchEvent(new CustomEvent('srs_beat', {
          detail: {
            phase:      'playing',
            beatInBar:  beatInBar + 1,
            isDownbeat,
            when:       nextBeatTime,
          },
        }));

        nextBeatIndex++;
        nextBeatTime += beatDur;
      }
    }, SCHEDULER_MS);
  };

  const stopScheduler = () => {
    clearInterval(schedulerTimer);
    schedulerTimer = null;
  };

  // ── RAF visual loop ───────────────────────────────────────────────────────
  // Reads audioCtx.currentTime each frame to interpolate the playhead position.

  const startRaf = (myToken) => {
    const beatDur    = getBeatDur();
    const flatNotes  = window.srs_state.flatNotes;
    const totalBeats = flatNotes.length
      ? flatNotes[flatNotes.length - 1].endBeat
      : 0;
    const ph         = document.getElementById('playhead');
    let lastRowIdx   = -1;

    const frame = () => {
      if (sessionToken !== myToken) return;
      rafId = requestAnimationFrame(frame);

      if (startTime === null) return;

      const transport = audioCtx.currentTime - startTime;

      const scoreBeat = transport / beatDur;

      // Finished?
      if (scoreBeat >= totalBeats) {
        ph.style.display = 'none';
        stopRaf();
        stopScheduler();
        setState('finished');
        return;
      }

      // Find current note
      const positions = window.srs_state.renderedPositions;
      let noteIdx     = flatNotes.length - 1;
      for (let i = 0; i < flatNotes.length; i++) {
        if (flatNotes[i].startBeat <= scoreBeat && scoreBeat < flatNotes[i].endBeat) {
          noteIdx = i;
          break;
        }
      }

      const note = flatNotes[noteIdx];
      const pos  = positions[noteIdx];
      if (!pos) return;

      // Interpolate x within the note duration
      const noteFrac = Math.min(1, Math.max(0,
        (scoreBeat - note.startBeat) / note.beats
      ));
      const x = pos.xStart + (pos.xEnd - pos.xStart) * noteFrac;

      ph.style.left    = x + 'px';
      ph.style.top     = pos.yTop + 'px';
      ph.style.height  = (pos.yBottom - pos.yTop) + 'px';
      ph.style.display = 'block';

      // Scroll only on row change — instant, no smooth animation
      if (pos.rowIndex !== lastRowIdx) {
        lastRowIdx = pos.rowIndex;
        ph.scrollIntoView({ behavior: 'instant', block: 'nearest' });
      }
    };

    rafId = requestAnimationFrame(frame);
  };

  const stopRaf = () => {
    cancelAnimationFrame(rafId);
    rafId = null;
  };

  // ── Public API ────────────────────────────────────────────────────────────

  const play = async () => {
    // Defensive guard
    if (!window.srs_state.flatNotes.length || !window.srs_state.renderedPositions.length) {
      showSrsWarning('No passage is ready. Press Generate first.');
      return;
    }
    if (state === 'playing') return;

    // Await resume so currentTime is valid and AudioContext is running
    await ensureAudioCtx();

    // Small buffer ensures first scheduled click is always in the future
    const INIT_BUFFER = 0.05;

    if (state === 'paused') {
      // Resume: recalculate startTime so transport position is preserved
      startTime = audioCtx.currentTime - pausedOffset;
      // Restart scheduler from current position
      const beatDur     = getBeatDur();
      nextBeatTime  = audioCtx.currentTime + INIT_BUFFER;
      nextBeatIndex = Math.floor(pausedOffset / beatDur);
    } else {
      // Fresh start
      pausedOffset  = 0;
      startTime     = audioCtx.currentTime;
      nextBeatIndex = 0;
      nextBeatTime  = audioCtx.currentTime + INIT_BUFFER;
    }

    setState('playing');

    const myToken = ++sessionToken;
    startScheduler(myToken);
    startRaf(myToken);
  };

  const pause = () => {
    if (state !== 'playing') return;
    pausedOffset = audioCtx.currentTime - startTime;
    stopRaf();
    stopScheduler();
    setState('paused');
  };

  const reset = () => {
    stopRaf();
    stopScheduler();
    sessionToken++;   // invalidate any in-flight callbacks

    pausedOffset  = 0;
    startTime     = null;
    nextBeatIndex = 0;
    nextBeatTime  = 0;

    // Park playhead at note 0 (or hide if no score)
    const ph        = document.getElementById('playhead');
    const positions = window.srs_state.renderedPositions;
    if (positions && positions.length) {
      const p0 = positions[0];
      ph.style.left    = p0.xStart + 'px';
      ph.style.top     = p0.yTop   + 'px';
      ph.style.height  = (p0.yBottom - p0.yTop) + 'px';
      ph.style.display = 'block';
    } else {
      ph.style.display = 'none';
    }

    if (state !== 'idle') setState('idle');
  };

  // Retained for debugging. Button state is driven by srs_state_change events.
  const getState = () => state;

  return { play, pause, reset, getState };
})();
