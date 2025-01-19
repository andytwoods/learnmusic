const session_manager = (function () {
    let api = {};

    const level = '{{ level }}';

    api.current_note = undefined;


    function sortAndRandomizeByN() {
        return window.progress_data.slice().sort((a, b) => {
            if (a.n !== b.n) {
                return a.n - b.n;
            }
            return Math.random() - 0.5;
        });
    }

    api.next_note = function () {
        api.current_note = sortAndRandomizeByN()[0];
        return api.current_note;
    }

    api.data_for_backend = function () {
        return window.progress_data.filter(note => note['n'] > 0);
    }

    api.update_data = function (rt, answer) {
        api.current_note['reaction_time_log'].push(rt);
        api.current_note['correct'].push(answer);
        api.current_note['n'] += 1;
    }

    return api;
}());
