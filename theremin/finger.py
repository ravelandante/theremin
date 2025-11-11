class Finger:
    def __init__(self, finger_type: str, finger_landmark, finger_world_landmark):
        self.finger_type = finger_type

        self.world_x = finger_world_landmark.x
        self.world_y = finger_world_landmark.y
        self.world_z = finger_world_landmark.z

        self.x = finger_landmark.x
        self.y = finger_landmark.y
        self.z = finger_landmark.z

    def is_finger_bent(self) -> bool:
        # TODO: make finger bend margins relative to hand size
        if self.finger_type == "thumb":
            return abs(self.world_x) < 0.06

        bend_thresholds = {
            "index": 0.03,
            "middle": 0.045,
            "ring": 0.04,
            "pinky": 0.03,
        }
        bend_threshold = bend_thresholds[self.finger_type]
        return -self.world_y < bend_threshold
