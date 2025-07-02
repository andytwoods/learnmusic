function getInstrumentData(instrument, callback) {
    // Fetch JSON from the URL
    fetch('/static/instruments/' + instrument)
        .then((response) => {
            if (!response.ok) {
                throw new Error('Network response was not ok ' + response.statusText);
            }
            return response.json();
        })
        .then((data) => {
            // Extract just the fingerings for backward compatibility
            if (data.fingerings) {
                callback(data.fingerings);
            } else {
                // If the JSON doesn't have the new structure, use it as is
                callback(data);
            }
        })
        .catch((error) => {
            console.error('Error fetching JSON:', error);
        });
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


document.addEventListener("DOMContentLoaded", function () {
    // Initialize the global flag for instrument_manager
    window.isDraggingEnabled = false;


    const elDragToggle_reset = document.getElementById('reset-button');

    const elDragToggleButton = document.getElementById('elDragToggleButton');
    const toggleButtonText = document.getElementById('toggleButtonText');

    // --- Constants ---
    const elPositionsCacheKey = "elPositionsCache";


    function get_draggables() {
        return Array.from(document.querySelectorAll('.draggable'));
    }


    // --- Reset Function ---
    function reset_els() {
        // Reset el positions to their original positions as specified in the HTML
        for (const draggable of get_draggables()) {
            // Remove any transform styles to restore original position
            draggable.style.transform = '';
            // Clear any other positioning styles that might have been added
            draggable.style.top = '';
            draggable.style.right = '';
            draggable.style.bottom = '';
            draggable.style.left = '';
        }


        // Clear cache
        localStorage.removeItem(elPositionsCacheKey);

        console.log("El positions reset to original HTML positions, cache cleared");
    }

    // --- Drag Functionality ---
    let isDragMode = false;
    let draggedEL = null;
    let startX, startY, startTop, startRight;

    // Function to enable/disable drag mode
    function toggleDragMode() {
        isDragMode = !isDragMode;

        // Set global flag for instrument_manager to check
        window.isDraggingEnabled = isDragMode;

        if (isDragMode) {
            // Enable drag mode
            toggleButtonText.textContent = "Save Positions";
            enableElDragging();
        } else {
            // Disable drag mode and save positions
            toggleButtonText.textContent = "Move elements";
            disableELDragging();
            saveElPositionsToCache();
        }
    }

    // Enable dragging on all elements
    function enableElDragging() {
        for (const draggable of get_draggables()) {
            draggable.classList.add("dragging");
            draggable.addEventListener("mousedown", startDrag);
            draggable.addEventListener("touchstart", startDrag, {passive: false});
        }
        document.addEventListener("mousemove", drag);
        document.addEventListener("touchmove", drag, {passive: false});
        document.addEventListener("mouseup", endDrag);
        document.addEventListener("touchend", endDrag);
    }

    // Disable dragging on all elements
    function disableELDragging() {
        for (const draggable of get_draggables()) {
            draggable.classList.remove("dragging");
            draggable.removeEventListener("mousedown", startDrag);
            draggable.removeEventListener("touchstart", startDrag);
        }
        document.removeEventListener("mousemove", drag);
        document.removeEventListener("touchmove", drag);
        document.removeEventListener("mouseup", endDrag);
        document.removeEventListener("touchend", endDrag);
    }

    // Start dragging an element
    function startDrag(e) {
        e.preventDefault();

        // Get the element
        draggedEL = e.currentTarget;

        // Get the starting position
        const touch = e.type === 'touchstart' ? e.touches[0] : e;
        startX = touch.clientX;
        startY = touch.clientY;

        // Get the current position of the element
        const computedStyle = window.getComputedStyle(draggedEL);
        const transform = computedStyle.transform;

        // Extract the translate elements from the transform matrix
        if (transform && transform !== 'none') {
            const matrix = new DOMMatrix(transform);
            startRight = matrix.m41; // translateX value
            startTop = matrix.m42;   // translateY value
        } else {
            startRight = 0;
            startTop = 0;
        }
    }

    // Drag the element
    function drag(e) {
        if (!draggedEL) return;

        e.preventDefault();

        // Get the current position
        const touch = e.type === 'touchmove' ? e.touches[0] : e;
        const deltaX = touch.clientX - startX;
        const deltaY = touch.clientY - startY;

        // Update the element position
        const newRight = startRight + deltaX;
        const newTop = startTop + deltaY;

        // Apply the new position
        draggedEL.style.transform = `translate3d(${newRight}px, ${newTop}px, 0)`;
    }

    // End dragging
    function endDrag() {
        if (draggedEL) {
            // Save element positions to cache when dragging ends
            saveElPositionsToCache();
        }
        draggedEL = null;
    }

    // Save element positions to cache
    function saveElPositionsToCache() {
        const positions = [];

        for (const draggable of get_draggables()) {
            const computedStyle = window.getComputedStyle(draggable);
            const transform = computedStyle.transform;

            let translateX = 0;
            let translateY = 0;

            if (transform && transform !== 'none') {
                const matrix = new DOMMatrix(transform);
                translateX = matrix.m41;
                translateY = matrix.m42;
            }

            positions.push({
                key: draggable.id,
                translateX: translateX,
                translateY: translateY
            });
        }

        localStorage.setItem(elPositionsCacheKey, JSON.stringify(positions));
        console.log("El positions saved to cache:", positions);
    }

    // Load element positions from cache
    function loadelPositionsFromCache() {
        try {
            const cachedPositions = localStorage.getItem(elPositionsCacheKey);

            if (cachedPositions) {
                const positions = JSON.parse(cachedPositions);

                // First, ensure all elements have no transform to start the animation from the initial position
                for (const draggable of get_draggables()) {
                    draggable.style.transform = '';
                }

                // Use setTimeout to ensure the browser has time to render the initial state
                setTimeout(() => {
                    for (let i = 0; i < positions.length; i++) {
                        const position = positions[i];
                        const el = document.getElementById(position['key']);

                        if (el) {
                            el.style.transform = `translate3d(${position.translateX}px, ${position.translateY}px, 0)`;
                        }
                    }

                    console.log("El positions loaded from cache with animation:", positions);
                }, 10); // Small delay to ensure the animation works
            }
        } catch (error) {
            console.error("Error loading el positions from cache:", error);
        }
    }

    // --- Event Listeners ---
    elDragToggleButton.addEventListener('click', toggleDragMode);
    elDragToggle_reset.addEventListener('click', reset_els);

    // Load element positions from cache
    loadelPositionsFromCache();
});

