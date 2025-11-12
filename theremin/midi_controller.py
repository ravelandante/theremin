import rtmidi
from hand import Hand
from typing import List

NOTE_ON = 0x90
NOTE_OFF = 0x80
AFTERTOUCH = 0xD0
ALL_OFF = 0xB0
PITCH_BEND = 0xE0


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
            self.send_midi(AFTERTOUCH, 1, normalised_volume, 0)

    def get_corrected_note(
        self, clamped_pitch: float, right_hand: Hand, scale: List[int]
    ) -> int:
        base_note = round(1 - clamped_pitch, 1) * 10 + 60
        scale_degree = 1
        fingers = right_hand.fingers
        finger_bent = {
            "index": fingers[1].is_finger_bent(),
            "middle": fingers[2].is_finger_bent(),
            "ring": fingers[3].is_finger_bent(),
            "pinky": fingers[4].is_finger_bent(),
        }

        if finger_bent["index"]:
            if finger_bent["pinky"] and finger_bent["ring"] and finger_bent["middle"]:
                scale_degree = 5
            elif finger_bent["ring"] and finger_bent["middle"]:
                scale_degree = 4
            elif finger_bent["middle"]:
                scale_degree = 3
            else:
                scale_degree = 2
        else:
            if finger_bent["pinky"]:
                if finger_bent["ring"] and finger_bent["middle"]:
                    scale_degree = 6
                elif finger_bent["ring"]:
                    scale_degree = 7
                else:
                    scale_degree = 8

        return int(base_note + scale[scale_degree - 1])

    def calculate_and_send_pitch_bend(
        self,
        left_wrist_x: float,
        previous_left_wrist_x: float,
        current_time: float,
        previous_time: float,
        pitch_bend_range: int,
    ):
        if previous_left_wrist_x is not None and previous_time is not None:
            delta_x = left_wrist_x - previous_left_wrist_x
            delta_time = current_time - previous_time

            pitch_bend_amount = int(pitch_bend_range + ((delta_x) / delta_time) * 4096)
            pitch_bend_amount = max(0, min(16383, pitch_bend_amount))

            self.send_midi(
                PITCH_BEND,
                1,
                pitch_bend_amount & 0x7F,
                (pitch_bend_amount >> 7) & 0x7F,
            )

    def stop_midi(self):
        self.send_midi(ALL_OFF, 1, 123, 0)
