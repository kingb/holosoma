"""Tests for DualMode X/x switching."""

from .conftest import _make_dual, skip_dual_mode


@skip_dual_mode
class TestDualModeSwitching:
    def test_x_keyboard_triggers_switch(self):
        dual = _make_dual()
        assert dual.active is dual.primary
        dual.primary.handle_keyboard_button("x")
        assert dual.active is dual.secondary
        assert dual.active_label == "secondary"

    def test_x_joystick_triggers_switch(self):
        dual = _make_dual()
        dual.primary.handle_joystick_button("X")
        assert dual.active is dual.secondary

    def test_double_switch_returns_to_primary(self):
        dual = _make_dual()
        dual.primary.handle_keyboard_button("x")
        dual.secondary.handle_keyboard_button("x")
        assert dual.active is dual.primary
        assert dual.active_label == "primary"

    def test_non_switch_keyboard_delegates_to_active(self):
        dual = _make_dual()
        orig_primary_kb = dual._orig_kb[id(dual.primary)]
        dual.primary.handle_keyboard_button("]")
        orig_primary_kb.assert_called_once_with("]")

    def test_non_switch_joystick_delegates_to_active(self):
        dual = _make_dual()
        orig_primary_joy = dual._orig_joy[id(dual.primary)]
        dual.primary.handle_joystick_button("A")
        orig_primary_joy.assert_called_once_with("A")

    def test_delegates_to_secondary_after_switch(self):
        dual = _make_dual()
        dual.primary.handle_keyboard_button("x")  # switch to secondary
        orig_secondary_kb = dual._orig_kb[id(dual.secondary)]
        dual.secondary.handle_keyboard_button("]")
        orig_secondary_kb.assert_called_once_with("]")

    def test_switch_stops_old_and_starts_new(self):
        dual = _make_dual()
        dual.primary.handle_keyboard_button("x")
        dual.primary._handle_stop_policy.assert_called_once()
        dual.secondary._resolve_control_gains.assert_called_once()
        dual.secondary._init_phase_components.assert_called_once()
        dual.secondary._handle_start_policy.assert_called_once()

    def test_joystick_state_carry_over(self):
        from holosoma_inference.inputs.joystick import JoystickVelocityInput

        dual = _make_dual()
        # Replace mock velocity inputs with real JoystickVelocityInput
        pri_vel = JoystickVelocityInput(dual.primary)
        pri_vel.key_states = {"X": True, "A": False}
        sec_vel = JoystickVelocityInput(dual.secondary)

        dual.primary._velocity_input = pri_vel
        dual.secondary._velocity_input = sec_vel

        dual.primary.handle_keyboard_button("x")

        assert sec_vel.key_states == {"X": True, "A": False}
        assert sec_vel.last_key_states == {"X": True, "A": False}
