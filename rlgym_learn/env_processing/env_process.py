from __future__ import annotations

import random
import socket
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from typing import Dict, Optional

import numpy as np
from rlgym.api import (
    ActionSpaceType,
    ActionType,
    AgentID,
    EngineActionType,
    ObsSpaceType,
    ObsType,
    RewardType,
    RLGym,
    StateType,
)

from ..api import StateMetrics
from ..rlgym_learn import PickleablePyAnySerdeType
from ..rlgym_learn import env_process as rust_env_process
from ..rlgym_learn import recvfrom_byte_py, sendto_byte_py


@dataclass
class PickleableSerdeTypeConfig:
    agent_id_serde_type: PickleablePyAnySerdeType
    action_serde_type: PickleablePyAnySerdeType
    obs_serde_type: PickleablePyAnySerdeType
    reward_serde_type: PickleablePyAnySerdeType
    obs_space_serde_type: PickleablePyAnySerdeType
    action_space_serde_type: PickleablePyAnySerdeType
    state_serde_type: PickleablePyAnySerdeType
    state_metrics_serde_type: PickleablePyAnySerdeType


def env_process(
    proc_id: str,
    parent_sockname,
    build_env_fn: Callable[
        [],
        RLGym[
            AgentID,
            ObsType,
            ActionType,
            EngineActionType,
            RewardType,
            StateType,
            ObsSpaceType,
            ActionSpaceType,
        ],
    ],
    serde_type_config: PickleableSerdeTypeConfig,
    collect_state_metrics_fn: Optional[
        Callable[[StateType, Dict[AgentID, RewardType]], StateMetrics]
    ],
    send_state_to_agent_controllers: bool,
    flinks_folder: str,
    shm_buffer_size: int,
    seed: int,
    render_this_proc: bool,
    render_delay: Optional[float],
    recalculate_agent_id_every_step: bool,
):
    child_end = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    child_end.bind(("127.0.0.1", 0))

    random.seed(seed)
    np.random.seed(seed)

    sendto_byte_py(child_end, parent_sockname)
    recvfrom_byte_py(child_end)

    rust_env_process(
        proc_id,
        child_end,
        parent_sockname,
        build_env_fn,
        flinks_folder,
        shm_buffer_size,
        serde_type_config.agent_id_serde_type,
        serde_type_config.action_serde_type,
        serde_type_config.obs_serde_type,
        serde_type_config.reward_serde_type,
        serde_type_config.obs_space_serde_type,
        serde_type_config.action_space_serde_type,
        serde_type_config.state_serde_type,
        serde_type_config.state_metrics_serde_type,
        collect_state_metrics_fn,
        send_state_to_agent_controllers,
        render_this_proc,
        timedelta(seconds=render_delay),
        recalculate_agent_id_every_step,
    )
