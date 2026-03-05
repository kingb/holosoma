"""Configuration values for motion data format."""

from __future__ import annotations

from typing import Mapping

import tyro

from holosoma_retargeting.config_types.data_type import MotionDataConfig
from holosoma_retargeting.config_types.robot import RobotDefaults


def get_default_motion_data_config(
    data_format: str = "smplh",
    robot_type: str = "g1",
    robot_defaults: Mapping[str, RobotDefaults] | None = None,
) -> MotionDataConfig:
    """Get default motion data configuration.

    Args:
        data_format: Motion data format type.
        robot_type: Robot type for joint mapping.
        robot_defaults: Optional robot defaults map to validate robot_type against.

    Returns:
        MotionDataConfig: Default configuration instance.
    """
    if robot_defaults is None:
        return MotionDataConfig(data_format=data_format, robot_type=robot_type)
    return MotionDataConfig(
        data_format=data_format,
        robot_type=robot_type,
        robot_defaults=dict(robot_defaults),
    )


def get_motion_data_config_from_cli() -> MotionDataConfig:
    """Get motion data configuration from tyro CLI."""
    return tyro.cli(MotionDataConfig)


__all__ = [
    "get_default_motion_data_config",
    "get_motion_data_config_from_cli",
]
