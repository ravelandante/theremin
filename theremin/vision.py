import cv2
import numpy as np
from typing import List

from .hand import Hand


class Vision:
    def __init__(self, volume_ratio_max: float, volume_ratio_min: float):
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

    def get_video(self, hand_detector, frame: np.ndarray) -> np.ndarray:
        frame = cv2.flip(cv2.resize(frame, (640, 360)), 1)
        frame.flags.writeable = False
        image_to_detect = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = hand_detector.process(image_to_detect)

        frame.flags.writeable = True

        if results.multi_hand_world_landmarks and results.multi_hand_landmarks:
            self.hands = self.get_hand_landmarks(
                results.multi_hand_world_landmarks,
                results.multi_hand_landmarks,
                results.multi_handedness,
            )
        else:
            self.hands = []

        return frame
