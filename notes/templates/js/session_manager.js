const session_manager = (function () {
    let api = {};

    const level = '{{ level }}';

    let current_note;
    let instrument_notes_data;



    api.setProgress = function (_progress_data) {
        api.progress_data = _progress_data;
        api.progress_data.forEach(note => {
            if (!note['reaction_time_log']) note['reaction_time_log'] = [];
            if (!note['correct']) note['correct'] = [];
        })
    }
    api.setNotes = function (_instrument_notes_data) {
        instrument_notes_data = _instrument_notes_data;
    }

    function sortAndRandomizeByN() {
        return api.progress_data.slice().sort((a, b) => {
            if (a.n !== b.n) {
                return a.n - b.n;
            }
            return Math.random() - 0.5;
        });
    }

    api.next_note = function () {
        if (window.level === 'beginner') current_note = learning_manager.next_note();
        else current_note = sortAndRandomizeByN()[0];
        return current_note;
    }

    api.data_for_backend = function () {
        return api.progress_data.filter(note => note['n'] > 0);
    }

    api.update_data = function (rt, answer) {
        current_note['reaction_time_log'].push(rt);
        current_note['correct'].push(answer);
        current_note['n'] += 1;
    }

    return api;
}());
