import numpy as np
import torch
from earl_pytorch import EARLPerceiver, ControlsPredictorDiscrete
from torch import nn
from torch.nn import Linear, Sequential, ReLU

from rocket_learn.agent.actor_critic_agent import ActorCriticAgent
from rocket_learn.agent.discrete_policy import DiscretePolicy


class Necto(nn.Module):  # Wraps earl + an output and takes only a single input
    def __init__(self, earl, output):
        super().__init__()
        self.earl = earl
        self.relu = ReLU()
        self.output = output

    def forward(self, inp):
        q, kv, m = inp
        res, w = self.earl(q, kv, m)
        res = self.output(self.relu(res))
        if isinstance(res, tuple):
            return tuple(r for r in res), w
        return res, w


def get_critic():
    return Necto(EARLPerceiver(128, 1, 4, 1, query_features=32, key_value_features=24),
                 Linear(128, 1))


def get_actor():
    # split = (3, 3, 2, 2, 2)
    split = (90,)
    return DiscretePolicy(Necto(EARLPerceiver(128, 1, 4, 1, query_features=32, key_value_features=24),
                                ControlsPredictorDiscrete(128, splits=split)), split)


def get_agent(actor_lr, critic_lr=None):
    actor = get_actor()
    critic = get_critic()
    optim = torch.optim.Adam([
        {"params": actor.parameters(), "lr": actor_lr},
        {"params": critic.parameters(), "lr": critic_lr if critic_lr is not None else actor_lr}
    ])

    agent = ActorCriticAgent(actor=actor, critic=critic, optimizer=optim)
    return agent
