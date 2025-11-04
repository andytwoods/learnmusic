const trial_manager = (function () {
    let api = {};

    const ITI = 50;

    const timer = (function () {
        let api = {};
        let start = undefined;

        api.start = function () {
            start = performance.now();
        }
        api.stop = function () {
            const rt = performance.now() - start;
            return rt.toFixed(0)
        }

        return api;
    }());

    const error_message_manager = (function () {
        let api = {};
        let callback;
        const error_message_el = document.getElementById('error-message');
        const correct_answer_el = document.getElementById('correct-answer');

        const correct_message_el = document.getElementById('correct-message');

        // Elements for optional note guessing UI (note letters only, ignore octave)
        const guessUI = document.getElementById('note-guess-ui');
        const guessButtonsContainer = document.getElementById('note-guess-buttons');
        const guessSubmit = document.getElementById('note-guess-submit');
        const guessFeedback = document.getElementById('note-guess-feedback');
        const NOTE_BUTTON_SELECTOR = '.note-guess-btn';
        let selectedLetter = null;

        function getCurrentShownLetter() {
            const shown = (typeof keyAdjust === 'function') ? keyAdjust(document.current_note) : document.current_note;
            // shown like "C#/4" -> take first char (A-G)
            return (shown || '').charAt(0).toUpperCase();
        }

        function clearButtonStates() {
            if (!guessButtonsContainer) return;
            const btns = guessButtonsContainer.querySelectorAll(NOTE_BUTTON_SELECTOR);
            btns.forEach(btn => btn.classList.remove('active'));
        }

        function setupGuessButtons() {
            if (!guessButtonsContainer) return;
            // Bind click handlers once
            if (!guessButtonsContainer.dataset.bound) {
                guessButtonsContainer.addEventListener('click', function (e) {
                    const btn = e.target.closest(NOTE_BUTTON_SELECTOR);
                    if (!btn) return;
                    selectedLetter = btn.dataset.note;
                    clearButtonStates();
                    btn.classList.add('active');
                });
                guessButtonsContainer.dataset.bound = '1';
            }
            // Do not preselect any letter; wait for user choice
            selectedLetter = null;
            clearButtonStates();
        }

        function resetGuessUI() {
            if (!guessUI) return;
            guessUI.style.display = 'none';
            if (guessFeedback) {
                guessFeedback.textContent = '';
                guessFeedback.className = 'mt-2';
            }
            selectedLetter = null;
            clearButtonStates();
        }

        if (guessSubmit) {
            guessSubmit.addEventListener('click', function (e) {
                e.preventDefault();
                if (!selectedLetter) return;
                const currentLetter = getCurrentShownLetter();
                const correct = selectedLetter === currentLetter;
                if (guessFeedback) {
                    const shown = (typeof keyAdjust === 'function') ? keyAdjust(document.current_note) : document.current_note;
                    const shownLetter = currentLetter;
                    guessFeedback.textContent = correct ? 'Correct!' : `Not quite. The note is ${shownLetter}.`;
                    guessFeedback.className = 'mt-2 text-white fw-bold';
                }
            });
        }

        function hideErrorMessage() {
            error_message_el.parentElement.style.display = 'none';
        }

        document.getElementById('close-error-message-btn').onclick = hideErrorMessage;

        api.stop = function () {
            hideErrorMessage();
            resetGuessUI();
            if (callback) callback();
            callback = undefined;
        }

        api.start = function (message, _callback) {
            callback = _callback;
            correct_answer_el.innerHTML = message;
            error_message_el.parentElement.style.display = 'block';
            // Show optional guessing UI only when enabled (e.g., practice_try page)
            if (window.enable_note_guess && guessUI) {
                setupGuessButtons();
                guessUI.style.display = 'block';
            }
        }

        api.brief_correct_message = function () {
            correct_message_el.style.display = 'block';
            setTimeout(function () {
                correct_message_el.style.display = 'none';
            }, 500);
        }

        return api;
    }());


    let locked = false;

    api.answer = function (answer, mistake_message) {
        if (locked) {
            error_message_manager.stop();
            return;
        }
        locked = true;
        const rt = timer.stop();
        if (window.special_condition === 'first_trial') {
            window.special_condition = '';
        } else if (!session_manager.current_note.skipRecording) {
            session_manager.update_data(rt, answer);
            saveResult(session_manager.current_note, rt, answer);
        }

        // this is NOT RT. Rather top left corner countdown.
        feedback_manager.answer_given(rt, answer);

        if (answer === true) {
            error_message_manager.brief_correct_message();
            setTimeout(function () {
                api.next();
                locked = false;
            }, ITI);
        } else error_message_manager.start(mistake_message, function () {
            api.next();
            locked = false;
        });
    }

    function parse_note(note) {
        let note_str = note['note'];
        note_str = note_str.charAt(0);
        switch (note['alter']) {
            case '1':
                note_str += '#';
                break;
            case '-1':
                note_str += 'b';
                break;
            case '2':
                note_str += '##';
                break;
            case '-2':
                note_str += 'bb';
                break;
        }
        note_str += '/' + note['octave'];
        return note_str;
    }


    api.next = function (special) {
        const next_note = session_manager.next_note();
        const parsed_note = parse_note(next_note);
        document.current_note = parsed_note;
        timer.start();
        stave_manager.updateNote(parsed_note, next_note.signature);
    }

    return api;
}());

if (typeof module !== 'undefined') module.exports = stave_manager;
