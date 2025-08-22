instruments = {"Trumpet": {
    "Beginner": {
        # https://chatgpt.com/share/67f819f1-948c-8003-a8d8-39f9443f5d58
        "notes": "C 0 4;D 0 4;E 0 4;F 0 4;G 0 4;A 0 4;B -1 4;B 0 4;C 0 5;A 0 3;B 0 3;F 1 4;D 0 5;E 0 5;F 0 5"
    },
    "Intermediate": {
        "lowest_note": "F 1 3",
        "highest_note": "C 0 5",
    },
    "Advanced": {
        "lowest_note": "F 1 3",
        "highest_note": "C 0 6",
    }
},
    "Trombone": {
        "Beginner": {
            "notes": "B -1 2;C 0 3;D 0 3;E -1 3;F 0 3;G 0 3;A -1 3;A 0 3;B -1 3;B 0 3;C 0 4;D -1 4;D 0 4;E -1 4;E 0 4;F 0 4;G 0 4;A -1 4;A 0 4;B -1 4;B 0 4;C 0 5;D -1 5;D 0 5;E -1 5;E 0 5;F 0 5;G 0 5;A -1 5;A 0 5;B -1 5;B 0 5;C 0 6;D -1 6;D 0 6"
        },
        "Intermediate": {
            "lowest_note": "F 1 3",
            "highest_note": "B -1 5",
        },
        "Advanced": {
            "lowest_note": "F 1 3",
            "highest_note": "D 0 6",
        }
    },
    "Soprano-Trombone": {
        "Beginner": {
            "notes": "B -1 2;C 0 3;D 0 3;E -1 3;F 0 3;G 0 3;A -1 3;A 0 3;B -1 3;B 0 3;C 0 4;D -1 4;D 0 4;E -1 4;E 0 4;F 0 4;G 0 4;A -1 4;A 0 4;B -1 4;B 0 4;C 0 5;D -1 5;D 0 5;E -1 5;E 0 5;F 0 5;G 0 5;A -1 5;A 0 5;B -1 5;B 0 5;C 0 6;D -1 6;D 0 6"
        },
        "Intermediate": {
            "lowest_note": "F 1 3",
            "highest_note": "B -1 5",
        },
        "Advanced": {
            "lowest_note": "F 1 3",
            "highest_note": "D 0 6",
        }
    },
}

instrument_infos = {
    'Trumpet': {
        'answer_template': 'trumpet.html',
        'answers': 'trumpet.json',
        'clef': ['TREBLE', ],
        'common_keys': ['Bb', 'C', ],
    },
    'Trombone': {
        'answer_template': 'trombone.html',
        'answers': 'trombone.json',
        'clef': ['TREBLE', 'BASS', ],
        'common_keys': ['C', 'Bb'],
    },
    'Soprano-Trombone': {
        'answer_template': 'trombone.html',
        'answers': 'soprano-trombone.json',
        'clef': ['TREBLE', ],
        'common_keys': ['Bb', 'C', ],
    },
}
