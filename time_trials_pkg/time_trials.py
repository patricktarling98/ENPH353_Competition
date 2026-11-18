import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data

from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist
from std_msgs.msg import String

from cv_bridge import CvBridge

from .lane_following import calculate_steering


# Competition settings
TEAM_NAME = "Team7"
PASSWORD = "team7"
TRIAL_DURATION = 20.0  # Simulation seconds


class TimeTrials(Node):

    def __init__(self):
        super().__init__(
            'time_trials_node',
            parameter_overrides=[
                Parameter('use_sim_time', value=True)
            ]
        )

        self.bridge = CvBridge()
        self.latest_image = None
        self.last_image_time = None

        # Competition state
        self.competition_started = False
        self.competition_finished = False
        self.start_time = None

        # Camera subscriber
        self.camera_sub = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.camera_callback,
            qos_profile_sensor_data
        )

        # Velocity publisher
        self.vel_pub = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        # Competition scoring publisher
        self.score_pub = self.create_publisher(
            String,
            '/score_tracker',
            10
        )

        # Control loop (10 Hz)
        self.timer = self.create_timer(
            0.1,
            self.control_loop
        )

        self.get_logger().info("Time trials controller initialized")

    # -------- CAMERA --------

    def camera_callback(self, msg):
        self.latest_image = self.bridge.imgmsg_to_cv2(
            msg,
            desired_encoding='bgr8'
        )
        self.last_image_time = self.get_clock().now()

    # -------- MOVEMENT --------

    def drive(self, linear, angular):
        msg = Twist()
        msg.linear.x = float(linear)
        msg.angular.z = float(angular)
        self.vel_pub.publish(msg)

    def stop(self):
        self.drive(0.0, 0.0)

    # -------- COMPETITION TIMER --------

    def send_score(self, clue_id, clue_value="NA"):
        msg = String()
        msg.data = (
            f"{TEAM_NAME},{PASSWORD},{clue_id},{clue_value}"
        )
        self.score_pub.publish(msg)

    def start_competition(self):
        self.send_score(0)

        self.start_time = self.get_clock().now()
        self.competition_started = True

        self.get_logger().info("Competition START message published")

    def stop_competition(self):
        if not self.competition_started or self.competition_finished:
            return

        self.stop()
        self.send_score(-1)

        self.competition_finished = True

        self.get_logger().info("Competition STOP message published")

    # -------- CONTROLLER --------

    def control_loop(self):
        now = self.get_clock().now()

        # Stop permanently after the trial ends
        if self.competition_finished:
            self.stop()
            return

        # Wait for camera and score tracker
        if not self.competition_started:
            self.stop()

            if self.latest_image is None:
                return

            if self.score_pub.get_subscription_count() == 0:
                return

            # Ensure simulation clock has started
            if now.nanoseconds == 0:
                return

            self.start_competition()
            return

        # Calculate elapsed simulation time
        elapsed = (
            now - self.start_time
        ).nanoseconds / 1e9

        # Automatically finish after trial duration
        if elapsed >= TRIAL_DURATION:
            self.stop_competition()
            return

        # Stop if camera data is unavailable or stale
        if self.latest_image is None or self.last_image_time is None:
            self.stop()
            return

        image_age = (
            now - self.last_image_time
        ).nanoseconds / 1e9

        if image_age < 0 or image_age > 0.5:
            self.stop()
            return

        # Calculate steering
        angular_velocity = calculate_steering(
            self.latest_image
        )

        # Drive robot
        self.drive(
            linear=0.5,
            angular=angular_velocity
        )


def main(args=None):
    rclpy.init(args=args)

    node = TimeTrials()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.stop()

        # Send stop message if interrupted during a trial
        if node.competition_started:
            node.stop_competition()

        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()