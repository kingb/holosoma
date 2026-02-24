"""ROS compatibility module - must be imported before any other holosoma_inference modules.

This module reorders sys.path to prioritize conda/pip packages over ROS system packages.
ROS setup scripts (e.g., `source /opt/ros/humble/setup.bash`) prepend ROS paths to PYTHONPATH,
which can cause version conflicts when ROS packages shadow conda packages.

Example: ROS Humble ships pinocchio compiled against NumPy 1.x, but your conda env may have
NumPy 2.x. Without path reordering, Python loads the ROS pinocchio and crashes.

Usage:
    # At the very top of your entry point script, before any other imports:
    import holosoma_inference.utils._ros_compat  # noqa: F401

This module automatically reorders sys.path when imported.
"""

import sys

# Reorder sys.path: conda/pip site-packages first, ROS paths last
_conda_paths = [p for p in sys.path if "site-packages" in p and "/opt/ros" not in p]
_ros_paths = [p for p in sys.path if "/opt/ros" in p]
_other_paths = [p for p in sys.path if p not in _conda_paths and p not in _ros_paths]
sys.path = _other_paths + _conda_paths + _ros_paths
del _conda_paths, _ros_paths, _other_paths
