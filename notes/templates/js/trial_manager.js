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

        api.stop = function () {
            error_message_el.style.display = 'none';
            callback();
            callback = undefined;
        }

        api.start = function (message, _callback) {
            callback = _callback;
            correct_answer_el.innerText = message;
            error_message_el.style.display = 'block';
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
        session_manager.update_data(rt, answer);

        // this is NOT RT. Rather top left corner countdown.
        countdown_manager.start();

        const pruned_progress_data = session_manager.data_for_backend();
        sendResultsToBackend(pruned_progress_data);

        if (answer === true) {
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
            case 1:
                note_str += '#';
                break;
            case -1:
                note_str += 'b';
                break;
            case 2:
                note_str += '##';
                break;
            case -2:
                note_str += 'bb';
                break;
        }
        note_str += '/' + note['octave'];
        return note_str;
    }

    api.next = function () {
        const next_note = session_manager.next_note();
        const parsed_note = parse_note(next_note);
        document.current_note = parsed_note;
        timer.start();
        stave_manager.updateNote(parsed_note);
    }

    return api;
}());
