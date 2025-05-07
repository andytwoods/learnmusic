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

function fade_in(element, duration) {
    // Apply the fade-in effect
    element.style.opacity = '0'; // Start with opacity 0
    element.style.transition = 'opacity 0.3s ease-in'; // Transition for 0.3 seconds
    element.style.display = 'block'; // Ensure it's displayed if it was hidden

    if (!duration) duration = 200;
// Trigger the fade-in after appending
    setTimeout(() => {
        element.style.opacity = '1'; // Set opacity to 1 for fade-in effect
    }, duration);
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

    if (noteString.indexOf('/') === -1) return enharmonics[noteString]

    // Parse the note and octave from VexFlow note string
    const regex = /^([A-Ga-g][#b]*)(\/\d)$/; // Matches notes like "A#/4", "Bb/4", etc.
    const match = noteString.match(regex);
    if (!match) {
        throw new Error("Invalid note format: " + noteString);
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
    if (e.target.hasAttribute('hx-no-confirm') || e.detail.target.hasAttribute('hx-no-confirm')) return

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
