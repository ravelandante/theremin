import cv2
import mediapipe as mp
import platform
import time
import numpy as np
from dataclasses import dataclass
from .midi_controller import MidiController
from .vision import Vision
from .hand import Hand
from collections import namedtuple

VOLUME_RATIO_BOUNDS = (0.14, 0.07)
DEBOUNCE_FRAMES = 3

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


@dataclass
class FingerOverlayData:
    tip_x: float
    tip_y: float
    is_bent: bool


@dataclass
class HandOverlayData:
    fingers: list
    control_x: float
    control_y: float


@dataclass
class FrameOverlay:
    hands: list
    draw_landmarks: bool
    note: int | None
    volume: float | None
    volume_controller_x: float | None

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
        self.cap = None

        self.previous_corrected_note = 0
        self.previous_clamped_volume = 0
        self.draw_landmarks_enabled = True

        self.previous_left_thumb_x = None
        self.previous_time = None
        self.previous_ok_hand = False
        # (handedness, finger_idx) -> [debounced_state, pending_state, pending_count]
        self._bend_debounce: dict = {}

        self._current_note: int | None = None
        self._current_volume: float | None = None
        self._current_volume_controller_x: float | None = None

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

    def toggle_landmarks(self):
        self.draw_landmarks_enabled = not self.draw_landmarks_enabled

    def _apply_debounce(self, *hands: Hand):
        for hand in hands:
            for i, finger in enumerate(hand.fingers):
                raw = finger.raw_is_finger_bent()
                key = (hand.handedness, i)
                if key not in self._bend_debounce:
                    self._bend_debounce[key] = [raw, raw, 1]
                    finger.debounced_bent = raw
                    continue
                debounced, pending, count = self._bend_debounce[key]
                if raw == pending:
                    count += 1
                    if count >= DEBOUNCE_FRAMES:
                        debounced = pending
                else:
                    pending = raw
                    count = 1
                self._bend_debounce[key] = [debounced, pending, count]
                finger.debounced_bent = debounced

    def perform(self, right_hand: Hand, left_hand: Hand):
        volume_min, volume_max = VOLUME_RATIO_BOUNDS[0], 1.0 - VOLUME_RATIO_BOUNDS[1]

        clamped_volume = max(
            0.0,
            min(
                1.0,
                (left_hand.fingers[2].mcp_y - volume_min) / (volume_max - volume_min),
            ),
        )
        clamped_pitch = max(0.0, min(1.0, right_hand.wrist.y))

        self._current_volume = clamped_volume
        self._current_volume_controller_x = left_hand.fingers[2].mcp_x

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

            is_ok = left_hand.is_ok_hand()
            if is_ok:
                current_time = time.time()
                self.controller.calculate_and_send_pitch_bend(
                    left_hand.fingers[0].tip_x,
                    self.previous_left_thumb_x,
                    current_time,
                    self.previous_time,
                )
                self.previous_left_thumb_x = left_hand.fingers[0].tip_x
                self.previous_time = current_time
            elif self.previous_ok_hand:
                self.controller.reset_pitch_bend()
            self.previous_ok_hand = is_ok

            self.previous_corrected_note = corrected_note
            self.previous_clamped_volume = clamped_volume
            self._current_note = corrected_note
        else:
            self.controller.stop_midi()
            self.previous_corrected_note = 0
            self._current_note = None

    def _build_overlay(self) -> FrameOverlay:
        hand_overlays = []
        for hand in self.vision.hands:
            fingers = [
                FingerOverlayData(f.tip_x, f.tip_y, f.is_finger_bent())
                for f in hand.fingers
            ]
            if hand.handedness == "Left":
                cx, cy = hand.fingers[2].mcp_x, hand.fingers[2].mcp_y
            else:
                cx, cy = hand.wrist.x, hand.wrist.y
            hand_overlays.append(HandOverlayData(fingers, cx, cy))

        return FrameOverlay(
            hands=hand_overlays,
            draw_landmarks=self.draw_landmarks_enabled,
            note=self._current_note,
            volume=self._current_volume,
            volume_controller_x=self._current_volume_controller_x,
        )

    def initialize_capture(self):
        backend = cv2.CAP_AVFOUNDATION if platform.system() == "Darwin" else cv2.CAP_ANY
        self.cap = cv2.VideoCapture(0, backend)
        if not self.cap.isOpened():
            raise RuntimeError("Could not open camera. Check that it is connected and that permission has been granted.")
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.hand_detector = self.mp_hands.Hands(
            model_complexity=0,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            max_num_hands=2,
        )

    def capture_frame_and_perform(self):
        success, frame = self.cap.read()
        if not success:
            return False, None, None

        final_frame = self.vision.get_video(self.hand_detector, frame)

        if right_hand := next(
            (hand for hand in self.vision.hands if hand.handedness == "Right"),
            None,
        ):
            if left_hand := next(
                (hand for hand in self.vision.hands if hand.handedness == "Left"),
                None,
            ):
                self._apply_debounce(right_hand, left_hand)
                self.perform(right_hand, left_hand)
        else:
            self.controller.stop_midi()
            self.previous_corrected_note = 0
            self._current_note = None
            self._current_volume = None
            self._current_volume_controller_x = None

        return True, final_frame, self._build_overlay()

    def release_resources(self):
        self.cap.release()
        self.controller.stop_midi()
        self.controller.midiout.close_port()

    def main_loop(self):
        try:
            self.initialize_capture()

            while self.cap.isOpened():
                success, final_frame, _ = self.capture_frame_and_perform()
                if not success:
                    continue

                cv2.imshow("Theremin", final_frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                elif key == ord("d"):
                    self.toggle_landmarks()
                elif key == ord("s"):
                    self.cycle_scale()

        finally:
            self.release_resources()
            cv2.destroyAllWindows()


if __name__ == "__main__":
    theremin = Theremin()
    theremin.main_loop()
