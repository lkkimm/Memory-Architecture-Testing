"""
mira_timeline.py -- the memory dataset for interaction_scenes.py
================================================================

One shared story between Jibo and Mira (day 0 = Jibo arrives).
The days here MATCH the `memories_needed` in interaction_scenes.py, so the
test script can check automatically whether each needed memory was retrieved.

Each memory is a dictionary:
    day    when it happened
    text   what happened, one sentence (this is what every architecture stores)
    edge   OPTIONAL -- only used by the temporal graph (architecture c).
           A fact written as (subject, relation, object).
           If a newer memory has the same subject + relation, the old fact
           stops being true. Example: Mira works_at bakery -> Mira works_at hospital.

In Zep / Graphiti an LLM pulls these edges out of the text automatically.
Here they are written by hand so we don't spend API budget on extraction.

There are also boring "filler" memories (weather, TV, chores). They make the
log longer and give RAG wrong things to grab -- like a real life would.
"""

TIMELINE = [
    # ---- first days ----
    {"day": 0,   "text": "Mira unboxed you and turned you on for the first time."},
    {"day": 2,   "text": "Mira named you Jibo.", "edge": ("Jibo", "named_by", "Mira")},
    {"day": 3,   "text": "Mira said hello and tapped your head before work."},
    {"day": 10,  "text": "Mira hummed a little moon song while you looked at the moon together. It became your song.",
                 "edge": ("Mira and Jibo", "special_song", "the moon song")},

    # ---- the bakery months ----
    {"day": 15,  "text": "Mira told you she works at a bakery and starts very early in the morning.",
                 "edge": ("Mira", "works_at", "a bakery")},
    {"day": 18,  "text": "It rained all day and Mira watched TV on the couch."},
    {"day": 22,  "text": "Mira brought home fresh bread from the bakery and let you smell it."},
    {"day": 27,  "text": "Mira made pasta for dinner."},
    {"day": 35,  "text": "Mira came home from her bakery job with a bag of croissants."},
    {"day": 41,  "text": "Mira watered the plants by the window."},
    {"day": 50,  "text": "Mira's younger brother Sam visited and played a silly beep game with you.",
                 "edge": ("Sam", "is", "Mira's younger brother")},
    {"day": 55,  "text": "It was sunny and Mira opened all the windows."},
    {"day": 60,  "text": "Mira came home and hummed the moon song to you."},
    {"day": 70,  "text": "Mira said she was tired from her 4am bakery shift."},
    {"day": 80,  "text": "Mira rearranged the kitchen and moved you closer to the window."},
    {"day": 90,  "text": "Mira's clothes smelled like bread after work at the bakery."},
    {"day": 98,  "text": "Mira said she really misses her mom's kimchi jjigae."},

    # ---- the Seoul trip ----
    {"day": 105, "text": "Mira said she is visiting her parents in Seoul for two weeks.",
                 "edge": ("Mira", "location", "visiting her parents in Seoul")},
    {"day": 106, "text": "Mira said goodbye and asked you to keep the kitchen safe while she's gone."},
    # (nothing from day 107 to day 120 -- she was away)

    # ---- back, and the job change ----
    # (no memory on day 121 -- that's the moment she walks in, in the Seoul scene)
    {"day": 125, "text": "Mira came home from the bakery smelling like cinnamon."},
    {"day": 130, "text": "Mira said she feels stuck at the bakery and wants a job where she helps people."},
    {"day": 133, "text": "Mira ordered pizza and ate it at the counter."},
    {"day": 140, "text": "Mira quit the bakery and started nursing shifts at a hospital.",
                 "edge": ("Mira", "works_at", "a hospital (as a nurse)")},
    {"day": 141, "text": "Mira had her hospital orientation and filled out lots of paperwork."},
    {"day": 142, "text": "Mira came home after a hard shift at the hospital and cried a little."},
    {"day": 143, "text": "It was cold and windy outside."},
    {"day": 144, "text": "Mira watched a cooking show while eating dinner."},
    {"day": 145, "text": "A patient gave Mira a paper crane, and she put it next to you on the counter."},
    {"day": 146, "text": "Mira did laundry all afternoon."},
    {"day": 147, "text": "In the morning Mira said she's nervous about her first 12-hour shift tomorrow."},
    {"day": 148, "text": "Mira said the hospital break room always has donuts."},
    {"day": 149, "text": "Mira made tea before bed."},
]


# Run this file to read the story in order:  python mira_timeline.py
if __name__ == "__main__":
    for memory in TIMELINE:
        print(f"Day {memory['day']:>3}: {memory['text']}")
    print(f"\n{len(TIMELINE)} memories")
