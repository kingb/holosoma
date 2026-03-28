"""Tests for keyboard input providers."""

from types import SimpleNamespace

import pytest

from .conftest import _make_policy


class TestKeyboardListener:
    def test_start_is_idempotent(self, policy):
        from holosoma_inference.inputs.keyboard import KeyboardListener

        # Remove _shared_hardware_source so listener doesn't skip
        del policy._shared_hardware_source
        listener = KeyboardListener(policy)
        listener.start()
        listener.start()  # second call should be a no-op
        assert listener._started is True

    def test_skips_thread_in_non_tty(self, policy, monkeypatch):
        from holosoma_inference.inputs.keyboard import KeyboardListener

        del policy._shared_hardware_source
        monkeypatch.setattr("sys.stdin.isatty", lambda: False)
        policy.use_keyboard = True
        policy.use_policy_action = False

        listener = KeyboardListener(policy)
        listener.start()

        assert policy.use_keyboard is False
        assert policy.use_policy_action is True

    def test_ensure_skips_shared_hardware(self):
        """When _shared_hardware_source exists, no KeyboardListener is created."""
        from holosoma_inference.inputs.keyboard import _ensure_keyboard_listener

        p = SimpleNamespace(_shared_hardware_source=True)
        _ensure_keyboard_listener(p)
        assert not hasattr(p, "_keyboard_listener")

    def test_ensure_creates_and_shares_listener(self, monkeypatch):
        from holosoma_inference.inputs.keyboard import KeyboardListener, _ensure_keyboard_listener

        p = _make_policy()
        # Remove auto-created attributes from MagicMock
        del p._shared_hardware_source
        del p._keyboard_listener
        monkeypatch.setattr("sys.stdin.isatty", lambda: False)

        _ensure_keyboard_listener(p)
        assert isinstance(p._keyboard_listener, KeyboardListener)

        # Second call reuses the same listener
        first = p._keyboard_listener
        _ensure_keyboard_listener(p)
        assert p._keyboard_listener is first

    def test_provider_start_calls_ensure(self, monkeypatch):
        from holosoma_inference.inputs.keyboard import (
            KeyboardListener,
            KeyboardOtherInput,
            KeyboardVelocityInput,
        )

        p = _make_policy()
        del p._shared_hardware_source
        del p._keyboard_listener
        monkeypatch.setattr("sys.stdin.isatty", lambda: False)

        vel = KeyboardVelocityInput(p)
        other = KeyboardOtherInput(p)
        vel.start()
        other.start()

        assert isinstance(p._keyboard_listener, KeyboardListener)
        assert p._keyboard_listener._started is True


class TestKeyboardVelocityInput:
    def test_base_returns_false_for_all_keys(self, policy):
        from holosoma_inference.inputs.keyboard import KeyboardVelocityInput

        prov = KeyboardVelocityInput(policy)
        prov.start()
        assert prov.handle_key("w") is False
        assert prov.handle_key("]") is False


class TestKeyboardOtherInput:
    def test_start_policy(self, policy):
        from holosoma_inference.inputs.keyboard import KeyboardOtherInput

        prov = KeyboardOtherInput(policy)
        assert prov.handle_key("]") is True
        policy._handle_start_policy.assert_called_once()

    def test_stop_policy(self, policy):
        from holosoma_inference.inputs.keyboard import KeyboardOtherInput

        prov = KeyboardOtherInput(policy)
        assert prov.handle_key("o") is True
        policy._handle_stop_policy.assert_called_once()

    def test_init_state(self, policy):
        from holosoma_inference.inputs.keyboard import KeyboardOtherInput

        prov = KeyboardOtherInput(policy)
        assert prov.handle_key("i") is True
        policy._handle_init_state.assert_called_once()

    @pytest.mark.parametrize("key", ["v", "b", "f", "g", "r"])
    def test_kp_control(self, policy, key):
        from holosoma_inference.inputs.keyboard import KeyboardOtherInput

        prov = KeyboardOtherInput(policy)
        assert prov.handle_key(key) is True
        policy._handle_kp_control.assert_called_once_with(key)

    def test_switch_policy_key(self, policy):
        from holosoma_inference.inputs.keyboard import KeyboardOtherInput

        policy._try_switch_policy_key.return_value = True
        prov = KeyboardOtherInput(policy)
        assert prov.handle_key("2") is True
        policy._try_switch_policy_key.assert_called_once_with("2")

    def test_unhandled_key_returns_false(self, policy):
        from holosoma_inference.inputs.keyboard import KeyboardOtherInput

        policy._try_switch_policy_key.return_value = False
        prov = KeyboardOtherInput(policy)
        assert prov.handle_key("x") is False


class TestLocomotionKeyboardVelocityInput:
    @pytest.mark.parametrize("key", ["w", "s", "a", "d"])
    def test_wasd_handled(self, policy, key):
        from holosoma_inference.inputs.keyboard import LocomotionKeyboardVelocityInput

        prov = LocomotionKeyboardVelocityInput(policy)
        assert prov.handle_key(key) is True
        policy._handle_velocity_control.assert_called_once_with(key)

    @pytest.mark.parametrize("key", ["q", "e"])
    def test_angular_velocity(self, policy, key):
        from holosoma_inference.inputs.keyboard import LocomotionKeyboardVelocityInput

        prov = LocomotionKeyboardVelocityInput(policy)
        assert prov.handle_key(key) is True
        policy._handle_angular_velocity_control.assert_called_once_with(key)

    def test_zero_velocity(self, policy):
        from holosoma_inference.inputs.keyboard import LocomotionKeyboardVelocityInput

        prov = LocomotionKeyboardVelocityInput(policy)
        assert prov.handle_key("z") is True
        policy._handle_zero_velocity.assert_called_once()

    def test_unhandled_key(self, policy):
        from holosoma_inference.inputs.keyboard import LocomotionKeyboardVelocityInput

        prov = LocomotionKeyboardVelocityInput(policy)
        assert prov.handle_key("]") is False


class TestLocomotionKeyboardOtherInput:
    def test_stand_command(self, policy):
        from holosoma_inference.inputs.keyboard import LocomotionKeyboardOtherInput

        prov = LocomotionKeyboardOtherInput(policy)
        assert prov.handle_key("=") is True
        policy._handle_stand_command.assert_called_once()

    def test_falls_through_to_base(self, policy):
        from holosoma_inference.inputs.keyboard import LocomotionKeyboardOtherInput

        prov = LocomotionKeyboardOtherInput(policy)
        assert prov.handle_key("]") is True
        policy._handle_start_policy.assert_called_once()


class TestWbtKeyboardOtherInput:
    def test_start_motion_clip(self, policy):
        from holosoma_inference.inputs.keyboard import WbtKeyboardOtherInput

        prov = WbtKeyboardOtherInput(policy)
        assert prov.handle_key("s") is True
        policy._handle_start_motion_clip.assert_called_once()

    def test_falls_through_to_base(self, policy):
        from holosoma_inference.inputs.keyboard import WbtKeyboardOtherInput

        prov = WbtKeyboardOtherInput(policy)
        assert prov.handle_key("o") is True
        policy._handle_stop_policy.assert_called_once()
