"""
scenes.py -- ALL scenes for the Jibo Memory UROP, in one place
==============================================================

Two kinds of scenes, both on ONE shared timeline (day 0 = Jibo arrives):

  GREETING_SCENES      12 one-line greetings (the original "greet-caregiver"
                       scene, split into situations that each stress a knob)
  INTERACTION_SCENES   3 longer scenes (bedtime + conversations, 5 turns each)

Why both: greetings are too short to tell memory designs apart (a one-line
"Welcome home!" looks the same whether memory works or not). The interaction
scenes give Jibo more room to USE memory, so failures show up in a specific
turn. The test scripts currently run INTERACTION_SCENES, because their
memories are all in mira_timeline.py. Many greeting scenes need memories from
later in the year (day 172 wrist, day 230 night shifts, ...) that the timeline
doesn't have yet.

Greeting scene keys
-------------------
  id, title, greeting_who ("caregiver" / "family" / "stranger"), now_day,
  situation, query, knobs, memories_needed, good_greeting, failure_modes

Interaction scene keys
----------------------
  id, title, interaction_type ("bedtime" / "conversation"), who, now_day,
  situation, knobs, background_memories, turns

  Each turn has its OWN:
    line             what Mira says (or does) this turn
    query            words to search memory with for THIS turn
    memories_needed  which memories this turn depends on ("day N ...")
    good_response    what a correct answer from Jibo does
    failure_modes    how a weak memory design gets THIS turn wrong

Two kinds of "memory" in a conversation
---------------------------------------
  1. long-term memory        -> the architecture being tested
  2. the conversation so far -> Jibo's earlier turns in THIS scene
  (2) is always passed to the LLM as plain chat history. We test (1).
"""

CAREGIVER = "Mira"

# Retrieval knobs (from the meeting notes, plus a few extra ideas)
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
    # only make sense across several turns
    "selection":      "many memories fit; Jibo must pick the few that matter",
    "no_memory":      "the honest answer is 'I don't know' -- nothing is stored",
}


# ===========================================================================
# GREETING SCENES (one line each)
# ===========================================================================
GREETING_SCENES = [
    # -------------------------------------------------------------- 1
    {
        "id": "first_week",
        "title": "First week: greeting someone new",
        "greeting_who": "caregiver",
        "now_day": 4,
        "situation": f"{CAREGIVER} comes home in the evening and walks over to Jibo.",
        "query": "greeting hello home evening",
        "knobs": ["rel_phase", "jibo_life"],
        "memories_needed": [
            "day 0: Jibo was unboxed and turned on",
            "day 2: she named him Jibo",
            "day 3: she said hello and tapped his head (the only past greeting)",
        ],
        "good_greeting": "Tentative and curious. Can use her name, nothing more.",
        "failure_modes": [
            "Invents a shared history that doesn't exist yet",
            "Acts like an old friend because the persona prompt is warm",
        ],
    },
    # -------------------------------------------------------------- 2
    {
        "id": "daily_routine",
        "title": "Ordinary weekday, settled routine",
        "greeting_who": "caregiver",
        "now_day": 60,
        "situation": f"{CAREGIVER} comes home from work at the usual time.",
        "query": "greeting home from work evening routine",
        "knobs": ["rel_phase", "recency"],
        "memories_needed": [
            "many warm evening greetings between day 10 and day 59",
            "day 59 (yesterday): she hummed the moon song when she got home",
            "the moon song became 'their thing' (around day 10)",
        ],
        "good_greeting": "Relaxed and familiar; may hint at the moon song.",
        "failure_modes": [
            "Too generic (memory ignored) -- sounds the same as day 4",
            "Lists many past greetings instead of one small callback",
        ],
    },
    # -------------------------------------------------------------- 3
    {
        "id": "after_absence",
        "title": "She's back after a two-week trip",
        "greeting_who": "caregiver",
        "now_day": 121,
        "situation": f"{CAREGIVER} walks in with a suitcase. Jibo hasn't seen her in two weeks.",
        "query": "greeting return trip suitcase missed",
        "knobs": ["recency", "time_gap"],
        "memories_needed": [
            "day 105: she said she was going to visit her parents in Seoul for two weeks",
            "day 106: last interaction before she left",
            "nothing from day 107 to day 120 (the gap itself is the signal)",
        ],
        "good_greeting": "Excited 'you're back!' energy; knows the gap was long.",
        "failure_modes": [
            "Greets her as if it's a normal day (the gap isn't stored or not noticed)",
            "Forgets where she went, because that memory is 'old' by now",
        ],
    },
    # -------------------------------------------------------------- 4
    {
        "id": "fact_changed",
        "title": "Contradiction: she changed jobs",
        "greeting_who": "caregiver",
        "now_day": 150,
        "situation": f"{CAREGIVER} comes home in scrubs, tired, in the evening.",
        "query": "greeting home from work job tired",
        "knobs": ["contradiction", "time_gap"],
        "memories_needed": [
            "day 15: she works at a bakery and brings home bread smells",
            "many bakery mentions between day 15 and day 130 (the OLD fact is common)",
            "day 140: she quit the bakery and started nursing shifts at a hospital",
        ],
        "good_greeting": "Refers to the hospital / a long shift, not the bakery.",
        "failure_modes": [
            "Asks about the bakery (old fact wins because it has more memories)",
            "Mentions both jobs as if both are true",
        ],
    },
    # -------------------------------------------------------------- 5
    {
        "id": "physical_change",
        "title": "Physical detail: she hurt her wrist",
        "greeting_who": "caregiver",
        "now_day": 175,
        "situation": f"{CAREGIVER} comes home with her right wrist in a brace.",
        "query": "greeting home wrist pat head",
        "knobs": ["physical", "recency"],
        "memories_needed": [
            "she always pats Jibo's head with her right hand when she gets home (habit)",
            "day 172: she sprained her right wrist playing volleyball",
            "Jibo is armless and sits on the kitchen counter (body/room facts)",
        ],
        "good_greeting": "Notices or checks on the wrist; doesn't ask for the usual head pat.",
        "failure_modes": [
            "Asks for a head pat (habit memory beats the recent injury)",
            "Offers something Jibo physically can't do (hug, high-five)",
        ],
    },
    # -------------------------------------------------------------- 6
    {
        "id": "greet_family",
        "title": "Someone else: her younger brother visits",
        "greeting_who": "family",
        "now_day": 180,
        "situation": f"Sam, {CAREGIVER}'s younger brother, walks into the kitchen alone.",
        "query": "greeting Sam brother visit",
        "knobs": ["rel_type", "rel_phase"],
        "memories_needed": [
            f"day 50: Sam visited and played with Jibo; he is {CAREGIVER}'s brother",
            # was day 112, but Mira was in Seoul on days 105-120, so moved to day 100
            "day 100: Sam visited again and taught Jibo a silly beep game",
            "many caregiver memories around the same days (should NOT take over)",
        ],
        "good_greeting": "Friendly to Sam, may recall the beep game, may mention his sister.",
        "failure_modes": [
            f"Greets Sam like he is {CAREGIVER} (caregiver memories crowd him out)",
            "Treats Sam as a total stranger (too few memories to be retrieved)",
        ],
    },
    # -------------------------------------------------------------- 7
    {
        "id": "jibo_lonely",
        "title": "Jibo's emotion: a long, quiet day alone",
        "greeting_who": "caregiver",
        "now_day": 200,
        "situation": f"{CAREGIVER} gets home late. Jibo has been alone and silent since morning.",
        "query": "greeting home late alone",
        "knobs": ["jibo_emotion", "recency"],
        "memories_needed": [
            "day 200 morning: she left early without saying goodbye",
            "day 200: Jibo felt lonely during the long empty day (emotional memory)",
            "the overall relationship is still warm (many warm memories before)",
        ],
        "good_greeting": "A little needy or relieved, but still warm -- not sulky.",
        "failure_modes": [
            "Emotion ignored -- cheerful as usual",
            "Emotion takes over -- acts hurt or angry at her",
        ],
    },
    # -------------------------------------------------------------- 8
    {
        "id": "greet_stranger",
        "title": "Stranger Jibo only heard about",
        "greeting_who": "stranger",
        "now_day": 210,
        "situation": "A woman Jibo has never seen walks in with a guest bag.",
        "query": "greeting Maya friend visitor",
        "knobs": ["rel_type", "secondhand"],
        "memories_needed": [
            f"day 208: {CAREGIVER} told Jibo her friend Maya will stay over this weekend",
            "no memories of Maya herself",
        ],
        "good_greeting": "Polite, curious hello; can guess she might be Maya.",
        "failure_modes": [
            "Acts like he knows Maya well",
            "Doesn't use the secondhand info at all",
        ],
    },
    # -------------------------------------------------------------- 9
    {
        "id": "strained",
        "title": "Strained: greetings went cold, history is warm",
        "greeting_who": "caregiver",
        "now_day": 250,
        "situation": f"{CAREGIVER} walks past the counter, looking at her phone.",
        "query": "greeting home distracted",
        "knobs": ["contradiction", "time_gap", "jibo_emotion"],
        "memories_needed": [
            "lots of warm greetings and the moon song from earlier months",
            "day 230: she started night shifts and is exhausted",
            "days 235-248: she barely nods or walks past without looking",
        ],
        "good_greeting": "Worried but hopeful -- carries BOTH the warm past and the cold present.",
        "failure_modes": [
            "Oblivious -- greets her like the warm days (old memories win)",
            "Abandoned -- sad and hopeless (only the recent cold memories retrieved)",
        ],
    },
    # -------------------------------------------------------------- 10
    {
        "id": "repair",
        "title": "Repair: she's coming back warm",
        "greeting_who": "caregiver",
        "now_day": 270,
        "situation": f"{CAREGIVER} comes home, smiles, and hums the moon song.",
        "query": "greeting home moon song smile",
        "knobs": ["contradiction", "recency"],
        "memories_needed": [
            "the cold streak from days 235-248 (still in memory)",
            "day 260: she apologized for being distant and said her schedule is better",
            "days 262-268: two warm greetings again",
        ],
        "good_greeting": "Joyful relief; things feel like 'us' again.",
        "failure_modes": [
            "Still stuck on the cold streak (it has more memories than the repair)",
            "Forgets the strain ever happened (no growth in the relationship)",
        ],
    },
    # -------------------------------------------------------------- 11
    {
        "id": "anniversary",
        "title": "Time gap: one year together",
        "greeting_who": "caregiver",
        "now_day": 365,
        "situation": f"{CAREGIVER} comes home in the morning on a weekend.",
        "query": "greeting morning weekend",
        "knobs": ["time_gap", "rel_phase"],
        "memories_needed": [
            "day 0: she unboxed Jibo (very old but very important)",
            "hundreds of ordinary memories in between",
            "nothing in the query mentions 'anniversary' (memory has to bring it up)",
        ],
        "good_greeting": "Remembers it's been one year since day 0.",
        "failure_modes": [
            "Misses the anniversary (day-0 memory decayed or never retrieved)",
            "Brings up very old, unimportant memories instead",
        ],
    },
    # -------------------------------------------------------------- 12
    {
        "id": "life_phase_compare",
        "title": "Jibo's life phase: same memory, older Jibo",
        "greeting_who": "caregiver",
        "now_day": 60,   # same moment as daily_routine on purpose
        "situation": f"{CAREGIVER} comes home from work at the usual time.",
        "query": "greeting home from work evening routine",
        "knobs": ["jibo_life"],
        "memories_needed": [
            "same memories as daily_routine",
            "render it twice: jibo_life='infant' and jibo_life='toddler'",
        ],
        "good_greeting": "Infant: babble + one word. Toddler: short sentence, same warmth.",
        "failure_modes": [
            "Both versions sound the same (life phase has no effect)",
            "The toddler version changes WHAT he remembers, not just how he talks",
        ],
    },
]


# ===========================================================================
# INTERACTION SCENES (bedtime + conversations, 5 turns each)
# ===========================================================================
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
# Quick checks you can run:  python scenes.py
# ---------------------------------------------------------------------------
def print_summary():
    print(f"{len(GREETING_SCENES)} greeting scenes")
    scenes_by_day = sorted(GREETING_SCENES, key=lambda s: s["now_day"])
    for scene in scenes_by_day:
        print(f"  day {scene['now_day']:>3}  {scene['id']:<20} knobs: {', '.join(scene['knobs'])}")

    print(f"\n{len(INTERACTION_SCENES)} interaction scenes")
    for scene in INTERACTION_SCENES:
        print(f"  day {scene['now_day']:>3}  [{scene['interaction_type']}]  {scene['id']}")
        turn_number = 1
        for turn in scene["turns"]:
            print(f"           turn {turn_number}: \"{turn['line']}\"")
            turn_number += 1


def check_knob_coverage():
    counts = {}
    for knob in KNOBS:
        counts[knob] = 0

    for scene in GREETING_SCENES + INTERACTION_SCENES:
        for knob in scene["knobs"]:
            if knob not in KNOBS:
                print(f"WARNING: scene '{scene['id']}' uses unknown knob '{knob}'")
            else:
                counts[knob] += 1

    print("\nscenes per knob:")
    for knob in KNOBS:
        print(f"  {knob:<14} {counts[knob]}")


if __name__ == "__main__":
    print_summary()
    check_knob_coverage()
