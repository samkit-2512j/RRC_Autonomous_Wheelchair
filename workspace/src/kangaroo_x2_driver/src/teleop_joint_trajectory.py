#!/usr/bin/env python

# Copyright (c) 2011, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the Willow Garage, Inc. nor the names of its
#      contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import rospy
# from geometry_msgs.msg import Twist
from std_msgs.msg import Header
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import sys, select, os
if os.name == 'nt':
  import msvcrt
else:
  import tty, termios

WHEELCHAIR_MAX_LIN_VEL = 2 		#Max velocity for Wheelchair_V(m/s)
WHEELCHAIR_MAX_ANG_VEL = 0.5

LIN_VEL_STEP_SIZE = 0.005 #0.1 m/s
ANG_VEL_STEP_SIZE = 0.15 #0.1 m/s

msg = """
Control Your Wheelchair!
---------------------------
Moving around:
        w
   a    s    d
        x
w/x : increase/decrease linear velocity (Wheelchair : ~ 0.22)
a/d : increase/decrease angular velocity (Wheelchair : ~ 2.84)
space key, s : force stop
CTRL-C to quit
"""

e = """
Communications Failed
"""

def getKey():
    if os.name == 'nt':
      return msvcrt.getch()

    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''

    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key

def vels(target_linear_vel, target_angular_vel):
    return "currently:\tlinear vel %s\t angular vel %s " % (target_linear_vel,target_angular_vel)

def makeSimpleProfile(output, input, slop):
    if input > output:
        output = min( input, output + slop )
    elif input < output:
        output = max( input, output - slop )
    else:
        output = input

    return output

def constrain(input, low, high):
    if input < low:
      input = low
    elif input > high:
      input = high
    else:
      input = input

    return input

def checkLinearLimitVelocity(vel):
    vel = constrain(vel, -WHEELCHAIR_MAX_LIN_VEL, WHEELCHAIR_MAX_LIN_VEL)
    return vel

def checkAngularLimitVelocity(vel):
    vel = constrain(vel, -WHEELCHAIR_MAX_ANG_VEL, WHEELCHAIR_MAX_ANG_VEL)
    return vel

if __name__=="__main__":
    if os.name != 'nt':
        settings = termios.tcgetattr(sys.stdin)

    rospy.init_node('Wheelchair_teleop')
    # pub = rospy.Publisher('wheelchair_diff/cmd_vel', Twist, queue_size=10)
    pub = rospy.Publisher('/joint_trajectory/', JointTrajectory, queue_size=10)
    rate = rospy.Rate(100)
    status = 0
    target_linear_vel   = 0.0
    target_angular_vel  = 0.0
    control_linear_vel  = 0.0
    control_angular_vel = 0.0

    try:
        print(msg)
        while(1):
            key = getKey()
            if key == 'w' :
                target_linear_vel = checkLinearLimitVelocity(target_linear_vel + LIN_VEL_STEP_SIZE)
                status = status + 1
                print(vels(target_linear_vel,target_angular_vel))
            elif key == 'x' :
                target_linear_vel = checkLinearLimitVelocity(target_linear_vel - LIN_VEL_STEP_SIZE)
                status = status + 1
                print(vels(target_linear_vel,target_angular_vel))
            elif key == 'a' :
                target_angular_vel = checkAngularLimitVelocity(target_angular_vel + ANG_VEL_STEP_SIZE)
                status = status + 1
                print(vels(target_linear_vel,target_angular_vel))
            elif key == 'd' :
                target_angular_vel = checkAngularLimitVelocity(target_angular_vel - ANG_VEL_STEP_SIZE)
                status = status + 1
                print(vels(target_linear_vel,target_angular_vel))
            elif key == ' ' or key == 's' :
                target_linear_vel   = 0.0
                control_linear_vel  = 0.0
                target_angular_vel  = 0.0
                control_angular_vel = 0.0
                print(vels(target_linear_vel, target_angular_vel))
            else:
                if (key == '\x03'):
                    break

            if status == 20 :
                print(msg)
                status = 0

            # twist = Twist()

            control_linear_vel = makeSimpleProfile(control_linear_vel, target_linear_vel, (LIN_VEL_STEP_SIZE/2.0))
            # twist.linear.x = control_linear_vel; twist.linear.y = 0.0; twist.linear.z = 0.0

            control_angular_vel = makeSimpleProfile(control_angular_vel, target_angular_vel, (ANG_VEL_STEP_SIZE/2.0))
            # twist.angular.x = 0.0; twist.angular.y = 0.0; twist.angular.z = control_angular_vel

            joints_str = JointTrajectory()
            joints_str.header = Header()
            joints_str.header.stamp = rospy.Time.now()
            joints_str.joint_names = ['3', '4']
            point = JointTrajectoryPoint()
            point.velocities = [target_linear_vel, target_angular_vel]
            point.time_from_start = rospy.Duration(2)
            joints_str.points.append(point)

            pub.publish(joints_str)

            # pub.publish(twist)
            rate.sleep()


    except:
        print(e)

    finally:
        # twist = Twist()
        # twist.linear.x = 0.0; twist.linear.y = 0.0; twist.linear.z = 0.0
        # twist.angular.x = 0.0; twist.angular.y = 0.0; twist.angular.z = 0.0
        # pub.publish(twist)

        joints_str = JointTrajectory()
        joints_str.header = Header()
        joints_str.header.stamp = rospy.Time.now()
        joints_str.joint_names = ['3', '4']
        point = JointTrajectoryPoint()
        point.velocities = [0.0, 0.0]
        point.time_from_start = rospy.Duration(2)
        joints_str.points.append(point)

        pub.publish(joints_str)

    if os.name != 'nt':
       termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)