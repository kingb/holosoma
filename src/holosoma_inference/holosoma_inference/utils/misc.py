import os
import subprocess


def prioritize_conda_over_ros() -> None:
    """Reorder sys.path to prioritize conda/pip packages over ROS system packages.

    ROS setup scripts prepend /opt/ros/*/site-packages to PYTHONPATH, which can cause
    version conflicts (e.g., ROS pinocchio compiled against NumPy 1.x vs conda NumPy 2.x).

    This reorders sys.path so conda/pip site-packages take precedence over ROS paths,
    while keeping ROS packages accessible at lower priority.

    Note: For entry point scripts, prefer `import holosoma_inference.utils._ros_compat`
    at the top of the file, which executes the reordering on import.
    """
    from . import _ros_compat  # noqa: F401


def get_holosoma_inference_root() -> str:
    """Get the root directory of the holosoma_inference package."""
    import holosoma_inference

    return os.path.dirname(holosoma_inference.__file__)


def resolve_holosoma_inference_path(path: str) -> str:
    """Resolve @holosoma_inference/ path prefix to absolute path.

    Args:
        path: Path that may contain @holosoma_inference/ prefix

    Returns:
        Resolved absolute path
    """
    if path.startswith("@holosoma_inference/"):
        return path.replace("@holosoma_inference", get_holosoma_inference_root())
    return path


def restore_terminal_settings() -> None:
    """Restore terminal settings to sane defaults.

    This is needed because sshkeyboard.listen_keyboard() puts the terminal
    into raw mode to capture keystrokes directly. This function restores
    the terminal to normal mode before closing the process.
    """
    subprocess.run(["stty", "sane"], check=False)
