import rtmidi
from hand import Hand
from typing import List
from rtmidi.midiconstants import (
    NOTE_ON,
    NOTE_OFF,
    CHANNEL_AFTERTOUCH,
    CONTROL_CHANGE,
    PITCH_BEND,
    ALL_NOTES_OFF,
)

PITCH_BEND_RANGE = 8192
FINGERS_TO_SCALE_DEGREE = {
    # (index, middle, ring, pinky): scale_degree
    (False, False, False, False): 1,
    (True, False, False, False): 2,
    (True, True, False, False): 3,
    (True, True, True, False): 4,
    (True, True, True, True): 5,
    (False, True, True, True): 6,
    (False, False, True, True): 7,
    (False, False, False, True): 8,
    (True, False, False, True): 9,
    (True, True, False, True): 10,
    (True, False, True, True): 11,
    (True, False, True, False): 12,
}


class MidiController:
    def __init__(self):
        self.midiout = rtmidi.MidiOut()
        available_ports = self.midiout.get_ports()

        if available_ports:
            self.midiout.open_port(0)
        else:
            print("opening virtual port")
            self.midiout.open_virtual_port("My virtual output")

    def send_midi(
        self,
        status: int,
        channel: int,
        first_byte: int,
        second_byte: int,
    ):
        status_byte = status | (channel - 1)
        self.midiout.send_message([status_byte, first_byte, second_byte])

    def play_note(
        self,
        corrected_note: int,
        previous_corrected_note: int,
        clamped_volume: float,
        previous_clamped_volume: int,
    ):
        normalised_volume = (1 - clamped_volume) * 127

        if previous_corrected_note != corrected_note:
            self.send_midi(NOTE_ON, 1, corrected_note, normalised_volume)
            self.send_midi(NOTE_OFF, 1, previous_corrected_note, 0)

        if previous_clamped_volume != normalised_volume:
            self.send_midi(CHANNEL_AFTERTOUCH, 1, normalised_volume, 0)

    def get_corrected_note(
        self, clamped_pitch: float, right_hand: Hand, scale: List[int]
    ) -> int:
        base_note = round(1 - clamped_pitch, 1) * 10 + 60

        fingers = right_hand.fingers
        pattern = (
            fingers[1].is_finger_bent(),
            fingers[2].is_finger_bent(),
            fingers[3].is_finger_bent(),
            fingers[4].is_finger_bent(),
        )

        scale_degree = FINGERS_TO_SCALE_DEGREE.get(pattern, 1)

        octave = (scale_degree - 1) // len(scale)
        degree_index = (scale_degree - 1) % len(scale)

        return int(base_note + scale[degree_index] + octave * 12)

    def calculate_and_send_pitch_bend(
        self,
        left_wrist_x: float,
        previous_left_wrist_x: float,
        current_time: float,
        previous_time: float,
    ):
        if previous_left_wrist_x is not None and previous_time is not None:
            delta_x = left_wrist_x - previous_left_wrist_x
            delta_time = current_time - previous_time

            pitch_bend_amount = int(PITCH_BEND_RANGE + ((delta_x) / delta_time) * 4096)
            pitch_bend_amount = max(0, min(16383, pitch_bend_amount))

            self.send_midi(
                PITCH_BEND,
                1,
                pitch_bend_amount & 0x7F,
                (pitch_bend_amount >> 7) & 0x7F,
            )

    def stop_midi(self):
        self.send_midi(CONTROL_CHANGE, 1, ALL_NOTES_OFF, 0)
