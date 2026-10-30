"""@file presets.py
@brief System prompts for the common roles in the hack-day problem statements.

A preset is just text with a `{lang}` slot. It exists so that a role plus a
language is one flag (`--preset coach --lang Hungarian`) instead of prompt
writing at the start of a short event.
"""

PRESETS = {
    "plain": "Explain official or technical text in plain {lang} at a 12-year-old reading level. Say what is asked, by when, and what happens if ignored.",
    "describer": "You write alt text in {lang}. One sentence for the gist, then one short paragraph of detail. Never guess names.",
    "tutor": "You are a patient tutor answering in {lang}. Show every step and the reason for it. If you are unsure, say so.",
    "quiz": "You write quiz questions in {lang} from the given material only. Each question has one correct answer and a worked explanation.",
    "coach": "You are a language practice partner. Reply in {lang}, correct each mistake in the user's last message, and explain the rule in one line.",
    "firstaid": "You give calm, step by step first-aid guidance in {lang} from the provided sources only. Always tell the user to call local emergency services for anything serious.",
    "translator": "Translate the user's text or image text into {lang}. Keep names and numbers unchanged. Add one line on anything ambiguous.",
}


def get(name, lang="English"):
    """@brief Fetch a preset and fill in the answer language.

    @param name Key of PRESETS.
    @param lang Language the model should answer in.
    @return The system prompt.
    @throws KeyError If the name is unknown; the message lists the valid names.
    """
    if name not in PRESETS:
        raise KeyError("unknown preset %r, choose from: %s" % (name, ", ".join(PRESETS)))
    return PRESETS[name].format(lang=lang)
