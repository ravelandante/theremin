import cv2
import mediapipe as mp
import rtmidi

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands

NOTE_ON_CH1 = 0x90
NOTE_OFF_CH1 = 0x80
AFTERTOUCH_CH1 = 0xD0

midiout = rtmidi.MidiOut()
available_ports = midiout.get_ports()

if available_ports:
    midiout.open_port(0)
else:
    print("opening virtual port")
    midiout.open_virtual_port("My virtual output")

def send_midi(corrected_note: int, previous_corrected_note: int, clamped_volume: float) -> int:
    normalised_volume = (1 - clamped_volume) * 127

    if previous_corrected_note != corrected_note:
        midiout.send_message([NOTE_ON_CH1, corrected_note, normalised_volume])
        midiout.send_message([NOTE_OFF_CH1, previous_corrected_note, 0])

    note_aftertouch = [AFTERTOUCH_CH1, normalised_volume]
    midiout.send_message(note_aftertouch)
    return corrected_note

def get_corrected_note(clamped_pitch: float, left_hand_landmarks: list) -> int:
    base_note = round(1 - clamped_pitch, 1) * 10 + 60

    finger_ys = {
        "index": -left_hand_landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP].y,
        "middle": -left_hand_landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y,
        "ring": -left_hand_landmarks[mp_hands.HandLandmark.RING_FINGER_TIP].y,
        "pinky": -left_hand_landmarks[mp_hands.HandLandmark.PINKY_TIP].y,
    }

    if finger_ys["index"] < 0.03:
        base_note += 2
        if finger_ys["middle"] < 0.05:
            base_note += 2
            if finger_ys["ring"] < 0.05:
                base_note += 1
                if finger_ys["pinky"] < 0.03:
                    base_note += 2
    
    return int(base_note)

def get_hand_landmarks(multi_hand_landmarks: list, multi_handedness: list) -> list:
    right_wrist_landmarks = None
    left_wrist_landmarks = None
    for i, hand_landmarks in enumerate(multi_hand_landmarks):
        hand_label = multi_handedness[i].classification[0].label

        hand_landmark = hand_landmarks.landmark

        if hand_label == "Right":
            right_wrist_landmarks = hand_landmark
        elif hand_label == "Left":
            left_wrist_landmarks = hand_landmark
        
    return [right_wrist_landmarks, left_wrist_landmarks]

def draw_landmarks(multi_hand_landmarks: list, frame):
    for hand_landmarks in multi_hand_landmarks:
        mp_drawing.draw_landmarks(
            frame,
            hand_landmarks,
            mp_hands.HAND_CONNECTIONS,
            mp_drawing_styles.get_default_hand_landmarks_style(),
            mp_drawing_styles.get_default_hand_connections_style())

def draw_coords(normal_x: float, normal_y: float, image_w: int, image_h: int):
    pixel_x = int(normal_x * image_w)
    pixel_y = int(normal_y * image_h)

    cv2.putText(frame, 
        f'X:{round(normal_x, 2)} Y:{round(normal_y, 2)}', 
        (pixel_x - 50, pixel_y - 20), 
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

cap = cv2.VideoCapture(0)
with mp_hands.Hands(
    model_complexity=0,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5) as hand_detector:

    previous_corrected_note = 0
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("unable to get webcam feed")
            continue

        frame.flags.writeable = False
        image_to_detect = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hand_detector.process(image_to_detect)
        frame.flags.writeable = True

        if results.multi_hand_landmarks:
            draw_landmarks(results.multi_hand_landmarks, frame)

        if results.multi_hand_world_landmarks and len(results.multi_hand_world_landmarks) == 2:
            world_landmarks = get_hand_landmarks(results.multi_hand_world_landmarks, results.multi_handedness)
            image_landmarks = get_hand_landmarks(results.multi_hand_landmarks, results.multi_handedness)
                
            if not image_landmarks[0] or not image_landmarks[1]:
                continue

            left_wrist = image_landmarks[1][mp_hands.HandLandmark.WRIST]
            right_wrist = image_landmarks[0][mp_hands.HandLandmark.WRIST]

            image_h, image_w, _ = frame.shape
            draw_coords(right_wrist.x, right_wrist.y, image_w, image_h)
            draw_coords(left_wrist.x, left_wrist.y, image_w, image_h)

            clamped_pitch = max(0.0, min(1.0, left_wrist.y))
            clamped_volume = max(0.0, min(1.0, right_wrist.y))

            left_wrist_landmarks = world_landmarks[1]

            corrected_note = get_corrected_note(clamped_pitch, left_wrist_landmarks)
            previous_corrected_note = send_midi(corrected_note, previous_corrected_note, clamped_volume)

        cv2.imshow('image', cv2.flip(frame, 1))

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
midiout.close_port()
