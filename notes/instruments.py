instruments = {"Trumpet": {
    "Beginner": {
        "lowest_note": None,
        "highest_note": None,
        "clef": "TREBLE",
        "notes": "C 0 4;D 0 4;E 0 4;F 0 4;G 0 4;A 0 4;B -1 4;B 0 4"
    },
    "Intermediate": {
        "lowest_note": "F 1 3",
        "highest_note": "C 0 5",
        "clef": "TREBLE",
        "notes": None
    },
    "Advanced": {
        "lowest_note": "F 1 3",
        "highest_note": "C 0 6",
        "clef": "TREBLE",
        "notes": None
    }
},
    "Trombone": {
        "Beginner": {
            "lowest_note": None,
            "highest_note": None,
            "clef": "TREBLE",
            "notes": "E 0 4;F 0 4;F 1 4;G 0 4;A -1 4;A 0 4;B -1 4;B 0 4;C 0 4"
        },
        "Intermediate": {
            "lowest_note": "F 1 3",
            "highest_note": "Bb 0 5",
            "clef": "TREBLE",
            "notes": None
        },
        "Advanced": {
            "lowest_note": "F 1 3",
            "highest_note": "D 0 6",
            "clef": "TREBLE",
            "notes": None
        }
    }
}

instrument_infos = {
    'trumpet': {
        'answer_template': 'trumpet.html',
        'answers': 'trumpet.json',
        'clef': ['TREBLE', ],
        'common_keys': ['Bb', 'C', ],
        'transposing_direction': [-1,],
        'notes': [
            "F 0 3", "G 0 3", "A -1 3", "A 0 3", "B -1 3", "B 0 3",
            "C 0 4", "D -1 4", "D 0 4", "E -1 4", "E 0 4", "F 0 4", "G 0 4",
            "A -1 4", "A 0 4", "B -1 4", "B 0 4",
            "C 0 5", "D -1 5", "D 0 5", "E -1 5", "E 0 5", "F 0 5", "G 0 5",
            "A -1 5", "A 0 5", "B -1 5", "B 0 5",
            "C 0 6", "D -1 6", "D 0 6"
        ],
    },
    'trombone': {
        'answer_template': 'trombone.html',
        'answers': 'trombone.json',
        'clef': ['TREBLE', 'BASS', ],
        'common_keys': ['C', ],
        'transposing_direction': [-1, 0],
        'notes': [
            "B -1 2", "C 0 3", "D 0 3", "E -1 3", "F 0 3", "G 0 3",
            "A -1 3", "A 0 3", "B -1 3", "B 0 3", "C 0 4", "D -1 4", "D 0 4",
            "E -1 4", "E 0 4", "F 0 4", "G 0 4", "A -1 4", "A 0 4", "B -1 4",
            "B 0 4", "C 0 5", "D -1 5", "D 0 5", "E -1 5", "E 0 5", "F 0 5",
            "G 0 5", "A -1 5", "A 0 5", "B -1 5", "B 0 5", "C 0 6", "D -1 6",
            "D 0 6"
        ],

    },
}
