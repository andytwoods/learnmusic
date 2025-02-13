api.next_note = (function () {
    const recentNotesLog = []; // Persistent across function calls

    return function () {
        if (window.special_condition === 'first_trial') {
            return window.progress_data[0];
        }

        const masteredNotes = window.progress_data.filter(isMastered);
        const nonMasteredNotes = window.progress_data.filter(note => !isMastered(note));

        let nextNote = null;

        // First, try to pick from non-mastered notes
        if (nonMasteredNotes.length > 0) {
            nextNote = processNotes(nonMasteredNotes, recentNotesLog);
        }

        // If no viable non-mastered note, move to mastered notes
        if (!nextNote && masteredNotes.length > 0) {
            nextNote = processNotes(masteredNotes, recentNotesLog);
        }

        // If no notes found, try all notes
        if (!nextNote) {
            nextNote = processNotes(window.progress_data, recentNotesLog);
        }

        // Ensure we don't return a note that was recently played
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

        function logProgressDataMastery() {
            if (!Array.isArray(window.progress_data)) {
                console.warn("window.progress_data is not an array.");
                return;
            }

            window.progress_data.forEach((note, index) => {
                const recentCorrect = note.correct ? note.correct.slice(-3) : [];
                const totalCorrect = recentCorrect.filter(val => val === true).length;
                const mastery = isMastered(note) ? "Mastered" : `Not mastered (Correct: ${totalCorrect}/3)`;

                console.log(`Note: ${note.note}, Octave: ${note.octave}, Alter: ${note.alter}, Mastery: ${mastery}`);
            });
        }

        logProgressDataMastery();
        return nextNote;
    };
})();
