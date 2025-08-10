const countdown_manager = (function () {
    let api = {};

    let remainingTime;

    const counterSpan = document.getElementById("counter-value");


    api.start = function (durationInSeconds) {
        if (remainingTime !== undefined) return;
        if (durationInSeconds === undefined) durationInSeconds = 60;
        document.getElementById('counter').style.display = 'block';
        remainingTime = durationInSeconds;
        counterSpan.textContent = remainingTime;

        const intervalId = setInterval(() => {
            remainingTime--;
            counterSpan.textContent = remainingTime;

            if (remainingTime <= 0) {

                clearInterval(intervalId);

                counterSpan.style.display = 'none';

                window.dispatchEvent(new Event('countdown_completed'));

            }
        }, 1000);

    }

    return api;
}());

if (typeof module !== 'undefined') module.exports = countdown_manager;
