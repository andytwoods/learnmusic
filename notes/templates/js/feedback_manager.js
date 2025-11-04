const feedback_manager = (function () {
    let api = {};
    let response_count;
    let response_i = 0;
    let correct_count = 0;
    let rt_log = [];

    api.set_response_count = function (i) {
        response_count = i;
    }

    const counterSpan = document.getElementById("counter-value");

    api.answer_given = function (rt, answer) {
        response_i++;
        if (answer) {
            correct_count++;
            // below, greater than 1 as we skip the first
            // response to give people take time get used to UI
            if (response_i > 1) rt_log.push(Number(rt));
        }
        if (response_i === response_count) {
            finish();
            return;
        }
        // Assume these variables are available in scope:
        // response_count, response_i, correct_count, wrong_count
        const remaining = Math.max(0, Number(response_count) - Number(response_i));
        const wrong_count = Math.max(0, Number(response_i) - Number(correct_count));
        const crosses = wrong_count > 0
            ? Array.from({ length: wrong_count }, () => '<i class="fas fa-times text-danger" aria-hidden="true"></i>').join(' ')
            : '';
        counterSpan.innerHTML = `
            ${remaining} remaining
            <br>
            ${crosses}`;
    }

    function calc_stats() {
        const average_rt = rt_log.length ? (rt_log.reduce((a, b) => a + b, 0) / rt_log.length) : 0;
        const percent_correct = (response_count > 0) ? ((correct_count / response_count) * 100) : 0;
        // Inputs:
        // - percent_correct: 0..100
        // - average_rt_ms: average reaction time in milliseconds

        // Tunable half-life for RT: the RT at which the time factor = 50%.
        // Pick a representative value for your task (e.g., 1000 ms).
        const RT_HALF = 1000; // was 1500; lower to make time more sensitive

        // Time factor grows as RT decreases (bounded 0..1)
        const timeFactor = 1 / (1 + (average_rt / RT_HALF));

        // Accuracy factor (0..1)
        const accFactor = Math.max(0, Math.min(1, percent_correct / 100));

        // Composite score on a 0..100 scale with one decimal for more granularity
        const rawScore = 100 * accFactor * timeFactor;
        const score = Math.round(rawScore * 10) / 10; // keep one decimal place

        let results_bundle = {
            percent_correct: percent_correct,
            average_rt: average_rt,
            average_rt_ms: average_rt,
            score: score,
            score_raw: rawScore, // expose raw for debugging/analytics
            is_high_score: false,
            high_score: null,
        };

        if (typeof window !== 'undefined' && typeof cache !== 'undefined') {
            const hs_key = 'highscore_' + window.cache_key;

            // High score comparison should use full precision to ensure strictly better faster runs win
            const existing = cache.get(hs_key);
            const currentRecord = {
                percent_correct: percent_correct,
                average_rt: average_rt,
                average_rt_ms: average_rt,
                score: score,
                score_raw: rawScore,
            };

            const isBetter =
                !existing ||
                typeof existing.score_raw !== 'number' ||
                currentRecord.score_raw > existing.score_raw;

            if (isBetter) {
                cache.save(hs_key, currentRecord);
                results_bundle.is_high_score = true;
                results_bundle.high_score = currentRecord;
            } else {
                results_bundle.is_high_score = false;
                results_bundle.high_score = existing;
            }
        }
        console.log("Results bundle:", results_bundle);
        return results_bundle;
    }

    function finish() {
        counterSpan.style.display = 'none';
        const stats = calc_stats();
        window.dispatchEvent(new CustomEvent('countdown_completed', {detail: stats}));
    }

    return api;
}());

if (typeof module !== 'undefined') module.exports = feedback_manager;
