import cv2
import numpy as np


def calculate_steering(image):
    """
    Takes a BGR camera image.

    Returns:
        angular_velocity: float (rad/s)
    """

    # Convert image to HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Detect white pixels
    lower_white = np.array([0, 0, 180])
    upper_white = np.array([179, 65, 255])

    mask = cv2.inRange(hsv, lower_white, upper_white)

    # Select bottom portion of image
    height, width = mask.shape

    roi = mask[
        int(height * 0.7):int(height * 0.9),
        :
    ]

    # Split ROI into three sections
    third = width // 3

    left = roi[:, :third]
    right = roi[:, 2 * third:]

    # Fraction of white pixels in each region
    left_white = np.mean(left > 0)
    right_white = np.mean(right > 0)

    # Steering calculation
    error = right_white - left_white

    Kp = 5.0

    angular_velocity = Kp * error

    # Limit turning speed
    angular_velocity = np.clip(
        angular_velocity,
        -0.5,
        0.5
    )

    return float(angular_velocity)