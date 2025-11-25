import mediapipe as mp
from typing import List
from .finger import Finger
from math import sqrt

THUMB_INDEX_DISTANCE_THRESHOLD = 0.05


class Hand:
    def __init__(self, handedness: str, world_landmarks, image_landmarks):
        self.mp_hands = mp.solutions.hands

        self.handedness = handedness

        self.fingers: List[Finger] = [
            Finger(
                "thumb",
                image_landmarks[self.mp_hands.HandLandmark.THUMB_TIP],
                world_landmarks[self.mp_hands.HandLandmark.THUMB_TIP],
                world_landmarks[self.mp_hands.HandLandmark.THUMB_IP],
                image_landmarks[self.mp_hands.HandLandmark.THUMB_MCP],
            ),
            Finger(
                "index",
                image_landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_TIP],
                world_landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_TIP],
                world_landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_PIP],
                image_landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_MCP],
            ),
            Finger(
                "middle",
                image_landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP],
                world_landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP],
                world_landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP],
                image_landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP],
            ),
            Finger(
                "ring",
                image_landmarks[self.mp_hands.HandLandmark.RING_FINGER_TIP],
                world_landmarks[self.mp_hands.HandLandmark.RING_FINGER_TIP],
                world_landmarks[self.mp_hands.HandLandmark.RING_FINGER_PIP],
                image_landmarks[self.mp_hands.HandLandmark.RING_FINGER_MCP],
            ),
            Finger(
                "pinky",
                image_landmarks[self.mp_hands.HandLandmark.PINKY_TIP],
                world_landmarks[self.mp_hands.HandLandmark.PINKY_TIP],
                world_landmarks[self.mp_hands.HandLandmark.PINKY_PIP],
                image_landmarks[self.mp_hands.HandLandmark.PINKY_MCP],
            ),
        ]

        self.wrist = image_landmarks[self.mp_hands.HandLandmark.WRIST]

    def calculate_finger_distance(self, finger1, finger2) -> float:
        return sqrt(
            (finger1.tip_world_x - finger2.tip_world_x) ** 2
            + (finger1.tip_world_y - finger2.tip_world_y) ** 2
            + (finger1.tip_world_z - finger2.tip_world_z) ** 2
        )

    def is_ok_hand(self) -> bool:
        thumb = self.fingers[0]
        index = self.fingers[1]

        if (
            self.fingers[2].is_finger_bent()
            or self.fingers[3].is_finger_bent()
            or self.fingers[4].is_finger_bent()
        ):
            return False

        thumb_index_distance = self.calculate_finger_distance(thumb, index)
        if thumb_index_distance > THUMB_INDEX_DISTANCE_THRESHOLD:
            return False

        return True
