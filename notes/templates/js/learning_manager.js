const learning_manager = (function () {
    let api = {};

    const ATTEMPTS_TO_CHECK_IF_MASTERED = 3
    const CORRECT_COUNT_THAT_INDICATES_MASTERED = 1;
    const RECENT_NOTES_LOG_SIZE = 2;

    // Helper function to determine if a note is mastered

    function isMastered(note) {
        // Limit to the last X answers
        const recentCorrect = note.correct ? note.correct.slice(-ATTEMPTS_TO_CHECK_IF_MASTERED) : [];

        // Count the number of correct answers in the last X attempts
        const totalCorrect = recentCorrect.filter(val => val === true).length;

        // Mastery condition: at least Y correct answers in the last X attempts
        return totalCorrect >= CORRECT_COUNT_THAT_INDICATES_MASTERED;
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

    function orderNotesByMastery(notes) {
        return notes.slice().sort((a, b) => {
            const masteryA = isMastered(a) ? 1 : 0;  // Determine if note is mastered
            const masteryB = isMastered(b) ? 1 : 0;

            // If mastery levels are the same, randomize order
            if (masteryA === masteryB) {
                return Math.random() - 0.5; // Randomize order when mastery is equal
            }

            // Otherwise, sort from least to most mastered
            return masteryA - masteryB;
        });
    }


    function processNotes(priorityNotes, recentNotesLog) {
        const orderedNotes = orderNotesByMastery(priorityNotes); // Get notes in what you described
        for (let note of orderedNotes) {
            // Ensures the note has not been recently tested
            if (!recentNotesLog.some(recentNote => areNotesEqual(recentNote, note))) {
                return note;
            }
        }
        return null; // No notes available that satisfy constraints
    }

    api.next_note = (function () {

        const recentNotesLog = []; // Tracks the last few notes played (e.g., 5)

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

            if (!nextNote) {
                nextNote = processNotes(window.progress_data, recentNotesLog);
            }
            else {
                const randomIndex = Math.floor(Math.random() * window.progress_data.length);
                nextNote = window.progress_data[randomIndex];
            }

            // Update the recent notes log
            if (nextNote) {
                recentNotesLog.push(nextNote);
                if (recentNotesLog.length > RECENT_NOTES_LOG_SIZE) {
                    recentNotesLog.shift(); // Maintain a queue of the last few notes
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
            return nextNote; // Return the selected note
        };
    })();

    return api;
}());
