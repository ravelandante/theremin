import cv2
import mediapipe as mp

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

        cv2.imshow('image', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()