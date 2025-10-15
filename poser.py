import cv2
import mediapipe as mp
import pyaudio
import numpy as np

SAMPLE_RATE = 44100
TONE_DURATION_SEC = 0.1                              # chunk duration in seconds
CHUNK_SIZE = int(SAMPLE_RATE * TONE_DURATION_SEC)    # number of frames per chunk

MIN_FREQUENCY_HZ = 65.41    # C2
MAX_FREQUENCY_HZ = 1046.5   # C6

# TODO: replace global variables with class state
global_frequency_normalised = 0.0
global_previous_frequency_normalised = 0.0
global_volume = 1.0
global_current_phase = 0.0

def audio_callback(_in_data, frame_count, _timing_info, _status):
    global global_current_phase
    global global_frequency_normalised
    global global_volume
    global global_previous_frequency_normalised

    # interpolate from global_previous_frequency_normalised to global_frequency_normalised over frame_count steps
    interpolated_normalised_freqs = np.linspace(
        global_previous_frequency_normalised,
        global_frequency_normalised,
        frame_count,
        endpoint=False
    )

    interpolated_frequencies_hz = MIN_FREQUENCY_HZ + (1 - interpolated_normalised_freqs) * (MAX_FREQUENCY_HZ - MIN_FREQUENCY_HZ)
    angular_frequencies = 2.0 * np.pi * interpolated_frequencies_hz
    
    # calculate the change in phase (delta_phase) for each sample
    delta_phases = angular_frequencies * (1.0 / SAMPLE_RATE)
    
    # cumulatively sum the phase changes starting from 'global_current_phase'
    phases = global_current_phase + np.cumsum(delta_phases) - delta_phases[0]
    
    # add a fade-in/fade-out (Hanning window) to the chunk to reduce clicks
    window = np.hanning(frame_count)
    
    # tone generation: V * sin(phases) * window
    samples = ((1 - global_volume) * np.sin(phases) * window).astype(np.float32)

    # store the phase at the end of this chunk for the next chunk's start
    global_current_phase = phases[-1] % (2.0 * np.pi) 
    global_previous_frequency_normalised = global_frequency_normalised
    
    return (samples.tobytes(), pyaudio.paContinue)

player = pyaudio.PyAudio()
stream = player.open(format=pyaudio.paFloat32,
                     channels=1,
                     rate=SAMPLE_RATE,
                     output=True,
                     frames_per_buffer=CHUNK_SIZE,
                     stream_callback=audio_callback)

stream.start_stream()

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

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("unable to get webcam feed")
            continue

        # flip image for natural mirror view
        frame = cv2.flip(frame, 1)

        # convert image from BGR (OpenCV) to RGB (MediaPipe)
        image_to_detect = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        results = pose_detector.process(image_to_detect)
        
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

                global_frequency_normalised = max(0.0, min(1.0, left_wrist.y))
                global_volume = max(0.0, min(1.0, right_wrist.y))

        cv2.imshow('image', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
player.close(stream)
stream.stop_stream()
stream.close()