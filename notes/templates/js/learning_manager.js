const learning_manager = (function () {
    let api = {};
    let structuredInstrumentNotes;
    let masteryCorrectThreshold = 3; // Default threshold for correct answers
    let masteryReactionTimeThreshold = 2; // Default threshold for reaction time in seconds
    let streak = 0; // Correct streak tracker
    const recentNotesLog = []; // Queue for the last 5 `nextNote` selections

    // Helper function to determine if a note is mastered

    function isMastered(note) {
        // Limit the calculation to the last 3 answers
        const recentCorrect = note.correct ? note.correct.slice(-3) : [];

        //const recentReactionTimes = note.reaction_time_log ? note.reaction_time_log.slice(-3) : [];

        const totalCorrect = recentCorrect.filter(val => val === true).length;
        //const avgReactionTime = recentReactionTimes.length > 0
        //    ? recentReactionTimes.reduce((a, b) => parseInt(a) + parseInt(b), 0) / recentReactionTimes.length
        //    : Infinity;

        //console.log(recentCorrect, recentReactionTimes, totalCorrect, avgReactionTime);
        return (
            totalCorrect >= masteryCorrectThreshold
            // && avgReactionTime <= masteryReactionTimeThreshold
        );
    }

    // Helper function for deep equality comparison of notes
    function areNotesEqual(note1, note2) {
        return note1 && note2 &&
            note1.note === note2.note &&
            note1.octave === note2.octave &&
            note1.alter === note2.alter;
    }

    // Weighted randomization for notes
    function weightedRandomNote(notes) {
        const weights = notes.map(note => (isMastered(note) ? 1 : 5)); // Mastered notes have lower weights
        const totalWeight = weights.reduce((a, b) => a + b, 0);
        const random = Math.random() * totalWeight;
        let cumulativeWeight = 0;

        for (let i = 0; i < notes.length; i++) {
            cumulativeWeight += weights[i];
            if (random <= cumulativeWeight) {
                return notes[i];
            }
        }
    }


    api.next_note = (function () {
        let lastNote = null;

        return function () {

            const masteredNotes = window.progress_data.filter(isMastered);
            const nonMasteredNotes = window.progress_data.filter(note => !isMastered(note));
            let nextNote;
console.log(masteredNotes, nonMasteredNotes);
            if (nonMasteredNotes.length > 0) {
                const subset = nonMasteredNotes.slice(0, Math.min(3, nonMasteredNotes.length));
                nextNote = weightedRandomNote(subset);

                if (!nextNote || areNotesEqual(nextNote, lastNote)) {
                    nextNote = subset[0]; // Fallback to avoid infinite loop
                }
            } else if (masteredNotes.length > 0) {
                // Use mastered notes if all notes are mastered
                do {
                    nextNote = weightedRandomNote(masteredNotes);
                } while (areNotesEqual(nextNote, lastNote)); // Avoid repeat
            } else {
                // Introduce a new note if no non-mastered notes are available
                const availableNewNotes = structuredInstrumentNotes.filter(newNote =>
                    !window.progress_data.some(existingNote => areNotesEqual(newNote, existingNote))
                );

                if (availableNewNotes.length > 0) {
                    nextNote = availableNewNotes[0];
                    window.progress_data.push(nextNote);
                } else {
                    // Fallback to any note if no new notes are available
                    nextNote = weightedRandomNote(window.progress_data);
                }
            }

            lastNote = nextNote; // Update lastNote tracker
            return nextNote;
        };
    }());


    return api;
}());
