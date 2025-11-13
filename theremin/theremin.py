import cv2
import mediapipe as mp
import time
import numpy as np
from midi_controller import MidiController
from vision import Vision
from hand import Hand
from collections import namedtuple

VOLUME_RATIO_BOUNDS = (0.14, 0.07)

Scale = namedtuple("Scale", ["name", "notes"])

POSSIBLE_SCALES = [
    Scale("Major", [0, 2, 4, 5, 7, 9, 11]),
    Scale("Chromatic", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
    Scale("Natural minor", [0, 2, 3, 5, 7, 8, 10]),
    Scale("Harmonic minor", [0, 2, 3, 5, 7, 8, 11]),
    Scale("Pentatonic", [0, 2, 4, 7, 9]),
    Scale("Major blues", [0, 2, 3, 4, 7, 9]),
    Scale("Minor blues", [0, 3, 5, 6, 7, 10]),
]


class Theremin:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.controller = MidiController()
        self.vision = Vision(VOLUME_RATIO_BOUNDS[0], VOLUME_RATIO_BOUNDS[1])
        self.scale = POSSIBLE_SCALES[0]

        self.previous_corrected_note = 0
        self.previous_clamped_volume = 0
        self.draw_landmarks_enabled = True

        self.previous_left_thumb_x = None
        self.previous_time = None

    def cycle_scale(self):
        current_scale_index = next(
            (
                i
                for i, (scale_name, _) in enumerate(POSSIBLE_SCALES)
                if scale_name == self.scale.name
            ),
            0,
        )
        next_scale_index = (current_scale_index + 1) % len(POSSIBLE_SCALES)
        self.scale = POSSIBLE_SCALES[next_scale_index]

    def perform(self, right_hand: Hand, left_hand: Hand, final_frame: np.ndarray):
        volume_min = VOLUME_RATIO_BOUNDS[0]
        volume_max = 1.0 - VOLUME_RATIO_BOUNDS[1]

        clamped_volume = max(
            0.0, min(1.0, (left_hand.wrist.y - volume_min) / (volume_max - volume_min))
        )
        clamped_pitch = max(0.0, min(1.0, right_hand.wrist.y))

        current_time = time.time()
        self.controller.calculate_and_send_pitch_bend(
            (left_hand.fingers[0].tip_x if left_hand.is_ok_hand() else 0),
            (self.previous_left_thumb_x if left_hand.is_ok_hand() else 0),
            current_time,
            self.previous_time,
        )

        self.previous_left_thumb_x = left_hand.fingers[0].tip_x
        self.previous_time = current_time

        if right_hand.fingers[0].is_finger_bent():
            corrected_note = self.controller.get_corrected_note(
                clamped_pitch, right_hand, self.scale.notes
            )
            self.controller.play_note(
                corrected_note,
                self.previous_corrected_note,
                clamped_volume,
                self.previous_clamped_volume,
            )

            self.previous_corrected_note = corrected_note
            self.previous_clamped_volume = clamped_volume
            self.vision.draw_note_name(corrected_note, final_frame)
            self.vision.draw_scale_name(self.scale.name, final_frame)
        else:
            self.controller.stop_midi()
            self.previous_corrected_note = 0
        self.vision.draw_volume(1 - clamped_volume, final_frame, left_hand.wrist.x)

    def main_loop(self):
        try:
            cap = cv2.VideoCapture(0)
            with self.mp_hands.Hands(
                model_complexity=0,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
                max_num_hands=2,
            ) as hand_detector:

                while cap.isOpened():
                    success, frame = cap.read()
                    if not success:
                        print("unable to get webcam feed")
                        continue

                    final_frame = self.vision.get_video(
                        hand_detector, frame, self.draw_landmarks_enabled
                    )

                    if right_hand := next(
                        (
                            hand
                            for hand in self.vision.hands
                            if hand.handedness == "Right"
                        ),
                        None,
                    ):
                        if left_hand := next(
                            (
                                hand
                                for hand in self.vision.hands
                                if hand.handedness == "Left"
                            ),
                            None,
                        ):
                            self.perform(right_hand, left_hand, final_frame)

                    cv2.imshow("Theremin", final_frame)

                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        break
                    elif key == ord("d"):
                        self.draw_landmarks_enabled = not self.draw_landmarks_enabled
                    elif key == ord("s"):
                        self.cycle_scale()

        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.controller.stop_midi()
            self.controller.midiout.close_port()


if __name__ == "__main__":
    theremin = Theremin()
    theremin.main_loop()
