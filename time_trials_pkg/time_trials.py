#Add code to drive robot and publish to score tracker

import rclpy # type: ignore
import time
from rclpy.node import Node # type: ignore
from geometry_msgs.msg import Twist # type: ignore
from std_msgs.msg import String

class Driver_Node(Node):
    def __init__(self):
        #Publish messages as: String(data='TeamRed,multi21,2,JEDIS'), name,psw,location id, prediction
        #id 0 for start, -1 for end

        START_TIMER_MESSAGE = String(data='Team7,psw,0,nothing')
        STOP_TIMER_MESSAGE = String(data='Team7,psw,-1,nothing')

        super().__init__(node_name='driver_node')
        self.cmd_vel_pub = self.create_publisher(msg_type=Twist, topic='/cmd_vel', qos_profile=10)
        self.score_pub = self.create_publisher(msg_type=String, topic='/score_tracker', qos_profile=10)
        time.sleep(2.0)

        self.score_pub.publish(msg=START_TIMER_MESSAGE)

        self.move = Twist()
        self.move.linear.x = 0.5
        self.move.angular.z = 0.0
        self.get_logger().info("Start driving:")
        self.cmd_vel_pub.publish(msg=self.move)

        time.sleep(4.0)
        self.move.linear.x = 0.0
        self.get_logger().info("Stop driving")
        self.cmd_vel_pub.publish(msg=self.move)

        self.score_pub.publish(msg=STOP_TIMER_MESSAGE)
        

def main():
    rclpy.init(args=None)
    driver = Driver_Node()
    rclpy.spin(driver)
    rclpy.shutdown()
