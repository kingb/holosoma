"""Input providers for holosoma_inference.

Two independent input channels:
- VelocityInput: continuous velocity commands (lin_vel, ang_vel)
- OtherInput: discrete commands (start/stop, walk/stand, kp tuning)

Each channel selects from keyboard, joystick, or ROS2 via config.
"""

from holosoma_inference.inputs.base import OtherInput, VelocityInput

__all__ = ["VelocityInput", "OtherInput"]
