const countdown_manager = (function () {
    let api = {};

    let remainingTime;

    const counterSpan = document.getElementById("counter-value");
    const card = document.getElementById("time-up");

    api.start = function (durationInSeconds) {
        if (remainingTime !== undefined) return;
        if (durationInSeconds === undefined) durationInSeconds = 30;
        document.getElementById('counter').style.display = 'block';
        remainingTime = durationInSeconds;
        counterSpan.textContent = remainingTime;

        const intervalId = setInterval(() => {
            remainingTime--;
            counterSpan.textContent = remainingTime;

            if (remainingTime <= 0) {
                clearInterval(intervalId);
                if(card) {
                    card.style.display = 'block';
                    counterSpan.style.display = 'none';
                }
            }
        }, 1000);

    }

    return api;
}());

if (typeof module !== 'undefined') module.exports = countdown_manager;
