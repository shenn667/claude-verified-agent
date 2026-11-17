"""claude-verified-agent: end-to-end verified agent over 3 local pillars."""

__version__ = "0.1.0"

from .agent import AgentConfig, VerifiedAgent, ask  # noqa: F401
from .gates import run_gate  # noqa: F401
