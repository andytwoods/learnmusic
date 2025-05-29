const countdown_manager = (function () {
    let api = {};

    let remainingTime;

    const counterSpan = document.getElementById("counter-value");

    api.start = function (durationInSeconds) {
        if (remainingTime !== undefined) return;
        if (durationInSeconds === undefined) durationInSeconds = 120;
        document.getElementById('counter').style.display = 'block';
        remainingTime = durationInSeconds;
        counterSpan.textContent = remainingTime;

        const intervalId = setInterval(() => {
            remainingTime--;
            counterSpan.textContent = remainingTime;

            if (remainingTime <= 0) {
                clearInterval(intervalId);
                counterSpan.textContent = "Time's up! Continue if you want :)";
            }
        }, 1000);

    }

    return api;
}());
