import mediapipe as mp

from finger import Finger


class Hand:
    def __init__(self, handedness, world_landmarks, image_landmarks):
        self.mp_hands = mp.solutions.hands

        self.handedness = handedness

        self.finger_tips = [
            Finger(
                "thumb",
                image_landmarks[self.mp_hands.HandLandmark.THUMB_TIP],
                world_landmarks[self.mp_hands.HandLandmark.THUMB_TIP],
            ),
            Finger(
                "index",
                image_landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_TIP],
                world_landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_TIP],
            ),
            Finger(
                "middle",
                image_landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP],
                world_landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP],
            ),
            Finger(
                "ring",
                image_landmarks[self.mp_hands.HandLandmark.RING_FINGER_TIP],
                world_landmarks[self.mp_hands.HandLandmark.RING_FINGER_TIP],
            ),
            Finger(
                "pinky",
                image_landmarks[self.mp_hands.HandLandmark.PINKY_TIP],
                world_landmarks[self.mp_hands.HandLandmark.PINKY_TIP],
            ),
        ]

        self.wrist = image_landmarks[self.mp_hands.HandLandmark.WRIST]
