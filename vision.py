import cv2
import mediapipe as mp

from hand import Hand


class Vision:
    def __init__(self):
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

        self.hands = []

    def get_hand_landmarks(
        self,
        multi_hand_world_landmarks: list,
        multi_hand_landmarks: list,
        multi_handedness: list,
    ) -> list:
        hands = []

        for i, hand_landmarks in enumerate(multi_hand_world_landmarks):
            hand_label = multi_handedness[i].classification[0].label
            hand_world_landmark = hand_landmarks.landmark
            hand_landmark = multi_hand_landmarks[i].landmark
            hands.append(Hand(hand_label, hand_world_landmark, hand_landmark))

        return hands

    def draw_landmarks(
        self,
        frame,
    ):
        image_h, image_w, _ = frame.shape
        for hand in self.hands:
            is_right_hand = hand.handedness == "Right"
            for finger_tip in hand.finger_tips:
                pixel_x = int(finger_tip.x * image_w)
                pixel_y = int(finger_tip.y * image_h)

                color = (
                    (0, 0, 255)
                    if is_right_hand and finger_tip.is_finger_bent()
                    else (0, 255, 0)
                )
                cv2.circle(frame, (pixel_x, pixel_y), 8, color, -1)

    def draw_coords(self, normal_x: float, normal_y: float, frame):
        image_h, image_w, _ = frame.shape
        pixel_x = int(normal_x * image_w)
        pixel_y = int(normal_y * image_h)

        cv2.putText(
            frame,
            f"X:{round(normal_x, 2)} Y:{round(normal_y, 2)}",
            (pixel_x - 50, pixel_y - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2,
        )

    def draw_note_name(self, midi_note: int, frame):
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

    def get_video(self, hand_detector, frame, draw_landmarks_enabled):
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

            if draw_landmarks_enabled:
                self.draw_landmarks(
                    frame,
                )
                if right_hand := next(
                    (hand for hand in self.hands if hand.handedness == "Right"), None
                ):
                    self.draw_coords(
                        right_hand.wrist.x,
                        right_hand.wrist.y,
                        frame,
                    )

                if left_hand := next(
                    (hand for hand in self.hands if hand.handedness == "Left"), None
                ):
                    self.draw_coords(
                        left_hand.wrist.x,
                        left_hand.wrist.y,
                        frame,
                    )

        resized_frame = cv2.resize(frame, (1280, 720))
        return resized_frame
