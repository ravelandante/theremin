import mediapipe as mp
from typing import List

from finger import Finger


class Hand:
    def __init__(self, handedness: str, world_landmarks, image_landmarks):
        self.mp_hands = mp.solutions.hands

        self.handedness = handedness

        self.finger_tips: List[Finger] = [
            Finger(
                "thumb",
                image_landmarks[self.mp_hands.HandLandmark.THUMB_TIP],
                world_landmarks[self.mp_hands.HandLandmark.THUMB_TIP],
                world_landmarks[self.mp_hands.HandLandmark.THUMB_IP],
            ),
            Finger(
                "index",
                image_landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_TIP],
                world_landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_TIP],
                world_landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_PIP],
            ),
            Finger(
                "middle",
                image_landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP],
                world_landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP],
                world_landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP],
            ),
            Finger(
                "ring",
                image_landmarks[self.mp_hands.HandLandmark.RING_FINGER_TIP],
                world_landmarks[self.mp_hands.HandLandmark.RING_FINGER_TIP],
                world_landmarks[self.mp_hands.HandLandmark.RING_FINGER_PIP],
            ),
            Finger(
                "pinky",
                image_landmarks[self.mp_hands.HandLandmark.PINKY_TIP],
                world_landmarks[self.mp_hands.HandLandmark.PINKY_TIP],
                world_landmarks[self.mp_hands.HandLandmark.PINKY_PIP],
            ),
        ]

        self.wrist = image_landmarks[self.mp_hands.HandLandmark.WRIST]

    def is_ok_hand(self) -> bool:
        # TODO: make this more robust by using distances between landmarks
        return (
            self.finger_tips[0].is_finger_bent()
            and self.finger_tips[1].is_finger_bent()
            and not self.finger_tips[2].is_finger_bent()
            and not self.finger_tips[3].is_finger_bent()
            and not self.finger_tips[4].is_finger_bent()
        )
