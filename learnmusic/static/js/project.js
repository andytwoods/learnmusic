

function getInstrumentData(instrument, callback) {

// Fetch JSON from the URL
    fetch('/static/instruments/' + instrument + '.json')
        .then((response) => {
            if (!response.ok) {
                throw new Error('Network response was not ok ' + response.statusText);
            }
            response.json().then(callback); // Parse JSON from the response
        })
        .catch((error) => {
            console.error('Error fetching JSON:', error);
        });/* Project specific Javascript goes here. */
}
