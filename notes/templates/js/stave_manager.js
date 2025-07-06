// --- transpose.js -----------------------------------------------------------
const transpose = (function () {
    const KEY_TO_SEMITONES = {
        C: 0, "C#": 1, Db: 1,
        D: 2, "D#": 3, Eb: 3,
        E: 4, Fb: 4, "E#": 5,
        F: 5, "F#": 6, Gb: 6,
        G: 7, "G#": 8, Ab: 8,
        A: 9, "A#": 10, Bb: 10,
        B: 11, Cb: 11, "B#": 0,
    };

    const INT_TO_SHARP = [
        "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B",
    ];

    function getSemitoneShift(fromKey, toKey) {
        const fromVal = KEY_TO_SEMITONES[fromKey] ?? 0;
        const toVal = KEY_TO_SEMITONES[toKey] ?? 0;
        let diff = fromVal - toVal;
        if (diff > 6) diff -= 12;
        if (diff < -6) diff += 12;
        return diff;
    }

    function transposeNoteString(noteStr, shift) {
        const [pitchPart, octavePart] = noteStr.split("/");
        let octave = parseInt(octavePart, 10);
        const noteLetter = pitchPart[0].toUpperCase();
        const accidental = pitchPart.slice(1) || "";
        let pitchInt = KEY_TO_SEMITONES[noteLetter + accidental] ?? 0;
        pitchInt += shift;
        while (pitchInt < 0) {
            pitchInt += 12;
            octave -= 1;
        }
        while (pitchInt > 11) {
            pitchInt -= 12;
            octave += 1;
        }
        return `${INT_TO_SHARP[pitchInt]}/${octave}`;
    }

    // NB: these two placeholders are replaced by Django in the template
    const currentFromKey = "{{ key }}";        // e.g. "Bb"
    const currentToKey = "{{ transpose_key }}"; // e.g. "Bb"

    return function (noteStr) {
        if (currentFromKey === currentToKey) return noteStr;
        const shift = getSemitoneShift(currentFromKey, currentToKey);
        return transposeNoteString(noteStr, shift);
    };
})();


// --- stave‑manager.js --------------------------------------------------------
const stave_manager = (function () {
    const api = {};
    const VF = Vex.Flow;
    const div = document.getElementById("sheet");
    let containerWidth = div.clientWidth;
    let staveWidth = 200;
    const baseHeight = 200;
    let scaleFactor = 1.0;
    const minScaleFactor = 0.5;
    const maxScaleFactor = 2.0;
    const my_clef = "{{ clef }}";

    // --------------------------------------------------------------------------------
    // We *recreate* renderer + context every time we zoom.  Therefore we keep them in
    // mutable bindings.
    // --------------------------------------------------------------------------------
    let renderer = new VF.Renderer(div, VF.Renderer.Backends.SVG);

    let context = renderer.getContext();

    // NB: we do *not* call context.scale(); we resize the surface instead.
    let startX = (containerWidth - staveWidth * scaleFactor) / 2;
    let stave = new VF.Stave(startX, 40 * scaleFactor, staveWidth * scaleFactor)
        .addClef(my_clef)
        .setContext(context)
        .draw();

    // -----------------------------------------------------------------------------
    // helpers
    // -----------------------------------------------------------------------------
    function calcStemDirection(noteStr) {
        const centre = my_clef === "bass" ? {note: "D", octave: 3} : {note: "B", octave: 4};
        const [pitch, oct] = noteStr.split("/");
        const octave = parseInt(oct, 10);
        const cleanPitch = pitch.replace(/[#b]/g, "");
        const scaleOrder = "CDEFGAB";

        if (octave > centre.octave) return -1;
        if (octave < centre.octave) return 1;
        return scaleOrder.indexOf(cleanPitch) >= scaleOrder.indexOf(centre.note) ? -1 : 1;
    }

    // -----------------------------------------------------------------------------
    // core drawing routines --------------------------------------------------------
    // -----------------------------------------------------------------------------
    function freshRenderer() {

        div.innerHTML = "";

        renderer = new VF.Renderer(div, VF.Renderer.Backends.SVG);

        containerWidth = div.clientWidth;

        const w = containerWidth * scaleFactor * scaleFactor;
        const h = baseHeight * scaleFactor;
        //renderer.resize(w, h);

        context = renderer.getContext();
        context.svg.setAttribute("viewBox", `0 0 ${w} ${h}`);

        // new stave centred in the newly‑scaled surface
        startX = (w - staveWidth * scaleFactor) / 2;
        stave = new VF.Stave(startX, 40 * scaleFactor, staveWidth * scaleFactor)
            .addClef(my_clef)
            .setContext(context)
            .draw();
    }

    // redraw when the user zooms ----------------------------------------------
    function redraw() {
        freshRenderer();
        if (api.currentNote) api.drawNote(api.currentNote);
    }

    // public: draw a (black) note ---------------------------------------------
api.updateNote = function (noteStr) {
  api.currentNote = noteStr;
  freshRenderer();

  const transposed = transpose(noteStr);
  const stemDir = calcStemDirection(transposed);

  // 1. build the note with centre-alignment
  const note = new VF.StaveNote({
    keys: [transposed],
    duration: "q",
    clef: my_clef,
    stem_direction: stemDir,
    align_center: true,          // keep this
  });

  // 2. optional accidental
  let accidentalWidth = 0;
  if (/[#b]/.test(transposed)) {
    const acc = new VF.Accidental(transposed.includes("#") ? "#" : "b");
    note.addModifier(acc, 0);
    accidentalWidth = acc.getWidth();   // glyph width is known immediately
  }

  // 3. format & centre the tickable as usual
  const voice = new VF.Voice({num_beats: 1, beat_value: 4}).addTickables([note]);
  new VF.Formatter().joinVoices([voice]).format([voice], staveWidth / 2);

  // 4. Nudge the whole tickable left so the HEAD, not the group, is centred
  if (accidentalWidth) {
    note.setXShift(7);  // negative = move left :contentReference[oaicite:0]{index=0}
  }

  voice.draw(context, stave);
};


    // public: draw a red feedback note ----------------------------------------
    api.feedbackNote = function (noteStr) {
        freshRenderer(); // start from a clean surface so old red notes vanish

        const stemDir = calcStemDirection(noteStr);
        const red = new VF.StaveNote({
            keys: [noteStr],
            duration: "q",
            stem_direction: stemDir,
            align_center: true,
        }).setStyle({fillStyle: "red", strokeStyle: "red"});

        if (/[#b]/.test(noteStr)) {
            red.addModifier(new VF.Accidental(noteStr.includes("#") ? "#" : "b"), 0);
        }

        const voice = new VF.Voice({num_beats: 1, beat_value: 4}).addTickables([red]);
        new VF.Formatter().joinVoices([voice]).format([voice], staveWidth / 2);
        voice.draw(context, stave);
    };

    // zoom controls -----------------------------------------------------------
    api.increaseMagnification = function () {
        if (scaleFactor < maxScaleFactor) {
            scaleFactor = +(scaleFactor + 0.1).toFixed(2);
            redraw();
        }
    };

    api.decreaseMagnification = function () {
        if (scaleFactor > minScaleFactor) {
            scaleFactor = +(scaleFactor - 0.1).toFixed(2);
            redraw();
        }
    };

    // initial exposure --------------------------------------------------------
    api.currentNote = null;
    // keep backward‑compat alias
    api.drawNote = api.updateNote;
    freshRenderer(); // draw once so there is a stave even before the first note
    return api;
})();

// --- hook up the zoom buttons once DOM is ready ------------------------------
document.addEventListener("DOMContentLoaded", () => {
    const zoomInBtn = document.getElementById("increase-magnification");   // 🔍➖ icon
    const zoomOutBtn = document.getElementById("decrease-magnification");   // 🔍➕

    zoomInBtn.addEventListener("click", stave_manager.increaseMagnification);
    zoomOutBtn.addEventListener("click", stave_manager.decreaseMagnification);
});

