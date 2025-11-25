# Theremin

Theremin is a MIDI controller for your camera. It uses camera-based hand landmark tracking to translate hand and finger movements and gestures into MIDI messages.

## Demo

TODO!

## How to set up

1. Make sure you have [pyenv](https://github.com/pyenv/pyenv) installed (for python version management) as [MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/guide) only supports Python 3.9 -> 3.12. This repo uses 3.12.10 as defined in the `.python-version` file. Alternatively, just make sure to use a supported version of Python.
2. Run `make install` in the base dir to set up the virtual environment and install pip dependencies.
    - alternatively, create a virtual env by running `python -m venv env` and install the necessary packages by running `env/bin/pip install -r requirements.txt`
3. Run `source env/bin/activate` on POSIX systems (Linux, MacOS) or `venv\Scripts\activate` on Windows to activate the virtual environment.
4. Run `python gui/gui.py` to run the main GUI app.

## How to use

the 'rest' position for Theremin is holding both open palms perpendicular towards the camera. The circle on the tip of each finger indicates if it is active (bent) or not. Green is inactive, red is active.

MIDI messages are sent through MIDI channel 1.

To cycle through available scales or toggle the landmark drawing, click the relevant button on the GUI.

### Right hand

The right hand controls the pitch of the notes and whether or not a note plays. The wrist y position determines the tonic or base note, and the note goes higher up the scale as the fingers are bent.

To start playing the base note, the thumb must be bent towards the centre of the hand. After that, the finger positions relative to the scale degrees played are as follows:

| Index | Middle | Ring  | Pinky | Scale Degree |
| ----- | ------ | ----- | ----- | ------------ |
| False | False  | False | False | 1            |
| True  | False  | False | False | 2            |
| True  | True   | False | False | 3            |
| True  | True   | True  | False | 4            |
| True  | True   | True  | True  | 5            |
| False | True   | True  | True  | 6            |
| False | False  | True  | True  | 7            |
| False | False  | False | True  | 8            |
| True  | False  | False | True  | 9            |
| True  | True   | False | True  | 10           |
| True  | False  | True  | True  | 11           |
| True  | False  | True  | False | 12           |

The thumb must be bent at all times for a note to be played.

### Left hand

The left hand controls the aftertouch volume of the MIDI notes played. The higher the wrist, the more the aftertouch.

Pitch bend is also controlled by bending the thumb and index finger into an OK sign, and then moving the fingers/hand from left to right.

## TODO

-   add GH demo
-   UI
-   allow selections for different finger functions to midi CC messages
-   allow assigning different axes/gestures to different midi control change messages
-   allow choosing a specific camera
-   MIDI keyboard integration as more of an expression controller
-   add more controls for the left fingers (maybe with gestures)
-   make right hand y control octave instead of note (maybe)
-   refactor to use finger enum instead of indices
-   add polyphonic mode where left hand controls a separate pitch
-   perm storage for preferences and customisations
-   debouncing for finger bending
-   host?
