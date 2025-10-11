const session_manager = (function () {
    let api = {};

    const level = '{{ level }}';

    api.current_note = undefined;


    function sortNotesAndRandomize() {
        return window.progress_data.notes.slice().sort((a, b) => {
            if (a.n !== b.n) {
                return a.n - b.n;
            }
            return Math.random() - 0.5;
        });
    }

    api.next_note = function () {
        const sortedAndRandomized = sortNotesAndRandomize();
        api.current_note = sortedAndRandomized[0];
        return api.current_note;
    }

    api.update_data = function (rt, answer) {
        api.current_note['reaction_time_log'].push(parseInt(rt));
        api.current_note['correct'].push(answer);
        api.current_note['n'] = parseInt(api.current_note['n']) + 1;
    }

    return api;
}());


if (typeof module !== 'undefined') module.exports = session_manager;
