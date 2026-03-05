#!/bin/bash
# Source this file to activate the hsmujoco_py312 conda env (Python 3.12 + ROS2 Jazzy).
# Usage:  source holosoma/scripts/source_mujoco_py312_setup.sh

# Detect script directory (works in both bash and zsh)
if [ -n "${BASH_SOURCE[0]}" ]; then
    SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
elif [ -n "${ZSH_VERSION}" ]; then
    SCRIPT_DIR=$( cd -- "$( dirname -- "${(%):-%x}" )" &> /dev/null && pwd )
fi

CONDA_ENV_NAME=hsmujoco_py312

source ${SCRIPT_DIR}/source_common.sh

# Source ROS2 Jazzy first (provides rclpy for Python 3.12)
if [ -f /opt/ros/jazzy/setup.bash ]; then
    source /opt/ros/jazzy/setup.bash
    echo "ROS2 Jazzy sourced"
else
    echo "Warning: /opt/ros/jazzy/setup.bash not found — bridge imports will fail"
fi

source ${CONDA_ROOT}/bin/activate $CONDA_ENV_NAME

export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${CONDA_ROOT}/envs/$CONDA_ENV_NAME/lib

# Validate
if python -c "import mujoco" 2>/dev/null; then
    echo "✅ $CONDA_ENV_NAME activated (Python $(python --version 2>&1 | cut -d' ' -f2))"
    echo "   MuJoCo $(python -c 'import mujoco; print(mujoco.__version__)')"
    echo "   PyTorch $(python -c 'import torch; print(torch.__version__)')"
    python -c "import rclpy; print('   rclpy OK')" 2>/dev/null || echo "   ⚠ rclpy not available"
else
    echo "Warning: MuJoCo environment activation may have issues"
fi
