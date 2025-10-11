const signature_manager = (function () {
    let api = {};

    function getRandomSignature(array) {
        if (array.length === 0) return 'C';
        return array[Math.floor(Math.random() * array.length)];
    }

    function add_signature(note) {
        note['signature'] = getRandomSignature(window.progress_data.signatures.vexflow);
        return note;
    }

    api.add_signature = add_signature;

    return api;
}());
