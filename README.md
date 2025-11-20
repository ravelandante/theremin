# Theremin

## How to set up

1. Make sure you have [pyenv](https://github.com/pyenv/pyenv) installed (for python version management) as [MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/guide) only supports Python 3.9 -> 3.12. This repo uses 3.12.10 as defined in the `.python-version` file. Alternatively, just make sure to use a supported version of Python.
2. Run `make install` in the base dir to set up the virtual environment and install pip dependencies.
    - alternatively, create a virtual env by running `python -m venv env` and install the necessary packages by running `env/bin/pip install -r requirements.txt`
3. Run `source env/bin/activate` on POSIX systems (Linux, MacOS) or `venv\Scripts\activate` on Windows to activate the virtual environment.
4. Run `python gui/gui.py` to run the main GUI app.

## TODO

-   UI
-   allow selections for different finger functions to midi CC messages
-   allow assigning different axes/gestures to different midi control change messages
-   allow choosing a specific camera
-   MIDI keyboard integration as more of an expression controller
-   add more controls for the left fingers (maybe with gestures)
-   make ok gesture recognition more robust (use finger distances)
-   make right hand y control octave instead of note (maybe)
-   refactor to use finger enum instead of indices
-   add polyphonic mode where left hand controls a separate pitch
-   add GH demo
-   host?
