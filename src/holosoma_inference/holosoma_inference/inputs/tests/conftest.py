"""Shared fixtures for input-provider tests."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest

from holosoma_inference.config.config_types.task import InputSource  # noqa: F401


def _make_policy(**overrides):
    """Build a minimal mock policy with all attributes providers touch."""
    p = MagicMock()
    p.lin_vel_command = np.array([[0.0, 0.0]])
    p.ang_vel_command = np.array([[0.0]])
    p.stand_command = np.array([[0]])
    p.base_height_command = np.array([[0.5]])
    p.desired_base_height = 0.5
    p.active_policy_index = 0
    p.model_paths = ["a.onnx", "b.onnx"]
    # _try_switch_policy_key returns False by default (MagicMock is truthy)
    p._try_switch_policy_key.return_value = False
    p.config = SimpleNamespace(
        task=SimpleNamespace(
            ros_cmd_vel_topic="cmd_vel",
            ros_other_input_topic="holosoma/other_input",
        )
    )
    for k, v in overrides.items():
        setattr(p, k, v)
    return p


@pytest.fixture
def policy():
    return _make_policy()


def _try_import_policies():
    """Try to import policy modules; skip tests if heavy deps are missing."""
    try:
        from holosoma_inference.policies.base import BasePolicy  # noqa: F401
        from holosoma_inference.policies.locomotion import LocomotionPolicy  # noqa: F401
        from holosoma_inference.policies.wbt import WholeBodyTrackingPolicy  # noqa: F401

        return True
    except (ImportError, ModuleNotFoundError):
        return False


_has_policies = _try_import_policies()
skip_policies = pytest.mark.skipif(not _has_policies, reason="Policy deps not installed")


def _try_import_dual_mode():
    try:
        from holosoma_inference.policies.dual_mode import DualModePolicy  # noqa: F401

        return True
    except (ImportError, ModuleNotFoundError):
        return False


_has_dual_mode = _try_import_dual_mode()
skip_dual_mode = pytest.mark.skipif(not _has_dual_mode, reason="DualMode deps not installed")


def _make_dual():
    """Build a DualModePolicy with mock policies, skipping __init__."""
    from holosoma_inference.policies.dual_mode import DualModePolicy

    dual = object.__new__(DualModePolicy)
    dual.primary = _make_policy()
    dual.secondary = _make_policy()
    dual.active = dual.primary
    dual.active_label = "primary"

    dual.primary._velocity_input = MagicMock()
    dual.secondary._velocity_input = MagicMock()
    dual.primary._other_input = MagicMock()
    dual.secondary._other_input = MagicMock()

    dual._patch_button_handlers()
    return dual
