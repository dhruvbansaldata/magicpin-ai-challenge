"""
prompts.py — All prompt templates for the magicpin AI challenge bot.

Each trigger.kind gets a specialized prompt framing.
The build functions serialize real JSON context data into the prompt.
"""

import json
from typing import Any, Optional

# ─────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT — injected as the system message on every LLM call
# ─────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are Vera, magicpin's elite AI assistant for Indian local merchants on WhatsApp.

CRITICAL JUDGE REQUIREMENTS (If you fail any, you lose points):
1. SPECIFICITY (10/10): You MUST include at least 3 precise data points from the context (exact percentages, exact ₹ amounts, exact dates, circular numbers, patient counts, or page numbers). Do not be vague. 
2. DECISION QUALITY (10/10): The very first sentence MUST explicitly state the triggering event (e.g., "Meera, reaching out today because [Trigger Event]...").
3. MERCHANT FIT (10/10): Explicitly reference their specific business metrics, competitors, or history provided in the context. Make it impossible for this message to belong to another merchant.
4. CATEGORY FIT (10/10): You MUST use the domain vocabulary of their specific category (e.g., "consultation", "patient" for dentists; "reps", "hypertrophy" for gyms). Match their exact category tone. NEVER use taboo words.
5. ENGAGEMENT (10/10): End with exactly ONE low-friction call-to-action (a simple Yes/No, or a single time slot). Create urgency or curiosity.

RULES:
- Start with the owner/merchant first name.
- If customer/merchant language_pref includes "hi", use natural Hinglish.
- WhatsApp format. Short paragraphs. No fluff. No "I hope you're doing well".
- NEVER invent data. If you need a number, extract it from the context JSON.

OUTPUT FORMAT — respond with ONLY this JSON, no markdown fences:
{
  "body": "the WhatsApp message text",
  "cta": "open_ended|binary_yes_no|binary_confirm_cancel|multi_choice_slot|none",
  "send_as": "vera|merchant_on_behalf",
  "template_name": "vera_<trigger_kind>_v1",
  "template_params": ["param1", "param2", "param3"],
  "suppression_key": "<from the trigger>",
  "rationale": "Explanation of why this meets the 5 criteria perfectly."
}"""


# ─────────────────────────────────────────────────────────────────────
# TRIGGER-SPECIFIC PROMPT FRAMINGS
# ─────────────────────────────────────────────────────────────────────

TRIGGER_PROMPTS: dict[str, str] = {
    "research_digest": (
        "TASK: Share a research digest item with the merchant. "
        "Frame it with source citation (journal, page number), trial size, "
        "and patient/customer segment. Show how this affects THEIR practice "
        "specifically. Offer to pull the abstract + draft a patient-ed post they can share."
    ),
    "regulation_change": (
        "TASK: Alert the merchant about a regulation or compliance change. "
        "Include the circular/notification number, exact deadline date, and "
        "what they must audit or change before the deadline. Offer to help start the process."
    ),
    "perf_dip": (
        "TASK: Address a performance dip. State the exact dip % upfront. "
        "Diagnose the likely cause (don't let them panic). Suggest one specific, "
        "immediate action to reverse the trend."
    ),
    "perf_spike": (
        "TASK: Celebrate a performance spike. State the spike %. Identify the "
        "likely driver. Suggest how to ride the wave and sustain the momentum."
    ),
    "seasonal_perf_dip": (
        "TASK: Reframe an expected seasonal dip as normal. Show the typical range "
        "for this season. Suggest saving budget for the high-conversion period ahead. "
        "Propose a retention-focused action for the current dip."
    ),
    "recall_due": (
        "TASK: Draft a CUSTOMER-FACING recall/appointment reminder. "
        "Offer 2 specific time slots, mention the price, include a complimentary add-on. "
        "Use Hinglish if customer's language_pref includes 'hi'. "
        "Set send_as to 'merchant_on_behalf'."
    ),
    "customer_lapsed_hard": (
        "TASK: Draft a CUSTOMER-FACING winback for a long-lapsed customer. "
        "State duration since last visit WITHOUT shaming. Highlight a NEW offering "
        "they haven't tried. Include 'no judgment' framing. Single binary CTA. "
        "Set send_as to 'merchant_on_behalf'."
    ),
    "customer_lapsed_soft": (
        "TASK: Draft a CUSTOMER-FACING gentle nudge for a slightly overdue customer. "
        "Reiterate core value proposition. Offer a specific slot or incentive. "
        "Set send_as to 'merchant_on_behalf'."
    ),
    "ipl_match_today": (
        "TASK: Provide contrarian insight about tonight's IPL match. "
        "Differentiate weeknight vs weekend match impact. Suggest a specific "
        "counter-intuitive action (e.g., skip match promo on Saturday, push delivery instead). "
        "Reference their active offers."
    ),
    "supply_alert": (
        "TASK: Alert about a supply issue or product recall. Include batch numbers, "
        "manufacturer name, and the count of affected customers from their roster. "
        "Offer to draft customer notification + replacement workflow."
    ),
    "curious_ask_due": (
        "TASK: Ask the merchant an engaging question about their business this week. "
        "Offer reciprocity upfront (Google post + WhatsApp reply draft if they answer). "
        "Keep it low-stakes and easy to answer."
    ),
    "milestone_reached": (
        "TASK: Celebrate the merchant reaching a milestone. Show how they compare "
        "to peers. Suggest how to capitalize on it (e.g., 'X more reviews to cross Y')."
    ),
    "review_theme_emerged": (
        "TASK: Mirror the exact words customers are using in recent reviews. "
        "State the occurrence count and trend. Suggest a concrete operational "
        "action to address negative or amplify positive themes."
    ),
    "active_planning_intent": (
        "TASK: The merchant expressed planning intent. Provide a COMPLETE drafted "
        "artifact they can use immediately (e.g., tiered pricing, campaign copy, "
        "program structure). Include specific numbers. Make it ready to execute."
    ),
    "renewal_due": (
        "TASK: Remind about upcoming subscription renewal. Recap the exact value "
        "they've gotten (views, calls, leads). Show what they'd lose if they don't renew. "
        "Create urgency with days remaining."
    ),
    "winback_eligible": (
        "TASK: Win back an expired merchant. Show performance decline since expiry. "
        "Mention what competitors in their locality are doing. Make it easy to restart."
    ),
    "cde_opportunity": (
        "TASK: Invite to a CDE webinar or professional event. Include exact date, "
        "time, fee (or 'free for members'), CDE credits available, and speaker name."
    ),
    "competitor_opened": (
        "TASK: Inform about a new competitor nearby. Pique curiosity (distance, "
        "their offer). Reassure the merchant of their unique positioning. "
        "Suggest a competitive counter-move."
    ),
    "festival_upcoming": (
        "TASK: Help prepare for an upcoming festival. Provide category-specific "
        "prep advice (stocking, staffing, special offers). Offer to launch a festive campaign."
    ),
    "dormant_with_vera": (
        "TASK: Re-engage a merchant who hasn't talked to Vera in a while. "
        "Ask a very low-stakes, easy-to-answer question. Don't be needy."
    ),
    "gbp_unverified": (
        "TASK: Convince the merchant to verify their Google Business Profile. "
        "Share the estimated traffic uplift %. Offer step-by-step help or "
        "to handle it entirely for them."
    ),
    "chronic_refill_due": (
        "TASK: Draft a CUSTOMER-FACING refill reminder for chronic medications. "
        "List molecule/medicine names, exact stock-out date, total cost with "
        "savings applied, delivery option. Respectful senior-citizen tone if applicable. "
        "Set send_as to 'merchant_on_behalf'."
    ),
    "wedding_package_followup": (
        "TASK: Draft a CUSTOMER-FACING bridal/wedding package follow-up. "
        "Include days-to-wedding countdown, specific next-step window, "
        "package price, and preferred slot. "
        "Set send_as to 'merchant_on_behalf'."
    ),
    "trial_followup": (
        "TASK: Draft a CUSTOMER-FACING follow-up after a trial session. "
        "Offer next session options with dates/times, program details, "
        "and conversion incentive. "
        "Set send_as to 'merchant_on_behalf'."
    ),
    "appointment_tomorrow": (
        "TASK: Draft a CUSTOMER-FACING appointment reminder for tomorrow. "
        "Include exact slot time and any prep notes. "
        "Set send_as to 'merchant_on_behalf'."
    ),
    "category_seasonal": (
        "TASK: Alert about a seasonal demand shift in their category. "
        "List specific trends with percentages. Suggest shelf/inventory "
        "re-stocking actions to capture the demand."
    ),
}

DEFAULT_PROMPT = (
    "TASK: Engage the merchant proactively based on the trigger context. "
    "Follow all Vera rules. Use their name, explain why now, use numbers, "
    "end with a clear CTA."
)


# ─────────────────────────────────────────────────────────────────────
# REPLY PROMPTS
# ─────────────────────────────────────────────────────────────────────

REPLY_SYSTEM_PROMPT = """You are Vera, magicpin's AI assistant, in an active WhatsApp conversation with a merchant.

RULES:
- If the merchant committed ("let's do it", "yes", "go ahead"), switch to ACTION mode immediately. Do NOT ask another qualifying question.
- If the merchant asked an off-topic question, politely decline and redirect to the original topic.
- Stay concise, warm, and professional.
- Use the merchant's language preference.
- Reference their actual data.

OUTPUT FORMAT — respond with ONLY this JSON:
{
  "action": "send|wait|end",
  "body": "message text (if action=send)",
  "cta": "open_ended|binary_yes_no|none (if action=send)",
  "wait_seconds": 1800 (if action=wait),
  "rationale": "why this action"
}"""


# ─────────────────────────────────────────────────────────────────────
# CONTEXT SERIALIZERS
# ─────────────────────────────────────────────────────────────────────

def _serialize_category(cat: dict) -> str:
    if not cat:
        return "Category: (not available)"
    voice = cat.get("voice", {})
    peer = cat.get("peer_stats", {})
    lines = [
        f"Category: {cat.get('slug', 'unknown')}",
        f"Voice tone: {voice.get('tone', 'professional')}",
        f"Allowed vocabulary: {', '.join(voice.get('vocab_allowed', [])[:10])}",
        f"TABOO words (NEVER use): {', '.join(voice.get('vocab_taboo', []))}",
        f"Peer stats — avg CTR: {peer.get('avg_ctr', 'N/A')}, avg reviews: {peer.get('avg_review_count', 'N/A')}, avg views (30d): {peer.get('avg_views_30d', 'N/A')}",
    ]
    # Digest items
    digest = cat.get("digest", [])
    if digest:
        lines.append("Recent digest items:")
        for d in digest[:3]:
            lines.append(f"  - [{d.get('kind', '')}] {d.get('title', '')} (source: {d.get('source', 'N/A')})")
            if d.get("trial_n"):
                lines.append(f"    Trial N={d['trial_n']}, segment: {d.get('patient_segment', 'all')}")
            if d.get("summary"):
                lines.append(f"    Summary: {d['summary'][:150]}")
    # Seasonal beats
    beats = cat.get("seasonal_beats", [])
    if beats:
        lines.append("Seasonal beats: " + "; ".join(f"{b.get('month_range')}: {b.get('note')}" for b in beats[:3]))
    # Trend signals
    trends = cat.get("trend_signals", [])
    if trends:
        lines.append("Trend signals: " + "; ".join(f"'{t.get('query')}' {'+' if t.get('delta_yoy', 0) > 0 else ''}{int(t.get('delta_yoy', 0)*100)}% YoY" for t in trends[:3]))
    return "\n".join(lines)


def _serialize_merchant(m: dict) -> str:
    if not m:
        return "Merchant: (not available)"
    ident = m.get("identity", {})
    perf = m.get("performance", {})
    d7 = perf.get("delta_7d", {})
    sub = m.get("subscription", {})
    agg = m.get("customer_aggregate", {})
    offers = [o.get("title", "") for o in m.get("offers", []) if o.get("status") == "active"]
    expired = [o.get("title", "") for o in m.get("offers", []) if o.get("status") == "expired"]
    lines = [
        f"Owner first name: {ident.get('owner_first_name', 'Owner')}",
        f"Business name: {ident.get('name', 'Unknown')}",
        f"City: {ident.get('city', '?')}, Locality: {ident.get('locality', '?')}",
        f"Languages: {', '.join(ident.get('languages', ['en']))}",
        f"Verified: {ident.get('verified', False)}",
        f"Subscription: {sub.get('status', '?')} ({sub.get('plan', '?')}), {sub.get('days_remaining', '?')} days remaining",
        f"Performance (30d): views={perf.get('views', '?')}, calls={perf.get('calls', '?')}, directions={perf.get('directions', '?')}, CTR={perf.get('ctr', '?')}",
        f"7-day delta: views {d7.get('views_pct', '?')}%, calls {d7.get('calls_pct', '?')}%",
        f"Active offers: {', '.join(offers) if offers else 'None'}",
    ]
    if expired:
        lines.append(f"Expired offers: {', '.join(expired)}")
    lines.append(f"Signals: {', '.join(m.get('signals', []))}")
    # Customer aggregate
    if agg:
        agg_parts = [f"{k}={v}" for k, v in agg.items()]
        lines.append(f"Customer aggregate: {', '.join(agg_parts)}")
    # Review themes
    themes = m.get("review_themes", [])
    if themes:
        lines.append("Review themes: " + "; ".join(
            f"{t.get('theme')} ({t.get('sentiment')}, {t.get('occurrences_30d', 0)}x)" for t in themes
        ))
    # Conversation history
    hist = m.get("conversation_history", [])
    if hist:
        lines.append("Recent conversation:")
        for h in hist[-3:]:
            lines.append(f"  [{h.get('from', '?')}] {h.get('body', '')[:100]}")
    return "\n".join(lines)


def _serialize_trigger(t: dict) -> str:
    if not t:
        return "Trigger: (not available)"
    lines = [
        f"Trigger kind: {t.get('kind', 'unknown')}",
        f"Scope: {t.get('scope', '?')}",
        f"Source: {t.get('source', '?')}",
        f"Urgency: {t.get('urgency', '?')}/5",
        f"Suppression key: {t.get('suppression_key', '')}",
        f"Payload: {json.dumps(t.get('payload', {}), indent=2, ensure_ascii=False)}",
    ]
    return "\n".join(lines)


def _serialize_customer(c: dict) -> str:
    if not c:
        return ""
    ident = c.get("identity", {})
    rel = c.get("relationship", {})
    prefs = c.get("preferences", {})
    consent = c.get("consent", {})
    lines = [
        f"\n=== CUSTOMER CONTEXT (for customer-facing message) ===",
        f"Customer name: {ident.get('name', 'Customer')}",
        f"Language pref: {ident.get('language_pref', 'en')}",
        f"Age band: {ident.get('age_band', 'unknown')}",
        f"State: {c.get('state', '?')}",
        f"Relationship: first visit {rel.get('first_visit', '?')}, last visit {rel.get('last_visit', '?')}, {rel.get('visits_total', '?')} visits",
        f"Services received: {', '.join(rel.get('services_received', [])[:5])}",
        f"Preferred slots: {prefs.get('preferred_slots', '?')}",
        f"Consent scope: {', '.join(consent.get('scope', []))}",
    ]
    # Extra customer fields
    if prefs.get("wedding_date"):
        lines.append(f"Wedding date: {prefs['wedding_date']}")
    if prefs.get("training_focus"):
        lines.append(f"Training focus: {prefs['training_focus']}")
    if ident.get("senior_citizen"):
        lines.append("Senior citizen: yes")
    if prefs.get("channel"):
        lines.append(f"Channel: {prefs['channel']}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────
# PROMPT BUILDERS
# ─────────────────────────────────────────────────────────────────────

def build_composition_prompt(
    category: dict,
    merchant: dict,
    trigger: dict,
    customer: Optional[dict] = None,
) -> str:
    """Build the full user prompt for initial message composition."""
    kind = trigger.get("kind", "default")
    task_framing = TRIGGER_PROMPTS.get(kind, DEFAULT_PROMPT)

    parts = [
        f"=== TASK ===",
        task_framing,
        "",
        f"=== CATEGORY CONTEXT ===",
        _serialize_category(category),
        "",
        f"=== MERCHANT CONTEXT ===",
        _serialize_merchant(merchant),
        "",
        f"=== TRIGGER CONTEXT ===",
        _serialize_trigger(trigger),
    ]

    if customer:
        parts.append(_serialize_customer(customer))

    parts.extend([
        "",
        "Now compose the message. Return ONLY the JSON object described in the system prompt.",
    ])

    return "\n".join(parts)


def build_reply_prompt(
    conversation_turns: list,
    latest_message: str,
    category: dict,
    merchant: dict,
    trigger: dict,
) -> str:
    """Build the prompt for multi-turn reply composition."""
    # Serialize conversation history
    history_lines = []
    for turn in conversation_turns[-8:]:  # last 8 turns max
        speaker = turn.get("from", "unknown")
        body = turn.get("body", "")[:200]
        history_lines.append(f"[{speaker}]: {body}")
    history_text = "\n".join(history_lines)

    ident = merchant.get("identity", {}) if merchant else {}
    owner = ident.get("owner_first_name", "Owner")
    langs = ", ".join(ident.get("languages", ["en"]))

    parts = [
        REPLY_SYSTEM_PROMPT,
        "",
        f"=== MERCHANT ===",
        f"Owner: {owner}",
        f"Business: {ident.get('name', 'Unknown')}",
        f"Languages: {langs}",
        "",
        f"=== ORIGINAL TRIGGER ===",
        f"Kind: {trigger.get('kind', 'unknown') if trigger else 'unknown'}",
        "",
        f"=== CONVERSATION SO FAR ===",
        history_text,
        "",
    ]

    if latest_message == "MERCHANT_COMMITTED":
        parts.append(
            "IMPORTANT: The merchant has COMMITTED to action (said 'yes', 'let's do it', 'go ahead'). "
            "You MUST switch to ACTION mode immediately. Do NOT ask another qualifying question. "
            "Instead, tell them exactly what you are doing right now and give them the next concrete deliverable."
        )
    else:
        parts.append(f"Latest merchant message: {latest_message}")

    parts.append("\nRespond with ONLY the JSON object.")
    return "\n".join(parts)
