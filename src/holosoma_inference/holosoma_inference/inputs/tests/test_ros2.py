"""Tests for ROS2 input providers."""

from types import SimpleNamespace

import numpy as np


class TestRos2VelocityInput:
    def test_callback_writes_velocity(self, policy):
        from holosoma_inference.inputs.ros2 import Ros2VelocityInput

        prov = Ros2VelocityInput(policy)
        msg = SimpleNamespace(
            twist=SimpleNamespace(
                linear=SimpleNamespace(x=0.5, y=-0.3),
                angular=SimpleNamespace(z=0.8),
            )
        )
        prov._callback(msg)

        np.testing.assert_almost_equal(policy.lin_vel_command[0, 0], 0.5)
        np.testing.assert_almost_equal(policy.lin_vel_command[0, 1], -0.3)
        np.testing.assert_almost_equal(policy.ang_vel_command[0, 0], 0.8)

    def test_callback_clamps_to_range(self, policy):
        from holosoma_inference.inputs.ros2 import Ros2VelocityInput

        prov = Ros2VelocityInput(policy)
        msg = SimpleNamespace(
            twist=SimpleNamespace(
                linear=SimpleNamespace(x=5.0, y=-5.0),
                angular=SimpleNamespace(z=99.0),
            )
        )
        prov._callback(msg)

        assert policy.lin_vel_command[0, 0] == 1.0
        assert policy.lin_vel_command[0, 1] == -1.0
        assert policy.ang_vel_command[0, 0] == 1.0

    def test_callback_clamps_negative_angular(self, policy):
        from holosoma_inference.inputs.ros2 import Ros2VelocityInput

        prov = Ros2VelocityInput(policy)
        msg = SimpleNamespace(
            twist=SimpleNamespace(
                linear=SimpleNamespace(x=0.0, y=0.0),
                angular=SimpleNamespace(z=-99.0),
            )
        )
        prov._callback(msg)

        assert policy.ang_vel_command[0, 0] == -1.0


class TestRos2OtherInput:
    def test_walk_command(self, policy):
        from holosoma_inference.inputs.ros2 import Ros2OtherInput

        prov = Ros2OtherInput(policy)
        prov._callback(SimpleNamespace(data="walk"))
        assert policy.stand_command[0, 0] == 1
        np.testing.assert_almost_equal(policy.base_height_command[0, 0], 0.5)

    def test_stand_command(self, policy):
        from holosoma_inference.inputs.ros2 import Ros2OtherInput

        policy.stand_command[0, 0] = 1
        prov = Ros2OtherInput(policy)
        prov._callback(SimpleNamespace(data="stand"))
        assert policy.stand_command[0, 0] == 0

    def test_start_command(self, policy):
        from holosoma_inference.inputs.ros2 import Ros2OtherInput

        prov = Ros2OtherInput(policy)
        prov._callback(SimpleNamespace(data="start"))
        policy._handle_start_policy.assert_called_once()

    def test_stop_command(self, policy):
        from holosoma_inference.inputs.ros2 import Ros2OtherInput

        prov = Ros2OtherInput(policy)
        prov._callback(SimpleNamespace(data="stop"))
        policy._handle_stop_policy.assert_called_once()

    def test_init_command(self, policy):
        from holosoma_inference.inputs.ros2 import Ros2OtherInput

        prov = Ros2OtherInput(policy)
        prov._callback(SimpleNamespace(data="init"))
        policy._handle_init_state.assert_called_once()

    def test_unknown_command_warns(self, policy):
        from holosoma_inference.inputs.ros2 import Ros2OtherInput

        prov = Ros2OtherInput(policy)
        prov._callback(SimpleNamespace(data="bogus"))
        policy.logger.warning.assert_called_once()

    def test_whitespace_and_case_normalization(self, policy):
        from holosoma_inference.inputs.ros2 import Ros2OtherInput

        prov = Ros2OtherInput(policy)
        prov._callback(SimpleNamespace(data="  WALK  "))
        assert policy.stand_command[0, 0] == 1
