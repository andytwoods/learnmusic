const learning_manager = (function () {
    let api = {};

    const ATTEMPTS_TO_CHECK_IF_MASTERED = 3;
    const CORRECT_COUNT_THAT_INDICATES_MASTERED = 1;
    const RECENT_NOTES_LOG_SIZE = 2;
    let LIKELIHOOD_OF_MASTERED_NOTE = 0.8;

    // Helper function to determine if a note is mastered
    function isMastered(note) {
        // Limit to the last X answers
        const recentCorrect = note.correct ? note.correct.slice(-ATTEMPTS_TO_CHECK_IF_MASTERED) : [];
        // Count the number of correct answers in the last X attempts
        const totalCorrect = recentCorrect.filter(val => val === true).length;

        // Mastery condition: at least Y correct answers in the last X attempts
        return totalCorrect >= CORRECT_COUNT_THAT_INDICATES_MASTERED;
    }

    // Helper function for deep equality comparison
    function areNotesEqual(note1, note2) {
        if (!note1 || !note2) {
            console.warn("Invalid notes passed to areNotesEqual:", note1, note2);
            return false;
        }
        return note1.note === note2.note &&
               note1.octave === note2.octave &&
               note1.alter === note2.alter;
    }

    // Simple function to preserve the original order but group unmastered first
    function orderNotesByMastery(notes) {
        const unmastered = notes.filter(note => !isMastered(note));
        const mastered   = notes.filter(note =>  isMastered(note));
        return [...unmastered, ...mastered];
    }

    // Returns the first note from priorityNotes not in the recentNotesLog
    function processNotes(priorityNotes, recentNotesLog) {
        const orderedNotes = orderNotesByMastery(priorityNotes);
        for (let note of orderedNotes) {
            if (!recentNotesLog.some(recentNote => areNotesEqual(recentNote, note))) {
                return note;
            }
        }
        return null;
    }

    api.next_note = (function () {
        const recentNotesLog = []; // Persistent across calls

        return function () {
            if (window.special_condition === 'first_trial') {
                return window.progress_data[0];
            }

            const masteredNotes = window.progress_data.filter(isMastered);
            const nonMasteredNotes = window.progress_data.filter(note => !isMastered(note));

            let nextNote = null;

            // Weighted pick between mastered vs. unmastered
            const r = Math.random(); // random float between 0 and 1
            if (r < LIKELIHOOD_OF_MASTERED_NOTE && masteredNotes.length > 0) {
                // Try from mastered first
                nextNote = processNotes(masteredNotes, recentNotesLog);
            }
            // If we didn't pick from mastered (or none was viable), try unmastered
            if (!nextNote && nonMasteredNotes.length > 0) {
                nextNote = processNotes(nonMasteredNotes, recentNotesLog);
            }
            // If still no note, pick from all
            if (!nextNote) {
                nextNote = processNotes(window.progress_data, recentNotesLog);
            }

            // If still no note, reset the recentNotesLog so we can pick again
            if (!nextNote) {
                console.warn("All notes have been recently played. Resetting recent notes log.");
                recentNotesLog.length = 0; // Clear the log and retry
                nextNote = processNotes(window.progress_data, recentNotesLog);
            }

            // Update the recent notes log
            if (nextNote) {
                recentNotesLog.push(nextNote);
                if (recentNotesLog.length > RECENT_NOTES_LOG_SIZE) {
                    recentNotesLog.shift(); // Maintain queue size
                }
            }

            // Logging for debugging
            function logProgressDataMastery() {
                if (!Array.isArray(window.progress_data)) {
                    console.warn("window.progress_data is not an array.");
                    return;
                }
                window.progress_data.forEach((note, index) => {
                    const recentCorrect = note.correct ? note.correct.slice(-3) : [];
                    const totalCorrect = recentCorrect.filter(val => val === true).length;
                    const mastery = isMastered(note)
                        ? "Mastered"
                        : `Not mastered (Correct: ${totalCorrect}/3)`;
                    console.log(
                        `Note: ${note.note}, Octave: ${note.octave}, Alter: ${note.alter}, Mastery: ${mastery}`
                    );
                });
            }

            logProgressDataMastery();
            return nextNote;
        };
    })();

    return api;
}());
