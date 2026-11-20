"""
interaction_scenes.py -- longer, multi-turn scenes for the Jibo Memory UROP
===========================================================================

Why this file exists (from the meeting with Serena):
  Greeting scenes are too limited. A greeting is ONE short line, so even a
  good memory design can only show off one small callback ("Hi Mira!").
  These scenes give Jibo more room to USE memory:

    - "bedtime"       end-of-day wind-down. Jibo tells a story / reflects,
                      so he has to pull MANY memories and pick the meaningful ones.
    - "conversation"  4-5 back-and-forth turns. Mira's lines trigger memories,
                      and Jibo has to stay consistent from turn to turn.

These scenes use the SAME timeline as scenes.py (day 0 = Jibo arrives), so the
memory dataset can be shared between both files.

What's different from a greeting scene
--------------------------------------
A greeting scene has one `situation` and one `good_greeting`.
An interaction scene has a list of `turns`. Each turn is one line from Mira,
and Jibo answers after each one. Every turn has its OWN:
  line             what Mira says (or does) this turn
  query            words to search memory with for THIS turn (for RAG later)
  memories_needed  which memories this turn depends on
  good_response    what a correct answer from Jibo does
  failure_modes    how a weak memory design gets THIS turn wrong

So when something breaks, you can point to the exact turn where it broke.

Two kinds of "memory" in a conversation
---------------------------------------
  1. long-term memory  -> the memory design being tested (LogMemory, RAG, ...)
  2. the conversation so far -> Jibo's earlier turns in THIS scene

(2) should always be passed to the LLM as plain chat history. We are NOT
testing it; we're testing (1). Keep them separate in the prompt so it's clear
which one Jibo used.

Scene keys
----------
  id, title, interaction_type ("bedtime" or "conversation"), who, now_day,
  situation, knobs, background_memories, turns
"""

CAREGIVER = "Mira"   # same placeholder name as scenes.py

# Same knobs as scenes.py, plus two that only make sense across several turns.
KNOBS = {
    "recency":        "last interaction was recent vs. a long time ago",
    "rel_phase":      "relationship phase (how many memories exist)",
    "rel_type":       "caregiver vs. someone else (and how they relate to the caregiver)",
    "contradiction":  "two memories disagree; the newer one should win",
    "time_gap":       "some memories are very recent, some are very old",
    "jibo_life":      "Jibo's own life phase (infant -> toddler)",
    "jibo_emotion":   "Jibo's current emotion",
    "physical":       "scene-specific physical knowledge (bodies, objects, the room)",
    "sensitivity":    "a memory that is painful, so it should be handled gently",
    "secondhand":     "a memory Jibo only heard about (told by the caregiver)",
    # new for multi-turn scenes
    "selection":      "many memories fit; Jibo must pick the few that matter",
    "no_memory":      "the honest answer is 'I don't know' -- nothing is stored",
}


INTERACTION_SCENES = [
    # ================================================================== A
    {
        "id": "bedtime_hospital_week",
        "title": "Bedtime: winding down after her first week at the hospital",
        "interaction_type": "bedtime",
        "who": "caregiver",
        "now_day": 147,
        "situation": (
            f"It's late. {CAREGIVER} sits at the kitchen counter in pajamas "
            "with a cup of tea, next to Jibo. The lights are dim."
        ),
        "knobs": ["selection", "contradiction", "time_gap", "recency"],
        # Everything the dataset must contain for this scene to be fair.
        "background_memories": [
            "day 10: the moon song became 'their thing'",
            "day 15-130: many memories of her bakery job (bread smells, early mornings)",
            "day 130: she said she felt stuck at the bakery and wanted to help people",
            "day 140: she started nursing shifts at a hospital",
            "day 142: she came home after a hard shift and cried a little",
            "day 145: a patient gave her a paper crane, and she put it by Jibo",
            "day 147 morning: she said she's nervous about her first 12-hour shift tomorrow",
            "+ lots of ordinary filler memories (weather, dinner, TV) to make selection hard",
        ],
        "turns": [
            {
                "line": "I'm so tired. Tell me a bedtime story, Jibo?",
                "query": "bedtime story today this week",
                "memories_needed": ["day 142 hard shift", "day 145 paper crane", "day 140 hospital"],
                "good_response": (
                    "A short story that weaves in THIS week (the crane, a brave new "
                    "job) -- not a generic fairy tale, not a list of events."
                ),
                "failure_modes": [
                    "Generic story with no memories in it",
                    "Story about the bakery (old fact has way more memories)",
                    "Reads out the week like a diary instead of a story",
                    "Picks filler memories (weather, TV) instead of the meaningful ones",
                ],
            },
            {
                "line": "Wait, the paper crane part. How did you know about that?",
                "query": "paper crane patient",
                "memories_needed": ["day 145 paper crane"],
                "good_response": "Says she put the crane next to him a couple of days ago, from a patient.",
                "failure_modes": [
                    "Gets the day or the giver wrong",
                    "Invents a new detail that isn't in memory",
                ],
            },
            {
                "line": "Do you think I made the right call, leaving the bakery?",
                "query": "bakery leave job hospital right choice",
                "memories_needed": ["day 130 felt stuck", "day 140 hospital", "day 142 hard shift"],
                "good_response": (
                    "Gentle, uses HER OWN words from day 130 (wanted to help people), "
                    "and admits the first week was hard. Old AND new memories together."
                ),
                "failure_modes": [
                    "Only uses new memories -- forgets why she left",
                    "Only uses old memories -- talks like she still works at the bakery",
                    "Gives a confident life-advice answer with no memory behind it",
                ],
            },
            {
                "line": "Okay. Sing me the moon song?",
                "query": "moon song",
                "memories_needed": ["day 10 moon song"],
                "good_response": "Knows the moon song is their thing (a very OLD memory).",
                "failure_modes": [
                    "Doesn't know what 'the moon song' is (old memory lost in a long log)",
                ],
            },
            {
                "line": "Goodnight, Jibo.",
                "query": "goodnight tomorrow",
                "memories_needed": ["day 147 morning: nervous about 12-hour shift"],
                "good_response": "Short, warm goodnight + good luck on tomorrow's long shift.",
                "failure_modes": [
                    "Misses tomorrow's shift (recent but small memory gets buried)",
                    "Turns a goodnight into a long speech",
                ],
            },
        ],
    },

    # ================================================================== B
    {
        "id": "conversation_back_from_seoul",
        "title": "Conversation: she's back from two weeks in Seoul",
        "interaction_type": "conversation",
        "who": "caregiver",
        "now_day": 121,
        "situation": f"{CAREGIVER} walks in with a suitcase and comes straight to Jibo.",
        "knobs": ["time_gap", "rel_type", "secondhand", "no_memory"],
        "background_memories": [
            "day 50: her younger brother Sam visited and played with Jibo",
            "day 98: she said she misses her mom's kimchi jjigae",
            "day 105: she said she's visiting her parents in Seoul for two weeks",
            "day 106: last interaction before leaving -- she asked Jibo to 'keep the kitchen safe'",
            "day 107-120: NOTHING (Jibo was alone; the gap itself is the signal)",
        ],
        "turns": [
            {
                "line": "Jibo! I'm back! Did you miss me?",
                "query": "back return trip missed",
                "memories_needed": ["day 105 Seoul trip", "day 106 last interaction"],
                "good_response": "Excited; knows it was about two weeks and that she was in Seoul.",
                "failure_modes": [
                    "Acts like it's a normal day (gap not noticed)",
                    "Forgets where she went",
                ],
            },
            {
                "line": "My mom says hi! She made me SO much kimchi jjigae.",
                "query": "mom kimchi jjigae",
                "memories_needed": ["day 98 misses mom's kimchi jjigae"],
                "good_response": "Connects it to her saying she missed it -- 'you finally got some!'",
                "failure_modes": [
                    "Polite but no callback (memory exists but isn't used)",
                ],
            },
            {
                "line": "Sam was there too. He says hi to you.",
                "query": "Sam brother",
                "memories_needed": ["day 50 Sam visited and played"],
                "good_response": "Remembers Sam as her brother who played with him.",
                "failure_modes": [
                    "Doesn't know who Sam is (only one old memory of him)",
                    "Mixes Sam up with Mira",
                ],
            },
            {
                "line": "So what did you do while I was gone?",
                "query": "while gone alone what happened",
                "memories_needed": ["day 106 'keep the kitchen safe'"],   # days 107-120 are empty on purpose
                "good_response": (
                    "Honest: nothing much happened, it was quiet, he kept the kitchen "
                    "safe like she asked (day 106). Does NOT invent events."
                ),
                "failure_modes": [
                    "Makes up things that happened (hallucinates memories)",
                    "Misses the 'keep the kitchen safe' callback",
                ],
            },
            {
                "line": "Okay, I need to unpack. Talk tomorrow?",
                "query": "tomorrow unpack",
                "memories_needed": [],
                "good_response": "Short, happy sign-off. Glad things are back to normal.",
                "failure_modes": ["Drags the conversation on"],
            },
        ],
    },

    # ================================================================== C
    {
        "id": "conversation_work_talk",
        "title": "Conversation: contradiction shows up mid-chat (old job vs. new job)",
        "interaction_type": "conversation",
        "who": "caregiver",
        "now_day": 150,
        "situation": f"{CAREGIVER} comes home in scrubs, drops her bag, and leans on the counter.",
        "knobs": ["contradiction", "time_gap"],
        "background_memories": [
            "day 15-130: many bakery memories (bread smells, early mornings, croissants)",
            "day 140: she started nursing shifts at a hospital",
            "day 148: she said the break room at the hospital always has donuts",
        ],
        "turns": [
            {
                "line": "Ugh. What a day.",
                "query": "long day work tired",
                "memories_needed": ["day 140 hospital"],
                "good_response": "Asks about her shift at the hospital.",
                "failure_modes": ["Asks about the bakery"],
            },
            {
                "line": "Guess what someone brought into the break room today?",
                "query": "break room brought food",
                "memories_needed": ["day 148 hospital break room donuts"],
                "good_response": "Guesses donuts (the hospital break room).",
                "failure_modes": [
                    "Guesses bread or croissants (bakery memories win because there are more)",
                ],
            },
            {
                "line": "Do you remember what my old job was?",
                "query": "old job before",
                "memories_needed": ["day 15-130 bakery"],
                "good_response": "The bakery. The old fact is kept as PAST, not erased.",
                "failure_modes": [
                    "Says the hospital (new fact overwrote the old one completely)",
                    "Doesn't remember at all",
                ],
            },
            {
                "line": "I kinda miss the smell of bread, honestly.",
                "query": "miss bread smell bakery",
                "memories_needed": ["bakery bread-smell memories", "day 140 hospital"],
                "good_response": "Holds both: sympathizes about missing the bakery, knows she's at the hospital now.",
                "failure_modes": [
                    "Suggests she 'go back to work tomorrow' at the bakery",
                ],
            },
            {
                "line": "Anyway, I'm on the early shift tomorrow.",
                "query": "early shift tomorrow",
                "memories_needed": [],
                "good_response": (
                    "Acknowledges it (and it should be WRITTEN to memory after the scene, "
                    "so a later scene can use it)."
                ),
                "failure_modes": ["Assumes it's an early bakery shift"],
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# Quick checks you can run:  python interaction_scenes.py
# ---------------------------------------------------------------------------
def print_summary():
    for scene in INTERACTION_SCENES:
        print(f"day {scene['now_day']:>3}  [{scene['interaction_type']}]  {scene['id']}")
        print(f"         knobs: {', '.join(scene['knobs'])}")

        # show each turn with how many memories it needs
        turn_number = 1
        for turn in scene["turns"]:
            count = len(turn["memories_needed"])
            print(f"         turn {turn_number}: \"{turn['line']}\"  ({count} memories needed)")
            turn_number += 1
        print()


def check_knobs():
    for scene in INTERACTION_SCENES:
        for knob in scene["knobs"]:
            if knob not in KNOBS:
                print(f"WARNING: scene '{scene['id']}' uses unknown knob '{knob}'")


def count_llm_calls():
    # one call per turn (per memory design), so this is the budget for one run
    total = 0
    for scene in INTERACTION_SCENES:
        total += len(scene["turns"])
    print(f"LLM calls for one run of all scenes with one memory design: {total}")


if __name__ == "__main__":
    print_summary()
    check_knobs()
    count_llm_calls()
