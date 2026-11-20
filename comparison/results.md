# Comparison of memory architectures (free checks, no LLM calls)

## 1. Needed memories that reached the prompt

| Scene | a_log | b_rag_tfidf | c_temporal_graph |
|---|---|---|---|
| bedtime_hospital_week | 9/9 | 6/9 | 8/9 |
| conversation_back_from_seoul | 5/5 | 3/5 | 5/5 |
| conversation_work_talk | 4/4 | 3/4 | 4/4 |
| **Total** | **18/18** | **12/18** | **17/18** |

## 2. Retrieval size sweep

| Setting | 3 | 6 (default) | 10 |
|---|---|---|---|
| RAG (TF-IDF) TOP_K | 10/18 | 12/18 | 12/18 |
| Temporal graph RECENT_N | 15/18 | 17/18 | 18/18 |

## 3. Where needed memories sit in the log prompt (a_log)

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

## 4. Memory block size per architecture

| Architecture | Avg characters | ~Tokens (chars / 4) |
|---|---|---|
| a_log | 1754 | 438 |
| b_rag_tfidf | 397 | 99 |
| c_temporal_graph | 781 | 195 |

