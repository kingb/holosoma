"""Tests for joystick input providers."""

import numpy as np
import pytest


class TestJoystickVelocityInput:
    def test_poll_skips_when_no_msg(self, policy):
        from holosoma_inference.inputs.joystick import JoystickVelocityInput

        policy.interface.get_joystick_msg.return_value = None
        prov = JoystickVelocityInput(policy)
        prov.poll()
        policy.interface.process_joystick_input.assert_not_called()

    def test_poll_reads_and_caches(self, policy):
        from holosoma_inference.inputs.joystick import JoystickVelocityInput

        new_lin = np.array([[0.5, 0.0]])
        new_ang = np.array([[0.1]])
        new_keys = {"A": True}
        policy.interface.get_joystick_msg.return_value = "msg"
        policy.interface.process_joystick_input.return_value = (new_lin, new_ang, new_keys)

        prov = JoystickVelocityInput(policy)
        prov.poll()

        np.testing.assert_array_equal(policy.lin_vel_command, new_lin)
        np.testing.assert_array_equal(policy.ang_vel_command, new_ang)
        assert prov.key_states == {"A": True}

    def test_poll_preserves_last_key_states(self, policy):
        from holosoma_inference.inputs.joystick import JoystickVelocityInput

        policy.interface.get_joystick_msg.return_value = "msg"
        policy.interface.process_joystick_input.return_value = (
            policy.lin_vel_command,
            policy.ang_vel_command,
            {"A": True},
        )

        prov = JoystickVelocityInput(policy)
        prov.key_states = {"B": True}
        prov.poll()

        assert prov.last_key_states == {"B": True}
        assert prov.key_states == {"A": True}


class TestJoystickOtherInput:
    def test_button_dispatch_a(self, policy):
        from holosoma_inference.inputs.joystick import JoystickOtherInput

        prov = JoystickOtherInput(policy)
        assert prov.handle_joystick_button("A") is True
        policy._handle_start_policy.assert_called_once()

    def test_button_dispatch_b(self, policy):
        from holosoma_inference.inputs.joystick import JoystickOtherInput

        prov = JoystickOtherInput(policy)
        assert prov.handle_joystick_button("B") is True
        policy._handle_stop_policy.assert_called_once()

    def test_button_dispatch_y(self, policy):
        from holosoma_inference.inputs.joystick import JoystickOtherInput

        prov = JoystickOtherInput(policy)
        assert prov.handle_joystick_button("Y") is True
        policy._handle_init_state.assert_called_once()

    @pytest.mark.parametrize("key", ["up", "down", "left", "right", "F1"])
    def test_kp_control(self, policy, key):
        from holosoma_inference.inputs.joystick import JoystickOtherInput

        prov = JoystickOtherInput(policy)
        assert prov.handle_joystick_button(key) is True
        policy._handle_joystick_kp_control.assert_called_once_with(key)

    def test_select_cycles_policy(self, policy):
        from holosoma_inference.inputs.joystick import JoystickOtherInput

        prov = JoystickOtherInput(policy)
        assert prov.handle_joystick_button("select") is True
        policy._activate_policy.assert_called_once_with(1)

    def test_l1_r1_kills_program(self, policy):
        from holosoma_inference.inputs.joystick import JoystickOtherInput

        prov = JoystickOtherInput(policy)
        with pytest.raises(SystemExit):
            prov.handle_joystick_button("L1+R1")

    def test_unknown_button_returns_false(self, policy):
        from holosoma_inference.inputs.joystick import JoystickOtherInput

        prov = JoystickOtherInput(policy)
        assert prov.handle_joystick_button("unknown") is False

    def test_poll_shared_edge_detection(self, policy):
        """When shared with velocity provider, detects rising edges from cached state."""
        from holosoma_inference.inputs.joystick import JoystickOtherInput, JoystickVelocityInput

        vel = JoystickVelocityInput(policy)
        vel.key_states = {"A": True}
        vel.last_key_states = {"A": False}

        prov = JoystickOtherInput(policy)
        prov._shared_velocity = vel
        prov.poll()

        # A was pressed (rising edge) -> should dispatch
        policy.handle_joystick_button.assert_called_once_with("A")

    def test_poll_shared_no_dispatch_on_hold(self, policy):
        """No dispatch when button was already held."""
        from holosoma_inference.inputs.joystick import JoystickOtherInput, JoystickVelocityInput

        vel = JoystickVelocityInput(policy)
        vel.key_states = {"A": True}
        vel.last_key_states = {"A": True}

        prov = JoystickOtherInput(policy)
        prov._shared_velocity = vel
        prov.poll()

        policy.handle_joystick_button.assert_not_called()

    def test_poll_standalone_reads_buttons(self, policy):
        """When not shared, reads buttons directly from SDK."""
        from holosoma_inference.inputs.joystick import JoystickOtherInput

        policy.interface.get_joystick_msg.return_value = "msg"
        policy.interface.get_joystick_key.return_value = "B"

        prov = JoystickOtherInput(policy)
        prov.poll()  # First poll: B goes True (rising edge)

        policy.handle_joystick_button.assert_called_once_with("B")

    def test_poll_standalone_skips_when_no_msg(self, policy):
        from holosoma_inference.inputs.joystick import JoystickOtherInput

        policy.interface.get_joystick_msg.return_value = None
        prov = JoystickOtherInput(policy)
        prov.poll()
        policy.handle_joystick_button.assert_not_called()


class TestLocomotionJoystickOtherInput:
    def test_stand_command(self, policy):
        from holosoma_inference.inputs.joystick import LocomotionJoystickOtherInput

        prov = LocomotionJoystickOtherInput(policy)
        assert prov.handle_joystick_button("start") is True
        policy._handle_stand_command.assert_called_once()

    def test_zero_velocity(self, policy):
        from holosoma_inference.inputs.joystick import LocomotionJoystickOtherInput

        prov = LocomotionJoystickOtherInput(policy)
        assert prov.handle_joystick_button("L2") is True
        policy._handle_zero_velocity.assert_called_once()

    def test_falls_through_to_base(self, policy):
        from holosoma_inference.inputs.joystick import LocomotionJoystickOtherInput

        prov = LocomotionJoystickOtherInput(policy)
        assert prov.handle_joystick_button("A") is True
        policy._handle_start_policy.assert_called_once()


class TestWbtJoystickOtherInput:
    def test_start_motion_clip(self, policy):
        from holosoma_inference.inputs.joystick import WbtJoystickOtherInput

        prov = WbtJoystickOtherInput(policy)
        assert prov.handle_joystick_button("start") is True
        policy._handle_start_motion_clip.assert_called_once()

    def test_falls_through_to_base(self, policy):
        from holosoma_inference.inputs.joystick import WbtJoystickOtherInput

        prov = WbtJoystickOtherInput(policy)
        assert prov.handle_joystick_button("B") is True
        policy._handle_stop_policy.assert_called_once()


class TestSharedJoystickWiring:
    def test_shared_velocity_none_by_default(self, policy):
        from holosoma_inference.inputs.joystick import JoystickOtherInput

        other = JoystickOtherInput(policy)
        assert other._shared_velocity is None
