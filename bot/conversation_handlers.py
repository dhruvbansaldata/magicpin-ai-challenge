"""
Multi-Turn Conversation Handler — magicpin AI Challenge Submission (challenge-brief.md §7.4)
Provides `respond(state, merchant_message)` for multi-turn evaluation and replay testing.
"""

from llm_client import LLMClient
from reply_engine import ConversationState, ReplyEngine

__all__ = ["ConversationState", "respond"]

_engine = ReplyEngine(LLMClient())


def respond(state: ConversationState, merchant_message: str) -> dict:
    """
    Given the conversation state so far + the merchant's latest message, produce the reply.
    Handles:
    - Auto-reply detection (action="wait")
    - Intent transition ("let's do it" -> immediate action step without repeating pitches)
    - Hostile / opt-out handling (action="end" + graceful exit)
    - Off-topic / question redirection
    """
    turn_number = len(state.turns) + 1
    return _engine.handle_reply(
        state=state,
        message=merchant_message,
        from_role="merchant",
        turn_number=turn_number,
    )
