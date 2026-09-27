"""
Multi-turn reply engine for the magicpin AI challenge bot.

Handles:
  - Auto-reply detection (WhatsApp Business canned replies)
  - Intent transitions (merchant commits → switch to action mode)
  - Hostile / opt-out handling
  - Off-topic redirection
  - Normal engaged conversation via LLM
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

from llm_client import LLMClient
from prompts import build_reply_prompt

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────
# Conversation State
# ─────────────────────────────────────────────────────────────────────

@dataclass
class ConversationState:
    conversation_id: str
    merchant_id: str
    customer_id: Optional[str] = None
    trigger_id: str = ""
    trigger_kind: str = ""
    category_slug: str = ""
    turns: list = field(default_factory=list)
    auto_reply_count: int = 0
    last_merchant_message: str = ""
    repeat_count: int = 0
    merchant_committed: bool = False
    ended: bool = False
    initial_body: str = ""


# ─────────────────────────────────────────────────────────────────────
# Signal dictionaries
# ─────────────────────────────────────────────────────────────────────

AUTO_REPLY_SIGNALS = [
    "thank you for contacting",
    "our team will respond",
    "automated assistant",
    "auto-reply",
    "we will get back to you",
    "your message is important",
    "aapki jaankari ke liye",
    "hamari team tak pahuncha",
    "will respond shortly",
    "automated response",
    "this is an auto",
    "bahut-bahut shukriya",
    "main ek automated",
    "yeh ek automated",
]

COMMITMENT_SIGNALS = [
    "let's do it", "lets do it", "ok go ahead", "go ahead",
    "yes please", "yes do it", "sure", "proceed", "haan",
    "kar do", "haan chalega", "let's go", "do it", "start karo",
    "what's next", "whats next", "ok done", "chalega",
    "karo", "theek hai", "thik hai", "ban jayega",
    "yes that would be helpful", "yes i want",
    "ok let's", "ok lets",
]

HOSTILE_SIGNALS = [
    "stop messaging", "stop sending", "spam", "useless",
    "don't message", "not interested", "block", "report",
    "bothering", "harassing", "band karo", "mat bhejo",
    "pareshan", "bakwas", "waste",
]

OFF_TOPIC_SIGNALS = [
    "gst", "tax", "filing", "passport", "insurance",
    "loan", "emi", "aadhar", "pan card", "income tax",
    "electricity bill", "water bill", "school admission",
]


# ─────────────────────────────────────────────────────────────────────
# Reply Engine
# ─────────────────────────────────────────────────────────────────────

class ReplyEngine:
    """Processes merchant/customer replies and returns the bot's next action."""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def process_reply(
        self,
        state: ConversationState,
        message: str,
        category: dict | None,
        merchant: dict | None,
        trigger: dict | None,
    ) -> dict:
        """Main entry point. Returns dict with action + body/wait_seconds/rationale."""
        msg_lower = message.lower().strip()

        # Record the turn
        state.turns.append({"from": "merchant", "body": message})

        # ── 1. Auto-reply detection ──────────────────────────────────
        if self._is_auto_reply(msg_lower):
            return self._handle_auto_reply(state)

        # ── 2. Exact repetition detection ────────────────────────────
        if message.strip() == state.last_merchant_message.strip() and message.strip():
            state.repeat_count += 1
            if state.repeat_count >= 2:
                state.ended = True
                return {
                    "action": "end",
                    "rationale": (
                        f"Same message repeated {state.repeat_count + 1} times. "
                        "Likely auto-reply pattern. Closing conversation."
                    ),
                }
        else:
            state.repeat_count = 0

        state.last_merchant_message = message.strip()

        # ── 3. Hostile / opt-out ─────────────────────────────────────
        if self._is_hostile(msg_lower):
            return self._handle_hostile(state)

        # ── 4. Off-topic ─────────────────────────────────────────────
        if self._is_off_topic(msg_lower):
            return self._handle_off_topic(state, msg_lower)

        # ── 5. Commitment / intent transition ────────────────────────
        if self._is_commitment(msg_lower):
            state.merchant_committed = True
            return self._handle_commitment(state, category, merchant, trigger)

        # ── 6. Normal engaged reply via LLM ──────────────────────────
        return self._compose_reply(state, message, category, merchant, trigger)

    # ─────────────────────────────────────────────────────────────────
    # Classifiers
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _is_auto_reply(msg_lower: str) -> bool:
        return any(sig in msg_lower for sig in AUTO_REPLY_SIGNALS)

    @staticmethod
    def _is_hostile(msg_lower: str) -> bool:
        return any(sig in msg_lower for sig in HOSTILE_SIGNALS)

    @staticmethod
    def _is_off_topic(msg_lower: str) -> bool:
        return any(sig in msg_lower for sig in OFF_TOPIC_SIGNALS)

    @staticmethod
    def _is_commitment(msg_lower: str) -> bool:
        return any(sig in msg_lower for sig in COMMITMENT_SIGNALS)

    # ─────────────────────────────────────────────────────────────────
    # Handlers
    # ─────────────────────────────────────────────────────────────────

    def _handle_auto_reply(self, state: ConversationState) -> dict:
        state.auto_reply_count += 1

        if state.auto_reply_count >= 3:
            state.ended = True
            return {
                "action": "end",
                "rationale": (
                    f"Auto-reply detected {state.auto_reply_count}x in a row, "
                    "no real engagement signal. Closing conversation."
                ),
            }
        elif state.auto_reply_count >= 2:
            return {
                "action": "wait",
                "wait_seconds": 86400,
                "rationale": (
                    "Same auto-reply twice in a row — owner not at phone. "
                    "Wait 24h before retry."
                ),
            }
        else:
            body = (
                "Looks like an auto-reply. No rush — when the owner "
                "sees this, just reply 'Yes' to pick up where we left off."
            )
            state.turns.append({"from": "vera", "body": body})
            return {
                "action": "send",
                "body": body,
                "cta": "binary_yes_no",
                "rationale": (
                    "Detected auto-reply (canned phrasing). One explicit "
                    "prompt for the owner to engage when available."
                ),
            }

    def _handle_hostile(self, state: ConversationState) -> dict:
        state.ended = True
        body = (
            "Apologies — I won't message again. If anything changes, "
            "you can always restart with 'Hi Vera'."
        )
        state.turns.append({"from": "vera", "body": body})
        return {
            "action": "send",
            "body": body,
            "cta": "none",
            "rationale": (
                "Merchant frustration/opt-out explicit. One-line acknowledgment "
                "with opt-back-in path. Conversation closes after this send."
            ),
        }

    def _handle_off_topic(self, state: ConversationState, msg_lower: str) -> dict:
        topic = next((sig for sig in OFF_TOPIC_SIGNALS if sig in msg_lower), "that")
        original = state.trigger_kind.replace("_", " ") or "your Google profile"
        body = (
            f"I'll have to leave {topic} to your CA — that's outside what I "
            f"can help with directly. Coming back to {original} — want me "
            "to continue where we left off?"
        )
        state.turns.append({"from": "vera", "body": body})
        return {
            "action": "send",
            "body": body,
            "cta": "open_ended",
            "rationale": (
                f"Out-of-scope ask ({topic}) politely declined. Redirecting "
                f"back to original trigger ({original}) without losing thread."
            ),
        }

    def _handle_commitment(
        self, state: ConversationState,
        category: dict | None, merchant: dict | None, trigger: dict | None,
    ) -> dict:
        """Switch from qualifying to ACTION mode immediately."""
        try:
            prompt = build_reply_prompt(
                state.turns, "MERCHANT_COMMITTED",
                category or {}, merchant or {}, trigger or {},
            )
            result = self.llm.complete_json(prompt)
            if result.get("action") == "send" and result.get("body"):
                state.turns.append({"from": "vera", "body": result["body"]})
                return result
        except Exception as e:
            logger.error(f"LLM commitment reply failed: {e}")

        # Fallback action-mode response
        owner = ""
        if merchant:
            owner = merchant.get("identity", {}).get("owner_first_name", "")

        body = (
            f"Great{', ' + owner if owner else ''}. Proceeding now — "
            "I'll have everything ready in 2 minutes. Stand by."
        )
        state.turns.append({"from": "vera", "body": body})
        return {
            "action": "send",
            "body": body,
            "cta": "none",
            "rationale": (
                "Merchant explicitly committed. Switching from question-asking "
                "to action-execution immediately."
            ),
        }

    def _compose_reply(
        self, state: ConversationState, message: str,
        category: dict | None, merchant: dict | None, trigger: dict | None,
    ) -> dict:
        """Use LLM to compose a contextual reply for normal engaged conversation."""
        try:
            prompt = build_reply_prompt(
                state.turns, message,
                category or {}, merchant or {}, trigger or {},
            )
            result = self.llm.complete_json(prompt)

            action = result.get("action", "send")
            if action in ("send", "wait", "end"):
                if action == "send" and result.get("body"):
                    state.turns.append({"from": "vera", "body": result["body"]})
                if action == "end":
                    state.ended = True
                return result
        except Exception as e:
            logger.error(f"LLM reply composition failed: {e}")

        # Fallback
        body = "Got it, let me work on that. I'll follow up shortly."
        state.turns.append({"from": "vera", "body": body})
        return {
            "action": "send",
            "body": body,
            "cta": "open_ended",
            "rationale": "Acknowledged merchant input. Following up with next steps.",
        }
