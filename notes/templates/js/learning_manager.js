const learning_manager = (function () {
    let api = {};
    let structuredInstrumentNotes;
    let masteryCorrectThreshold = 3; // Default threshold for correct answers
    let masteryReactionTimeThreshold = 2; // Default threshold for reaction time in seconds
    let streak = 0; // Correct streak tracker
    const recentNotesLog = []; // Queue for the last 5 `nextNote` selections
    const number_notes_to_initially_show = 3;
    const retries = 3;

    // Helper function to determine if a note is mastered

    function isMastered(note) {
        // Limit the calculation to the last 3 answers
        const recentCorrect = note.correct ? note.correct.slice(-3) : [];

        //const recentReactionTimes = Array.isArray(note.reaction_time_log)
        //        ? note.reaction_time_log.slice(-3)
        //        : [];

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
        if (!note1 || !note2) {
            console.warn("Invalid notes passed to areNotesEqual:", note1, note2);
            return false;
        }
        return note1.note === note2.note &&
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


    function processNotes(priorityNotes, recentNotesLog, selectionF) {
        if (priorityNotes.length > 0) {
            const subset = priorityNotes.slice(0, Math.min(number_notes_to_initially_show, priorityNotes.length));
            let nextNote = null;
            let attempts = 0; // Counter to track retry attempts

            // Retry logic to fetch a non-recent, non-repeated note
            do {
                nextNote = selectionF(subset); // Try selecting a note from the subset
                attempts++;
            } while (
                (attempts < retries) &&
                (!nextNote || recentNotesLog.some(recentNote => areNotesEqual(recentNote, nextNote)))
                );

            if (nextNote) {
                return nextNote;
            }
        }
        return null;
    }

    api.next_note = (function () {
        const recentNotesLog = []; // Tracks the last 5 notes played

        return function () {
            const masteredNotes = window.progress_data.filter(isMastered);
            const nonMasteredNotes = window.progress_data.filter(note => !isMastered(note));

            // Check non-mastered notes first, then mastered notes
            let nextNote =
                processNotes(nonMasteredNotes, recentNotesLog, weightedRandomNote) ||
                processNotes(masteredNotes, recentNotesLog, (els)=>els[0]);

            if (!nextNote) {
                // If neither non-mastered nor mastered notes are available, introduce a new note
                const availableNewNotes = structuredInstrumentNotes.filter(newNote =>
                    !window.progress_data.some(existingNote => areNotesEqual(newNote, existingNote))
                );

                if (availableNewNotes.length > 0) {
                    nextNote = availableNewNotes[0];
                    window.progress_data.push(nextNote);
                } else {
                    // Fallback: return any note if no new notes are available
                    nextNote = weightedRandomNote(window.progress_data);
                }
            }

            if (nextNote) {
                // Update recentNotesLog (maintain a queue of the last 5 notes)
                recentNotesLog.push(nextNote);
                if (recentNotesLog.length > 5) {
                    recentNotesLog.shift(); // Remove the oldest note if log exceeds size
                }
            }

            return nextNote; // Return the selected note
        };
    }());

    return api;
}());
