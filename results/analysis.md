# Free analyses (no LLM calls)

## Experiment 1: retrieval size sweep

Needed memories that made it into the prompt (all 3 scenes, 15 turns).

| Setting | 3 | 6 (default) | 10 |
|---|---|---|---|
| b_rag TOP_K | 10/18 | 12/18 | 12/18 |
| c_temporal_graph RECENT_N | 15/18 | 17/18 | 18/18 |

## Experiment 2: where needed memories sit in the log prompt (a_log)

0% = first line of the memory block, 100% = last line.

| Scene | Turn | Needed memory | Position | Zone |
|---|---|---|---|---|
| bedtime_hospital_week | 1 | day 142 hard shift | 83% | end |
| bedtime_hospital_week | 1 | day 145 paper crane | 93% | end |
| bedtime_hospital_week | 1 | day 140 hospital | 76% | end |
| bedtime_hospital_week | 2 | day 145 paper crane | 93% | end |
| bedtime_hospital_week | 3 | day 130 felt stuck | 69% | middle |
| bedtime_hospital_week | 3 | day 140 hospital | 76% | end |
| bedtime_hospital_week | 3 | day 142 hard shift | 83% | end |
| bedtime_hospital_week | 4 | day 10 moon song | 10% | start |
| bedtime_hospital_week | 5 | day 147 morning: nervous about 12-hour shift | 100% | end |
| conversation_back_from_seoul | 1 | day 105 Seoul trip | 94% | end |
| conversation_back_from_seoul | 1 | day 106 last interaction | 100% | end |
| conversation_back_from_seoul | 2 | day 98 misses mom's kimchi jjigae | 89% | end |
| conversation_back_from_seoul | 3 | day 50 Sam visited and played | 56% | middle |
| conversation_back_from_seoul | 4 | day 106 'keep the kitchen safe' | 100% | end |
| conversation_work_talk | 1 | day 140 hospital | 71% | middle |
| conversation_work_talk | 2 | day 148 hospital break room donuts | 97% | end |
| conversation_work_talk | 4 | day 140 hospital | 71% | middle |

Totals: start 1, middle 4, end 12

## Experiment 3: memory block size per architecture

| Architecture | Avg characters | ~Tokens (chars / 4) |
|---|---|---|
| a_log | 1754 | 438 |
| b_rag | 397 | 99 |
| c_temporal_graph | 781 | 195 |

