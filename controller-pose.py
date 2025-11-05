import cv2
import mediapipe as mp
import rtmidi

NOTE_ON_CH1 = 0x90
NOTE_OFF_CH1 = 0x80
POLY_AFTERTOUCH_CH1 = 0xA0

midiout = rtmidi.MidiOut()
available_ports = midiout.get_ports()

if available_ports:
    midiout.open_port(0)
else:
    print("opening virtual port")
    midiout.open_virtual_port("My virtual output")

def send_midi(normalised_pitch, previous_corrected_note, volume):
    corrected_note = round(1 - normalised_pitch, 1) * 10 + 60
    corrected_volume = (1 - volume) * 127

    if previous_corrected_note != corrected_note:
        note_on = [NOTE_ON_CH1, corrected_note, corrected_volume]
        midiout.send_message(note_on)
        note_off = [NOTE_OFF_CH1, previous_corrected_note, 0]
        midiout.send_message(note_off)

    note_aftertouch = [POLY_AFTERTOUCH_CH1, corrected_note, corrected_volume]
    midiout.send_message(note_aftertouch)
    return corrected_note

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

def draw_coords(normal_x, normal_y, image_w, image_h):
    # coordinates are normalized (0.0 to 1.0):
    pixel_x = int(normal_x * image_w)
    pixel_y = int(normal_y * image_h)

    cv2.putText(frame, 
        f'X:{round(normal_x, 2)} Y:{round(normal_y, 2)}', 
        (pixel_x - 50, pixel_y - 20), 
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

cap = cv2.VideoCapture(0)

with mp_pose.Pose(
    min_detection_confidence=0.5, 
    min_tracking_confidence=0.5) as pose_detector:

    previous_corrected_note = 0
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("unable to get webcam feed")
            continue

        frame.flags.writeable = False
        
        # flip image for natural mirror view
        frame = cv2.flip(frame, 1)

        # convert image from BGR (OpenCV) to RGB (MediaPipe)
        image_to_detect = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        results = pose_detector.process(image_to_detect)
        
        frame.flags.writeable = True

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2)
            )

            if results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST] and results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST]:
                right_wrist = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST]
                left_wrist = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST]
                
                image_h, image_w, _ = frame.shape
                draw_coords(right_wrist.x, right_wrist.y, image_w, image_h)
                draw_coords(left_wrist.x, left_wrist.y, image_w, image_h)

                normalised_freq_coords = max(0.0, min(1.0, left_wrist.y))
                normalised_volume = max(0.0, min(1.0, right_wrist.y))

                previous_corrected_note = send_midi(normalised_freq_coords, previous_corrected_note, normalised_volume)

        cv2.imshow('image', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
midiout.close_port()
