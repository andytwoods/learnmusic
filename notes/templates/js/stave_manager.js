const transpose = (function () {

    const KEY_TO_SEMITONES = {
        // Keys
        'C': 0, 'C#': 1, 'Db': 1,
        'D': 2, 'D#': 3, 'Eb': 3,
        'E': 4, 'Fb': 4, 'E#': 5,
        'F': 5, 'F#': 6, 'Gb': 6,
        'G': 7, 'G#': 8, 'Ab': 8,
        'A': 9, 'A#': 10, 'Bb': 10,
        'B': 11, 'Cb': 11, 'B#': 0
    };

    const INT_TO_SHARP = [
        "C", "C#", "D", "D#", "E", "F",
        "F#", "G", "G#", "A", "A#", "B"
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
        const accidental = pitchPart.slice(1) || ""; // everything after the first char

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
        const newPitchName = INT_TO_SHARP[pitchInt];

        return `${newPitchName}/${octave}`;
    }

    let currentFromKey = '{{ key }}'
    let currentToKey = '{{ transpose_key }}';

    return function (noteStr) {

        if(currentFromKey===currentToKey) return noteStr;
        const semitoneShift = getSemitoneShift(currentFromKey, currentToKey);
        const updatedNote = transposeNoteString(noteStr, semitoneShift);
        return updatedNote

    };
}());


const stave_manager = (function () {
    let api = {};
    const VF = Vex.Flow;  // Reference VexFlow library
    const div = document.getElementById("sheet");
    let containerWidth = div.clientWidth;
    let staveWidth = 200; //
    const my_clef = '{{ clef }}';
    const my_key = '{{ key }}';
    const transpose_key = "{{ transpose_key }}";
    // Initialize VexFlow renderer
    const renderer = new VF.Renderer(div, VF.Renderer.Backends.SVG);
    renderer.resize(containerWidth, 200);  // Resize the SVG

    const context = renderer.getContext();  // Get the rendering context

    const startX = (containerWidth - staveWidth) / 2; // Calculate the starting point for centering
    let stave = new VF.Stave(startX, 40, staveWidth);
    stave.addClef(my_clef);

    //stave.addKeySignature('F');


    stave.setContext(context); // Attach the context to the stave
    stave.draw(context);       // Draw the stave

    function calc_stem_direct(note_str) {


        let middle_note, middle_octave;
        if (my_clef === 'treble') {
            middle_note = "B";
            middle_octave = 4;
        } else if (my_clef === 'bass') {
            middle_note = 'D'
            middle_octave = 3;
        } else if (my_clef === 'alto') {
            middle_note = 'C';
            middle_octave = 4;
        } else if (my_clef === 'tenor') {
            middle_note = 'C';
            middle_octave = 3;
        } else {
            throw new Error('stave not recognized: ' + my_clef);
        }

        const note_arr = note_str.split("/");
        const target_octave = parseInt(note_arr[1]);
        let target_note = note_arr[0];
        let target_accidental = '';

        if (target_note.indexOf('#') !== -1) {
            target_note = target_note.replace('#', '');
        } else if (target_note.indexOf('b') !== -1) {
            target_note = target_note.replace('b', '');
        }

        const scale_order = 'CDEFGAB';
        const target_scale_index = scale_order.indexOf(target_note);
        const middle_scale_index = scale_order.indexOf(middle_note);

        if (target_octave > middle_octave) {
            return -1;
        } else if (target_octave < middle_octave) {
            return 1;
        }

        if (target_scale_index >= middle_scale_index) {
            return -1;
        } else {
            return 1;
        }
    }

    api.updateNote = function (newNote) {
        newNote = transpose(newNote);
        renderer.getContext().svg.innerHTML = "";
        stave.setContext(context);
        stave.draw();

        let noteX = staveWidth / 2;

        const stemDirection = calc_stem_direct(newNote);

        // Create and explicitly set the stem direction
        const note = new VF.StaveNote({
            keys: [newNote],
            duration: "q",
            clef: my_clef,
            align_center: true,
            stem_direction: stemDirection // Explicitly set the stem direction
        });

        const voice = new VF.Voice({num_beats: 1, beat_value: 4});
        voice.addTickables([note]);

        // Handle accidentals
        if (newNote.indexOf('#') !== -1 || newNote.indexOf('b') !== -1) {

            VF.Accidental.applyAccidentals([voice]);
            noteX += 15;
        }


        // Format and draw the voice
        new VF.Formatter().joinVoices([voice]).format([voice], noteX);
        voice.draw(context, stave);
    };

    // Track DOM elements of feedback notes
    let feedbackNotes = [];

    api.feedback_note = function (note) {
        // Clear previously rendered red notes
        feedbackNotes.forEach(element => {
            if (element instanceof Node) {
                element.parentNode.removeChild(element); // Remove valid SVG nodes
            }
        });
        feedbackNotes = []; // Reset the array

        // Set the context for the stave
        stave.setContext(context);
        stave.draw();

        // Set X positions for the red note to appear
        const firstNoteX = staveWidth / 2;
        let secondNoteX = firstNoteX + 75; // Adjust spacing as desired

        // Calculate the stem direction for the new note
        const stemDirection = calc_stem_direct(note);

        // Create the new red note
        const redNote = new VF.StaveNote({
            keys: [note],
            duration: "q",
            align_center: true,
            stem_direction: stemDirection,
        });

        // Set the note color to red
        redNote.setStyle({fillStyle: "red", strokeStyle: "red"});

        // Handle accidentals (if sharp '#' or flat 'b' is present)
        if (note.indexOf("#") !== -1 || note.indexOf("b") !== -1) {
            redNote.addModifier(new VF.Accidental(note.includes("#") ? "#" : "b"), 0);
            secondNoteX += 15; // Adjust X position for accidentals
        }

        // Create a voice and add the new red note
        const voice = new VF.Voice({num_beats: 1, beat_value: 4});
        voice.addTickables([redNote]);

        // Format and draw the voice
        const contextGroup = context.openGroup(); // Create a group to isolate this note in SVG
        new VF.Formatter().joinVoices([voice]).format([voice], secondNoteX);
        voice.draw(context, stave);
        context.closeGroup();

        // Track the SVG group as feedback note for future removal
        feedbackNotes.push(contextGroup);
    };

    // 🔹 **Resize Stave on Container Resize**
    function resizeStave() {
        containerWidth = container.clientWidth;
        staveWidth = containerWidth * 0.8; // Stave should be 80% of container
        renderer.resize(containerWidth, 200);
        context.clear();

        stave = new VF.Stave(10, 40, staveWidth);
        stave.addClef(my_clef);
        stave.setContext(context).draw();
    }


    return api;
}());

