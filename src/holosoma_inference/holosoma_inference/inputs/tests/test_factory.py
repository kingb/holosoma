"""Tests for factory methods and integration wiring."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from holosoma_inference.config.config_types.task import InputSource

from .conftest import skip_policies


@skip_policies
class TestBasePolicyFactory:
    """Test BasePolicy._create_velocity_input and _create_other_input."""

    def _make_base(self):
        from holosoma_inference.policies.base import BasePolicy

        return BasePolicy.__new__(BasePolicy)

    def test_keyboard_velocity(self):
        from holosoma_inference.inputs.keyboard import KeyboardVelocityInput

        bp = self._make_base()
        result = bp._create_velocity_input(InputSource.keyboard)
        assert isinstance(result, KeyboardVelocityInput)

    def test_joystick_velocity(self):
        from holosoma_inference.inputs.joystick import JoystickVelocityInput

        bp = self._make_base()
        result = bp._create_velocity_input(InputSource.joystick)
        assert isinstance(result, JoystickVelocityInput)

    def test_ros2_velocity(self):
        from holosoma_inference.inputs.ros2 import Ros2VelocityInput

        bp = self._make_base()
        result = bp._create_velocity_input(InputSource.ros2)
        assert isinstance(result, Ros2VelocityInput)

    def test_keyboard_other(self):
        from holosoma_inference.inputs.keyboard import KeyboardOtherInput

        bp = self._make_base()
        result = bp._create_other_input(InputSource.keyboard)
        assert isinstance(result, KeyboardOtherInput)

    def test_joystick_other(self):
        from holosoma_inference.inputs.joystick import JoystickOtherInput

        bp = self._make_base()
        result = bp._create_other_input(InputSource.joystick)
        assert isinstance(result, JoystickOtherInput)

    def test_ros2_other(self):
        from holosoma_inference.inputs.ros2 import Ros2OtherInput

        bp = self._make_base()
        result = bp._create_other_input(InputSource.ros2)
        assert isinstance(result, Ros2OtherInput)

    def test_unknown_source_raises(self):
        bp = self._make_base()
        with pytest.raises(ValueError, match="Unknown velocity"):
            bp._create_velocity_input("invalid")
        with pytest.raises(ValueError, match="Unknown other"):
            bp._create_other_input("invalid")


@skip_policies
class TestLocomotionPolicyFactory:
    """Test LocomotionPolicy overrides for keyboard/joystick providers."""

    def _make_loco(self):
        from holosoma_inference.policies.locomotion import LocomotionPolicy

        return LocomotionPolicy.__new__(LocomotionPolicy)

    def test_keyboard_velocity_is_locomotion(self):
        from holosoma_inference.inputs.keyboard import LocomotionKeyboardVelocityInput

        lp = self._make_loco()
        result = lp._create_velocity_input(InputSource.keyboard)
        assert isinstance(result, LocomotionKeyboardVelocityInput)

    def test_keyboard_other_is_locomotion(self):
        from holosoma_inference.inputs.keyboard import LocomotionKeyboardOtherInput

        lp = self._make_loco()
        result = lp._create_other_input(InputSource.keyboard)
        assert isinstance(result, LocomotionKeyboardOtherInput)

    def test_joystick_other_is_locomotion(self):
        from holosoma_inference.inputs.joystick import LocomotionJoystickOtherInput

        lp = self._make_loco()
        result = lp._create_other_input(InputSource.joystick)
        assert isinstance(result, LocomotionJoystickOtherInput)

    def test_joystick_velocity_falls_to_base(self):
        from holosoma_inference.inputs.joystick import JoystickVelocityInput

        lp = self._make_loco()
        result = lp._create_velocity_input(InputSource.joystick)
        assert type(result) is JoystickVelocityInput

    def test_ros2_falls_to_base(self):
        from holosoma_inference.inputs.ros2 import Ros2OtherInput, Ros2VelocityInput

        lp = self._make_loco()
        assert isinstance(lp._create_velocity_input(InputSource.ros2), Ros2VelocityInput)
        assert isinstance(lp._create_other_input(InputSource.ros2), Ros2OtherInput)


@skip_policies
class TestWbtPolicyFactory:
    """Test WholeBodyTrackingPolicy overrides for keyboard/joystick providers."""

    def _make_wbt(self):
        from holosoma_inference.policies.wbt import WholeBodyTrackingPolicy

        return WholeBodyTrackingPolicy.__new__(WholeBodyTrackingPolicy)

    def test_keyboard_other_is_wbt(self):
        from holosoma_inference.inputs.keyboard import WbtKeyboardOtherInput

        wp = self._make_wbt()
        result = wp._create_other_input(InputSource.keyboard)
        assert isinstance(result, WbtKeyboardOtherInput)

    def test_joystick_other_is_wbt(self):
        from holosoma_inference.inputs.joystick import WbtJoystickOtherInput

        wp = self._make_wbt()
        result = wp._create_other_input(InputSource.joystick)
        assert isinstance(result, WbtJoystickOtherInput)

    def test_keyboard_velocity_falls_to_base(self):
        from holosoma_inference.inputs.keyboard import KeyboardVelocityInput

        wp = self._make_wbt()
        result = wp._create_velocity_input(InputSource.keyboard)
        assert type(result) is KeyboardVelocityInput

    def test_ros2_falls_to_base(self):
        from holosoma_inference.inputs.ros2 import Ros2OtherInput, Ros2VelocityInput

        wp = self._make_wbt()
        assert isinstance(wp._create_velocity_input(InputSource.ros2), Ros2VelocityInput)
        assert isinstance(wp._create_other_input(InputSource.ros2), Ros2OtherInput)


class TestChannelSeparation:
    """When velocity_input=ros2, keyboard WASD must NOT affect velocity."""

    def test_base_keyboard_velocity_ignores_wasd(self, policy):
        from holosoma_inference.inputs.keyboard import KeyboardVelocityInput

        prov = KeyboardVelocityInput(policy)
        for key in ("w", "a", "s", "d", "q", "e", "z"):
            assert prov.handle_key(key) is False
        policy._handle_velocity_control.assert_not_called()

    def test_locomotion_velocity_does_not_leak_to_other(self, policy):
        """LocomotionKeyboardOtherInput does NOT handle WASD."""
        from holosoma_inference.inputs.keyboard import LocomotionKeyboardOtherInput

        policy._try_switch_policy_key.return_value = False
        prov = LocomotionKeyboardOtherInput(policy)
        for key in ("w", "a", "s", "d", "q", "e", "z"):
            assert prov.handle_key(key) is False


@skip_policies
class TestKeyboardDispatchPriority:
    """handle_keyboard_button tries velocity first; skips other if handled."""

    def _make_dispatch_policy(self):
        from holosoma_inference.policies.base import BasePolicy

        bp = BasePolicy.__new__(BasePolicy)
        bp._velocity_input = MagicMock()
        bp._other_input = MagicMock()
        bp._print_control_status = MagicMock()
        return bp

    def test_velocity_handled_skips_other(self):
        bp = self._make_dispatch_policy()
        bp._velocity_input.handle_key.return_value = True

        bp.handle_keyboard_button("w")

        bp._velocity_input.handle_key.assert_called_once_with("w")
        bp._other_input.handle_key.assert_not_called()

    def test_velocity_declined_passes_to_other(self):
        bp = self._make_dispatch_policy()
        bp._velocity_input.handle_key.return_value = False

        bp.handle_keyboard_button("]")

        bp._velocity_input.handle_key.assert_called_once_with("]")
        bp._other_input.handle_key.assert_called_once_with("]")


@skip_policies
class TestCreateInputProvidersIntegration:
    """Test the wiring logic in _create_input_providers."""

    def test_shared_joystick_wiring(self):
        """When both channels are joystick, _shared_velocity is wired."""
        from holosoma_inference.inputs.joystick import JoystickOtherInput, JoystickVelocityInput
        from holosoma_inference.policies.base import BasePolicy

        bp = BasePolicy.__new__(BasePolicy)
        bp.config = SimpleNamespace(
            task=SimpleNamespace(velocity_input=InputSource.joystick, other_input=InputSource.joystick)
        )
        bp.use_joystick = True
        bp._create_input_providers()

        assert isinstance(bp._velocity_input, JoystickVelocityInput)
        assert isinstance(bp._other_input, JoystickOtherInput)
        assert bp._other_input._shared_velocity is bp._velocity_input

    def test_no_shared_wiring_for_mixed_sources(self, monkeypatch):
        """When velocity is keyboard and other is joystick, no shared wiring."""
        from holosoma_inference.inputs.joystick import JoystickOtherInput
        from holosoma_inference.inputs.keyboard import KeyboardVelocityInput
        from holosoma_inference.policies.base import BasePolicy

        monkeypatch.setattr("sys.stdin.isatty", lambda: False)

        bp = BasePolicy.__new__(BasePolicy)
        bp.config = SimpleNamespace(
            task=SimpleNamespace(velocity_input=InputSource.keyboard, other_input=InputSource.joystick)
        )
        bp.use_joystick = True
        bp.logger = MagicMock()
        bp.use_keyboard = False
        bp.use_policy_action = False
        bp._create_input_providers()

        assert isinstance(bp._velocity_input, KeyboardVelocityInput)
        assert isinstance(bp._other_input, JoystickOtherInput)
        assert bp._other_input._shared_velocity is None

    def test_joystick_falls_back_to_keyboard_when_unavailable(self, monkeypatch):
        """When use_joystick is False, joystick sources fall back to keyboard."""
        from holosoma_inference.inputs.keyboard import KeyboardOtherInput, KeyboardVelocityInput
        from holosoma_inference.policies.base import BasePolicy

        monkeypatch.setattr("sys.stdin.isatty", lambda: False)

        bp = BasePolicy.__new__(BasePolicy)
        bp.config = SimpleNamespace(
            task=SimpleNamespace(velocity_input=InputSource.joystick, other_input=InputSource.joystick)
        )
        bp.use_joystick = False
        bp.logger = MagicMock()
        bp.use_keyboard = False
        bp.use_policy_action = False
        bp._create_input_providers()

        assert isinstance(bp._velocity_input, KeyboardVelocityInput)
        assert isinstance(bp._other_input, KeyboardOtherInput)
