instruments = {"Trumpet": {
    "Beginner": {
        "lowest_note": None,
        "highest_note": None,
        "clef": "TREBLE",
        "notes": "C 0 4;D 0 4;E 0 4;F 0 4;G 0 4;A 0 4;Bb -1 4;B 0 4"
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
            "notes": "E 0 4;F 0 4;F# 0 4;G 0 4;Ab 0 4;A 0 4;Bb -1 4;B 0 4;C 0 4"
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
        'clef': ['TREBLE',]
    },
    'trombone': {
        'answer_template': 'trombone.html',
        'answers': 'trombone.json',
        'clef': ['TREBLE', 'BASS',]
    },
}

