class Finger:
    def __init__(
        self,
        finger_type: str,
        finger_tip_landmark,
        finger_tip_world_landmark,
        finger_pip_world_landmark,
    ):
        self.finger_type = finger_type

        self.tip_x = finger_tip_landmark.x
        self.tip_y = finger_tip_landmark.y
        self.tip_z = finger_tip_landmark.z

        self.tip_world_x = finger_tip_world_landmark.x
        self.tip_world_y = finger_tip_world_landmark.y
        self.tip_world_z = finger_tip_world_landmark.z

        self.pip_world_x = finger_pip_world_landmark.x
        self.pip_world_y = finger_pip_world_landmark.y
        self.pip_world_z = finger_pip_world_landmark.z

    def is_finger_bent(self) -> bool:
        if self.finger_type == "thumb":
            return abs(self.tip_world_x) < 0.06

        y_adjuster = 0.015
        if self.finger_type == "ring":
            y_adjuster = 0.01
        elif self.finger_type == "pinky":
            y_adjuster = 0.02

        return self.tip_world_y > self.pip_world_y - y_adjuster
