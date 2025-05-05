const learning_manager = (function () {
    let api = {};

    const ATTEMPTS_TO_CHECK_IF_MASTERED = 3;
    const CORRECT_COUNT_THAT_INDICATES_MASTERED = 1;
    const RECENT_NOTES_LOG_SIZE = 2;

    // Weighted pick between mastered and unmastered
    let LIKELIHOOD_OF_MASTERED_NOTE = 0.8;

    // Number of notes to seed initially
    const NUMBER_OF_NEW_NOTES_TO_START_LEARNING_INITIALLY = 5;

    // Number of notes to add each time user chooses “Yes” in SweetAlert2
    const NUMBER_NEW_NOTES_TO_ADD_SAME_TIME = 3;

    // Track if we’ve done the initial “seed” of notes
    let initialNotesAdded = false;

    // Optional: track if we’ve already asked user about new notes
    // (so you don’t re-prompt them multiple times in the same session)
    let alreadyAskedAboutNewNotes = false;


    /*
     * 1) PARTIAL MASTERY:
     *    - We count how many of the last ATTEMPTS_TO_CHECK_IF_MASTERED attempts are correct.
     */

    function getMasteryScore(note) {
        const recent = note.correct
            ? note.correct.slice(-ATTEMPTS_TO_CHECK_IF_MASTERED)
            : [];
        return recent.filter(val => val).length; // 0..3
    }

    function isMastered(note) {
        // “Mastered” means >= CORRECT_COUNT_THAT_INDICATES_MASTERED correct
        // out of the last ATTEMPTS_TO_CHECK_IF_MASTERED answers
        const score = getMasteryScore(note) >= CORRECT_COUNT_THAT_INDICATES_MASTERED;
        console.log('here')
        return score;
    }

    // “allNotesMastered” check for the entire set
    function allNotesMastered(data) {
        if (!Array.isArray(data) || data.length === 0) return false;
        return data.every(isMastered);
    }

    /*
     * 2) PARTIAL-MASTERY ORDERING:
     *   - Sort by ascending mastery score (lowest first).
     *   - Among notes with the same score:
     *       if score=0 => stable order
     *       if score≥1 => random
     */
    function orderNotesByMastery(notes) {
        return notes.slice().sort((a, b) => {
            const scoreA = getMasteryScore(a);
            const scoreB = getMasteryScore(b);

            // Sort by ascending score
            if (scoreA === scoreB) {
                // For 0, keep stable ordering
                if (scoreA === 0) {
                    return 0;
                }
                // Score≥1 => random tie-break
                return Math.random() - 0.5;
            }
            return scoreA - scoreB;
        });
    }

    function areNotesEqual(note1, note2) {
        if (!note1 || !note2) return false;
        return (note1.note   === note2.note &&
                note1.octave === note2.octave &&
                note1.alter  === note2.alter);
    }

    // Helper to pick up to maxCount new notes from allPossibleNotes
    // that aren’t already in window.progress_data
    function pickNewNotes(maxCount) {
        const existing = window.progress_data || [];
        const missing = allPossibleNotes.filter(possibleNote =>
            !existing.some(existingNote => areNotesEqual(existingNote, possibleNote))
        );
        return missing.slice(0, maxCount);
    }

    /*
     * Return the first note from priorityNotes that is not in the recentNotesLog.
     * The “priorityNotes” are first sorted by partial mastery (lowest first).
     */
    function processNotes(priorityNotes, recentNotesLog) {
        const orderedNotes = orderNotesByMastery(priorityNotes);
        for (let note of orderedNotes) {
            if (!recentNotesLog.some(r => areNotesEqual(r, note))) {
                return note;
            }
        }
        return null;
    }

    api.set_LIKELIHOOD_OF_MASTERED_NOTE = function (value) {
        LIKELIHOOD_OF_MASTERED_NOTE = Math.max(0, Math.min(1, value));
    };

    api.next_note = (function () {
        const recentNotesLog = [];

        return function () {
            // 1) If user is brand new and we haven't seeded them yet
            if (!initialNotesAdded && window.progress_data.length === 0) {
                const firstBatch = pickNewNotes(NUMBER_OF_NEW_NOTES_TO_START_LEARNING_INITIALLY);
                window.progress_data.push(...firstBatch);
                initialNotesAdded = true;
                console.log("Added initial notes:", firstBatch);

                // Return the first note from the new batch
                return window.progress_data[0];
            }

            // 2) If all current notes are mastered => show SweetAlert
            //    (You can skip “alreadyAsked” if you want to ask multiple times.)
            if (allNotesMastered(window.progress_data)) {

                Swal.fire({
                    title: "Well done!",
                    text: "You’ve mastered all current notes. Would you like to add more?",
                    icon: "info",
                    showCancelButton: true,
                    confirmButtonText: "Yes, new notes!",
                    cancelButtonText: "No, keep practising these"
                }).then((result) => {
                    if (result.isConfirmed) {
                        const newNotes = pickNewNotes(NUMBER_NEW_NOTES_TO_ADD_SAME_TIME);
                        if (newNotes.length) {
                            window.progress_data.push(...newNotes);
                            console.log("Added new notes:", newNotes);
                        } else {
                            console.log("No more notes left to add!");
                        }
                    } else {
                        console.log("User chose not to add new notes.");
                    }
                });

                // Meanwhile, return a dummy “C4” note with skipRecording
                // so user sees something but it doesn't affect mastery stats
                return {
                    note: 'C',
                    octave: '4',
                    alter: '0',
                    skipRecording: true
                };
            }

            // Otherwise do normal flow (partial mastery picking logic)
            if (window.special_condition === 'first_trial') {
                return window.progress_data[0];
            }

            const masteredNotes    = window.progress_data.filter(isMastered);
            const nonMasteredNotes = window.progress_data.filter(n => !isMastered(n));

            let nextNote = null;
            const r = Math.random();

            // Weighted pick
            if (r < LIKELIHOOD_OF_MASTERED_NOTE && masteredNotes.length > 0) {
                nextNote = processNotes(masteredNotes, recentNotesLog);
            }
            if (!nextNote && nonMasteredNotes.length > 0) {
                nextNote = processNotes(nonMasteredNotes, recentNotesLog);
            }
            if (!nextNote) {
                nextNote = processNotes(window.progress_data, recentNotesLog);
            }
            if (!nextNote) {
                console.warn("All notes have been recently played. Resetting recentNotesLog.");
                recentNotesLog.length = 0;
                nextNote = processNotes(window.progress_data, recentNotesLog);
            }

            if (nextNote) {
                recentNotesLog.push(nextNote);
                if (recentNotesLog.length > RECENT_NOTES_LOG_SIZE) {
                    recentNotesLog.shift();
                }
            }

            // Optional debugging
            /*
            function logMasteryScores() {
                window.progress_data.forEach(n => {
                    const s = getMasteryScore(n);
                    console.log(
                      `Note: ${n.note}, Octave: ${n.octave}, Alter: ${n.alter}, Score: ${s}`
                    );
                });
            }
            logMasteryScores();
            */

            return nextNote;
        };
    })();

    return api;
}());
