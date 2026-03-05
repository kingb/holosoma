"""Configuration values for robot retargeting."""

from __future__ import annotations

from typing import Mapping

import tyro

from holosoma_retargeting.config_types.robot import RobotConfig, RobotDefaults


def get_default_robot_config(
    robot_type: str = "g1",
    robot_defaults: Mapping[str, RobotDefaults] | None = None,
) -> RobotConfig:
    """Get default robot configuration.

    Args:
        robot_type: Robot type identifier.
        robot_defaults: Optional robot defaults map to override built-in defaults.

    Returns:
        RobotConfig: Default configuration instance.
    """
    if robot_defaults is None:
        return RobotConfig(robot_type=robot_type)
    return RobotConfig(robot_type=robot_type, robot_defaults=dict(robot_defaults))


def get_robot_config_from_cli() -> RobotConfig:
    """Get robot configuration from tyro CLI.

    Returns:
        RobotConfig: Configuration instance from CLI arguments.
    """
    return tyro.cli(RobotConfig)


__all__ = ["get_default_robot_config", "get_robot_config_from_cli"]
