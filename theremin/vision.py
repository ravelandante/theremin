import cv2
import mediapipe as mp
import numpy as np
from typing import List

from hand import Hand


class Vision:
    def __init__(self, volume_ratio_max: int, volume_ratio_min: int):
        self.NOTE_NAMES = [
            "C",
            "C#",
            "D",
            "D#",
            "E",
            "F",
            "F#",
            "G",
            "G#",
            "A",
            "A#",
            "B",
        ]
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.volume_ratio_max = volume_ratio_max
        self.volume_ratio_min = volume_ratio_min

        self.hands: List[Hand] = []

    def get_hand_landmarks(
        self,
        multi_hand_world_landmarks: list,
        multi_hand_landmarks: list,
        multi_handedness: list,
    ) -> List[Hand]:
        hands: List[Hand] = []

        for i, hand_landmarks in enumerate(multi_hand_world_landmarks):
            hand_label = multi_handedness[i].classification[0].label
            hand_world_landmark = hand_landmarks.landmark
            hand_landmark = multi_hand_landmarks[i].landmark
            hands.append(Hand(hand_label, hand_world_landmark, hand_landmark))

        return hands

    def draw_landmarks(
        self,
        frame: np.ndarray,
    ):
        image_h, image_w, _ = frame.shape
        for hand in self.hands:
            for finger in hand.fingers:
                pixel_x = int(finger.tip_x * image_w)
                pixel_y = int(finger.tip_y * image_h)

                color = (0, 0, 255) if finger.is_finger_bent() else (0, 255, 0)
                cv2.circle(frame, (pixel_x, pixel_y), 8, color, -1)
            wrist_pixel_x = int(hand.wrist.x * image_w)
            wrist_pixel_y = int(hand.wrist.y * image_h)
            cv2.circle(frame, (wrist_pixel_x, wrist_pixel_y), 8, (255, 0, 0), -1)

    def draw_note_name(self, midi_note: int, frame: np.ndarray):
        octave = (midi_note // 12) - 1
        note_index = midi_note % 12

        cv2.putText(
            frame,
            f"Note: {self.NOTE_NAMES[note_index]}{octave}",
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    def draw_scale_name(self, scale_name: str, frame: np.ndarray):
        cv2.putText(
            frame,
            f"Scale: {scale_name}",
            (50, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    def draw_volume(self, volume: float, frame: np.ndarray, left_wrist_x: float):
        image_h, image_w, _ = frame.shape
        volume_pixel_max = int(self.volume_ratio_max * image_h)
        volume_pixel_min = int(self.volume_ratio_min * image_h)
        circle_y = int(
            image_h
            - volume_pixel_min
            - (volume * (image_h - volume_pixel_min - volume_pixel_max))
        )
        circle_x = 20

        cv2.line(
            frame,
            (circle_x, volume_pixel_max),
            (circle_x, image_h - volume_pixel_min),
            (0, 255, 0),
            2,
        )
        cv2.circle(frame, (circle_x, circle_y), 4, (0, 255, 0), -1)

        left_wrist_pixel_x = int(left_wrist_x * image_w)
        cv2.line(
            frame,
            (left_wrist_pixel_x, circle_y),
            (10, circle_y),
            (0, 255, 0),
            1,
        )

        cv2.putText(
            frame,
            f"{volume:.2f}",
            (circle_x + 10, circle_y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

    def get_video(
        self, hand_detector, frame: np.ndarray, draw_landmarks_enabled: bool
    ) -> np.ndarray:
        frame = cv2.flip(cv2.resize(frame, (640, 360)), 1)
        frame.flags.writeable = False
        image_to_detect = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = hand_detector.process(image_to_detect)

        frame.flags.writeable = True

        resized_frame = cv2.resize(frame, (1280, 720))
        if results.multi_hand_world_landmarks and results.multi_hand_landmarks:
            self.hands = self.get_hand_landmarks(
                results.multi_hand_world_landmarks,
                results.multi_hand_landmarks,
                results.multi_handedness,
            )

            if draw_landmarks_enabled:
                self.draw_landmarks(
                    resized_frame,
                )

        return resized_frame
