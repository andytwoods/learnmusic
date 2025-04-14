def create_unique_notes_list():
    # Data structure for each grade:
    #   grade_number -> { "scale name": [list_of_notes_as_strings] }
    # Notes here are the written pitches for Bb Trumpet (e.g. "C4", "F#4", "Bb3", etc.)
    scales_by_grade = {
        1: {
            "C major": ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"],
            "G major": ["G3", "A3", "B3", "C4", "D4", "E4", "F#4", "G4"],
            "D major": ["D4", "E4", "F#4", "G4", "A4", "B4", "C#5", "D5"],
        },
        2: {
            "C major": ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"],
            "G major": ["G3", "A3", "B3", "C4", "D4", "E4", "F#4", "G4"],
            "D major": ["D4", "E4", "F#4", "G4", "A4", "B4", "C#5", "D5"],
            "A minor (harmonic)": ["A3", "B3", "C4", "D4", "E4", "F4", "G#4", "A4"],
            "A minor (melodic)": ["A3", "B3", "C4", "D4", "E4", "F#4", "G#4", "A4",
                                  # Descending version often used too,
                                  # but we’ll stick to the ascending form here.
                                 ],
        },
        3: {
            "C major": ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"],
            "G major": ["G3", "A3", "B3", "C4", "D4", "E4", "F#4", "G4"],
            "D major": ["D4", "E4", "F#4", "G4", "A4", "B4", "C#5", "D5"],
            "F major": ["F3", "G3", "A3", "Bb3", "C4", "D4", "E4", "F4"],
            "A minor (harmonic)": ["A3", "B3", "C4", "D4", "E4", "F4", "G#4", "A4"],
            "A minor (melodic)": ["A3", "B3", "C4", "D4", "E4", "F#4", "G#4", "A4"],
            "E minor (harmonic)": ["E4", "F#4", "G4", "A4", "B4", "C5", "D#5", "E5"],
            "E minor (melodic)": ["E4", "F#4", "G4", "A4", "B4", "C#5", "D#5", "E5"],
        },
        4: {
            "C major (2 octaves)":  ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5",
                                     "D5", "E5", "F5", "G5", "A5", "B5", "C6"],
            "G major (2 octaves)":  ["G3", "A3", "B3", "C4", "D4", "E4", "F#4", "G4",
                                     "A4", "B4", "C5", "D5", "E5", "F#5", "G5"],
            "D major (2 octaves)":  ["D4", "E4", "F#4", "G4", "A4", "B4", "C#5", "D5",
                                     "E5", "F#5", "G5", "A5", "B5", "C#6", "D6"],
            "F major (2 octaves)":  ["F3", "G3", "A3", "Bb3", "C4", "D4", "E4", "F4",
                                     "G4", "A4", "Bb4", "C5", "D5", "E5", "F5"],
            "Bb major (2 octaves)": ["Bb3", "C4", "D4", "Eb4", "F4", "G4", "A4", "Bb4",
                                     "C5", "D5", "Eb5", "F5", "G5", "A5", "Bb5"],
            "A minor (harmonic) 2v": ["A3", "B3", "C4", "D4", "E4", "F4", "G#4", "A4",
                                      "B4", "C5", "D5", "E5", "F5", "G#5", "A5"],
            "A minor (melodic) 2v":  ["A3", "B3", "C4", "D4", "E4", "F#4", "G#4", "A4",
                                      "B4", "C5", "D5", "E5", "F#5", "G#5", "A5"],
            "E minor (harmonic) 2v": ["E4", "F#4", "G4", "A4", "B4", "C5", "D#5", "E5",
                                      "F#5", "G5", "A5", "B5", "C6", "D#6", "E6"],
            "E minor (melodic) 2v":  ["E4", "F#4", "G4", "A4", "B4", "C#5", "D#5", "E5",
                                      "F#5", "G5", "A5", "B5", "C#6", "D#6", "E6"],
            "D minor (harmonic) 2v": ["D4", "E4", "F4", "G4", "A4", "Bb4", "C#5", "D5",
                                      "E5", "F5", "G5", "A5", "Bb5", "C#6", "D6"],
            "D minor (melodic) 2v":  ["D4", "E4", "F4", "G4", "A4", "B4", "C#5", "D5",
                                      "E5", "F5", "G5", "A5", "B5", "C#6", "D6"],
        },
        5: {
            "Ab major (1 octave)":  ["Ab3", "Bb3", "C4", "Db4", "Eb4", "F4", "G4", "Ab4"],
            "G minor (harmonic)":   ["G3", "A3", "Bb3", "C4", "D4", "Eb4", "F#4", "G4"],
            "G minor (melodic)":    ["G3", "A3", "Bb3", "C4", "D4", "E4", "F#4", "G4"],
        }
    }

    # Helper to convert e.g. "Bb3" -> "B -1 3", "F#4" -> "F +1 4", "C4" -> "C 0 4"
    def convert_note_format(note_str):
        """
        Takes a note like 'Bb3', 'F#4', 'C4', etc. and returns
        something like 'B -1 3', 'F +1 4', 'C 0 4'.
        """
        # Split into note name (with possible accidental) and octave
        # Examples: "Bb3" -> note_part="Bb", octave="3"
        #           "F#4" -> note_part="F#", octave="4"
        #           "C4"  -> note_part="C",  octave="4"
        # We'll assume the last character(s) are always the octave number.
        # That means we look from the right to find the first digit.
        octave = ""
        i = len(note_str) - 1
        # Collect all trailing digits (in case of something like 'C10', but that’s unlikely on trumpet)
        while i >= 0 and note_str[i].isdigit():
            octave = note_str[i] + octave
            i -= 1
        note_part = note_str[:i+1]  # everything up to that digit

        # Check if note_part has an accidental
        # e.g. "Bb" -> letter="B", accidental=-1
        #      "F#" -> letter="F", accidental=+1
        #      "C"  -> letter="C", accidental=0
        letter = note_part[0]  # e.g. 'B' or 'F' or 'C'
        accidental_value = 0   # default: no accidental
        if len(note_part) > 1:
            # There's some accidental
            if note_part[1] in ('b', '♭'):
                accidental_value = -1
            elif note_part[1] in ('#', '♯'):
                accidental_value = +1

        # Build the final string (letter, accidental, octave).
        # We'll do:
        #   "C 0 4" or "B -1 3" or "F +1 4"
        return f"{letter} {accidental_value} {octave}"

    unique_notes = []  # will store the converted note strings in encounter order

    # Main iteration
    for grade in range(1, 6):  # 1 through 5
        # Get the dictionary of scales for this grade
        scales = scales_by_grade.get(grade, {})
        for scale_name, notes in scales.items():
            for note in notes:
                converted = convert_note_format(note)
                if converted not in unique_notes:
                    unique_notes.append(converted)

    return unique_notes


results = ';'.join(create_unique_notes_list())
print(results)

