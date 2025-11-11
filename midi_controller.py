import rtmidi
from hand import Hand

NOTE_ON_CH1 = 0x90
NOTE_OFF_CH1 = 0x80
AFTERTOUCH_CH1 = 0xD0
ALL_OFF_CH1 = 0xB0
PITCH_BEND_CH1 = 0xE0

MAJOR_SCALE_INTERVALS = [0, 2, 4, 5, 7, 9, 11, 12]
NATURAL_MINOR_SCALE_INTERVALS = [0, 2, 3, 5, 7, 8, 10, 12]
HARMONIC_MINOR_SCALE_INTERVALS = [0, 2, 3, 5, 7, 8, 11, 12]


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
        corrected_note: int,
        previous_corrected_note: int,
        clamped_volume: float,
        previous_clamped_volume: int,
    ):
        normalised_volume = (1 - clamped_volume) * 127

        if previous_corrected_note != corrected_note:
            self.midiout.send_message([NOTE_ON_CH1, corrected_note, normalised_volume])
            self.midiout.send_message([NOTE_OFF_CH1, previous_corrected_note, 0])

        if previous_clamped_volume != normalised_volume:
            self.midiout.send_message([AFTERTOUCH_CH1, normalised_volume])

    def get_corrected_note(
        self,
        clamped_pitch: float,
        right_hand: Hand,
    ) -> int:
        base_note = round(1 - clamped_pitch, 1) * 10 + 60
        scale_degree = 1
        finger_tips = right_hand.finger_tips
        finger_bent = {
            "index": finger_tips[1].is_finger_bent(),
            "middle": finger_tips[2].is_finger_bent(),
            "ring": finger_tips[3].is_finger_bent(),
            "pinky": finger_tips[4].is_finger_bent(),
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

        return int(base_note + MAJOR_SCALE_INTERVALS[scale_degree - 1])

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

            self.midiout.send_message(
                [
                    PITCH_BEND_CH1,
                    pitch_bend_amount & 0x7F,
                    (pitch_bend_amount >> 7) & 0x7F,
                ]
            )

    def stop_midi(self):
        self.midiout.send_message([ALL_OFF_CH1, 123, 0])
