const learning_manager = (function () {
    let api = {};

    api.next_note = function () {

        const countNs = session_manager.progress_data.reduce((sum, item) => sum + item.n, 0);
        const countCorrects = session_manager.progress_data.reduce((sum, item) => {
            return sum + item.correct.filter(value => value === true).length;
        }, 0);
        const percentageCorrect = countCorrects / countNs * 100;

        return session_manager.progress_data[0];
    }

    return api;

}());
