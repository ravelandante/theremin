import cv2
import mediapipe as mp
import time
import numpy as np
from midi_controller import MidiController
from vision import Vision
from hand import Hand


class Theremin:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.controller = MidiController()
        self.vision = Vision()
        self.PITCH_BEND_RANGE = 8192

        self.previous_corrected_note = 0
        self.previous_clamped_volume = 0
        self.draw_landmarks_enabled = True

        self.previous_left_thumb_x = None
        self.previous_time = None

    def perform(self, right_hand: Hand, left_hand: Hand, final_frame: np.ndarray):
        clamped_pitch = max(0.0, min(1.0, right_hand.wrist.y))
        clamped_volume = max(0.0, min(1.0, left_hand.wrist.y))

        current_time = time.time()
        self.controller.calculate_and_send_pitch_bend(
            (left_hand.finger_tips[0].x if left_hand.is_ok_hand() else 0),
            (self.previous_left_thumb_x if left_hand.is_ok_hand() else 0),
            current_time,
            self.previous_time,
            self.PITCH_BEND_RANGE,
        )

        self.previous_left_thumb_x = left_hand.finger_tips[0].x
        self.previous_time = current_time

        if right_hand.finger_tips[0].is_finger_bent():
            corrected_note = self.controller.get_corrected_note(
                clamped_pitch,
                right_hand,
            )
            self.controller.send_midi(
                corrected_note,
                self.previous_corrected_note,
                clamped_volume,
                self.previous_clamped_volume,
            )

            self.previous_corrected_note = corrected_note
            self.previous_clamped_volume = clamped_volume
            self.vision.draw_note_name(corrected_note, final_frame)
        else:
            self.controller.stop_midi()
            self.previous_corrected_note = 0
        self.vision.draw_volume(1 - clamped_volume, final_frame)

    def main_loop(self):
        try:
            cap = cv2.VideoCapture(0)
            with self.mp_hands.Hands(
                model_complexity=0,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
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

                    cv2.imshow("image", final_frame)

                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        break
                    elif key == ord("d"):
                        self.draw_landmarks_enabled = not self.draw_landmarks_enabled
        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.controller.stop_midi()
            self.controller.midiout.close_port()


theremin = Theremin()
theremin.main_loop()
