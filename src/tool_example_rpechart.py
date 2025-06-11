ne = lambda s, e, st, et: {
    "easingType": 1,
    "start": e,
    "startTime": st,
    "end": s,
    "endTime": et,
}

line = {
    "Group": 0,
    "Name": "Untitled",
    "Texture": "line.png",
    "alphaControl": [
        {"alpha": 1.0,"easing": 1,"x": 0.0},
        {"alpha": 1.0,"easing": 1,"x": 9999999.0}
    ],
    "bpmfactor": 1.0,
    "eventLayers": [
        {
            "alphaEvents": [ne(255, 255, [0, 0, 1], [1, 0, 1])],
            "moveXEvents": [ne(0, 0, [0, 0, 1], [1, 0, 1])],
            "moveYEvents": [ne(0, 0, [0, 0, 1], [1, 0, 1])],
            "rotateEvents": [ne(0, 0, [0, 0, 1], [1, 0, 1])],
            "speedEvents":[]
        }
    ],
    "extended": {
        "inclineEvents": [ne(0.0, 0.0, [0, 0, 1], [1, 0, 1])],
    },
    "father": -1,
    "isCover": 1,
    "notes": [],
    "numOfNotes": 0,
    "posControl": [{"easing": 1, "pos": 1.0, "x": 0.0}, {"easing": 1, "pos": 1.0, "x": 9999999.0}],
    "sizeControl": [{"easing": 1, "size": 1.0, "x": 0.0}, {"easing": 1, "size": 1.0, "x": 9999999.0}],
    "skewControl": [{"easing": 1, "skew": 0.0, "x": 0.0}, {"easing": 1, "skew": 0.0, "x": 9999999.0}],
    "yControl": [{"easing": 1, "x": 0.0, "y": 1.0}, {"easing": 1, "x": 9999999.0, "y": 1.0}],
    "zOrder": 0
}

chart = {
    "BPMList": [
            {
                "bpm": 60,
                "startTime": [0, 0, 1]
            }
    ],
    "META": {
            "RPEVersion": 140,
            "background": "bg.png",
            "charter": "",
            "composer": "",
            "id": "0",
            "level": "",
            "name": "",
            "offset": 0,
            "song": "song.mp3"
    },
    "judgeLineList": [],
    "judgeLineGroup": ["Default"],
}
