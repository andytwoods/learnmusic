# JavaScript Tests for Learning Manager

This directory contains tests for the `learning_manager.js` file. There are two ways to test the JavaScript code:

## 1. Manual Testing in the Browser

A dedicated test page has been set up to test the learning_manager.js file in the browser environment.

### How to Access the Test Page

1. Start the Django development server:
   ```
   python manage.py runserver
   ```

2. Navigate to the test page in your browser:
   ```
   http://localhost:8000/notes/test-js/
   ```

3. The test page will display the results of various tests for the learning_manager.js functions.

## 2. Automated Testing with Jest

Jest tests have been set up to thoroughly test all functions in the learning_manager.js file.

### Prerequisites

- Node.js and npm must be installed on your system.

### How to Run the Tests

1. Install the required dependencies:
   ```
   npm install
   ```

2. Run the tests:
   ```
   npm test
   ```

### Test Coverage

The Jest tests cover the following functions:

- `getMasteryScore`: Tests the calculation of mastery scores based on recent attempts.
- `isMastered`: Tests the determination of whether a note is mastered.
- `allNotesMastered`: Tests the check for whether all notes in a set are mastered.
- `orderNotesByMastery`: Tests the sorting of notes by mastery score.
- `areNotesEqual`: Tests the comparison of notes for equality.
- `pickNewNotes`: Tests the selection of new notes not already in progress_data.
- `lightlyShuffleNotes`: Tests the light shuffling of notes.
- `processNotes`: Tests the processing of notes to find the next note to display.
- `next_note`: Tests the main function that determines the next note to display.
- `set_LIKELIHOOD_OF_MASTERED_NOTE`: Tests the setting of the likelihood parameter.

### Test Structure

The tests are organized into describe blocks for each function, with multiple test cases for each function to cover different scenarios and edge cases.

## Test Files

- `learning_manager.test.js`: Jest tests for learning_manager.js.

## Adding More Tests

To add more tests:

1. Add new test cases to `learning_manager.test.js`.
2. Run the tests to ensure they pass.
