"""Keyboard input providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from holosoma_inference.inputs.base import OtherInput, VelocityInput

if TYPE_CHECKING:
    from holosoma_inference.policies.base import BasePolicy


class KeyboardVelocityInput(VelocityInput):
    """Base keyboard velocity — no keys handled.

    Subclass for policy-specific velocity keys (e.g. WASD for locomotion).
    """

    def start(self) -> None:
        pass  # Keyboard listener managed by policy


class KeyboardOtherInput(OtherInput):
    """Keyboard handler for common discrete commands.

    Keys: ] (start), o (stop), i (init), v/b/f/g/r (kp tuning), 1-9 (switch policy).
    """

    def start(self) -> None:
        pass  # Keyboard listener managed by policy

    def handle_key(self, keycode: str) -> bool:
        if self.policy._try_switch_policy_key(keycode):
            return True
        if keycode == "]":
            self.policy._handle_start_policy()
            return True
        if keycode == "o":
            self.policy._handle_stop_policy()
            return True
        if keycode == "i":
            self.policy._handle_init_state()
            return True
        if keycode in ("v", "b", "f", "g", "r"):
            self.policy._handle_kp_control(keycode)
            return True
        return False


# ---------------------------------------------------------------------------
# Locomotion-specific
# ---------------------------------------------------------------------------


class LocomotionKeyboardVelocityInput(KeyboardVelocityInput):
    """Locomotion velocity keys: W/A/S/D (linear), Q/E (angular), Z (zero)."""

    def handle_key(self, keycode: str) -> bool:
        if keycode in ("w", "s", "a", "d"):
            self.policy._handle_velocity_control(keycode)
            return True
        if keycode in ("q", "e"):
            self.policy._handle_angular_velocity_control(keycode)
            return True
        if keycode == "z":
            self.policy._handle_zero_velocity()
            return True
        return False


class LocomotionKeyboardOtherInput(KeyboardOtherInput):
    """Adds stand/walk toggle (=) to base keyboard commands."""

    def handle_key(self, keycode: str) -> bool:
        if keycode == "=":
            self.policy._handle_stand_command()
            return True
        return super().handle_key(keycode)


# ---------------------------------------------------------------------------
# WBT-specific
# ---------------------------------------------------------------------------


class WbtKeyboardOtherInput(KeyboardOtherInput):
    """Adds motion clip start (s) to base keyboard commands."""

    def handle_key(self, keycode: str) -> bool:
        if keycode == "s":
            self.policy._handle_start_motion_clip()
            return True
        return super().handle_key(keycode)
