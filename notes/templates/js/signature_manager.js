const signature_manager = (function () {
    let api = {};
    const count = 6;
    let counter = 0;
    let current_signature;

    // Utility: return a new shuffled copy (Fisher–Yates)
    function shuffled_signatures(arr) {
        const a = arr.slice();
        for (let i = a.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [a[i], a[j]] = [a[j], a[i]];
        }
        return a;
    }

    // Queue sourced from a shuffled list, replenished when empty
    let signatureQueue = [];

    function ensureQueue() {
        if (signatureQueue.length === 0) {
            const source = (window.progress_data && window.progress_data.signatures && window.progress_data.signatures.vexflow) || [];
            signatureQueue = shuffled_signatures(source);
        }
    }

    function nextSignatureFromQueue() {
        ensureQueue();
        return signatureQueue.shift();
    }

    function add_signature(note) {
        counter++;
        if (!current_signature) {
            current_signature = nextSignatureFromQueue();
            counter = 1; // first use of the newly set signature
        }
        if (counter > count) {
            current_signature = nextSignatureFromQueue();
            counter = 1;
        }
        note.signature = current_signature;
        return note;
    }

    api.add_signature = add_signature;

    return api;
}());

// Export for Node.js
if (typeof module !== "undefined") module.exports = signature_manager;
