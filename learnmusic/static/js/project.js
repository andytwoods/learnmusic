function getInstrumentData(instrument, callback) {

// Fetch JSON from the URL
    fetch('/static/instruments/' + instrument)
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

function getEnharmonicEquivalents(noteString) {
    // Enharmonic mappings
    const enharmonics = {
        "C": ["B#", "Dbb"],
        "C#": ["Db"],
        "Db": ["C#", "B##"],
        "D": ["C##", "Ebb"],
        "D#": ["Eb"],
        "Eb": ["D#", "Fbb"],
        "E": ["Fb", "D##"],
        "E#": ["F"],
        "F": ["E#", "Gbb"],
        "F#": ["Gb"],
        "Gb": ["F#", "E##"],
        "G": ["F##", "Abb"],
        "G#": ["Ab"],
        "Ab": ["G#", "Bbbb"],
        "A": ["G##", "Bbb"],
        "A#": ["Bb"],
        "Bb": ["A#", "Cbb"],
        "B": ["Cb", "A##"],
        "B#": ["C"]
    };

    // Parse the note and octave from VexFlow note string
    const regex = /^([A-Ga-g][#b]*)(\/\d)$/; // Matches notes like "A#/4", "Bb/4", etc.
    const match = noteString.match(regex);
    if (!match) {
        throw new Error("Invalid note format");
    }

    const pitch = match[1]; // Note part (e.g., Bb, C#, etc.)
    const octave = match[2]; // Octave part (e.g., /4)

    // Get the enharmonic equivalents for the pitch
    const alternates = enharmonics[pitch] || [];

    // Generate the enharmonic notes with the same octave
    const result = alternates.map(enharmonic => `${enharmonic}${octave}`);

    return result;
}

function throttle(callback, limit) {
    var waiting = false;                      // Initially, we're not waiting
    return function () {                      // We return a throttled function
        if (!waiting) {                       // If we're not waiting
            callback.apply(this, arguments);  // Execute users function
            waiting = true;                   // Prevent future invocations
            setTimeout(function () {          // After a period of time
                waiting = false;              // And allow future invocations
            }, limit);
        }
    }
}


document.addEventListener("htmx:confirm", function (e) {

    // below breaks htmx sometimes
    //if (!e.detail.target.hasAttribute('hx-confirm')) return

    e.preventDefault()

    Swal.fire({
        title: "Proceed?",
        text: `${e.detail.question}`
    }).then(function (result) {
        if (result.isConfirmed) {
            e.detail.issueRequest(true);
        }
    })
})
