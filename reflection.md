# PawPal+ — AI Collaboration Reflection

## How I Used AI Throughout This Project

### Phase 1 — Design & Structure
I used AI to help me think through the object model before writing a single line of code. I described what the app needed to do ("schedule pet care tasks based on priority and owner availability") and asked it to suggest which classes, attributes, and relationships made sense. The AI proposed the `Owner → Pet → Task` ownership chain, which I adopted because it mirrors real life: owners manage pets, pets have tasks.

One decision the AI explained clearly was *why* `Scheduler` should call `owner.get_all_tasks()` instead of receiving a flat list of tasks directly — it keeps the scheduling logic decoupled from how tasks are stored, which makes the code easier to extend and test.

### Phase 2 — Data Structures
When I asked "what data structures would make this faster and stand out?", the AI walked me through several options and the trade-offs:

| Structure | Why I used it |
|---|---|
| `heapq` | O(log n) ordering of tasks by priority without sorting the whole list each time |
| `IntEnum` | Lets `Priority` values be compared with `<` and `>` like integers, not just strings |
| `defaultdict` | Groups tasks by time slot without manually checking if a key exists |
| `deque(maxlen=10)` | Rolling history of past schedules, fixed memory — no cleanup code needed |

I wouldn't have thought to use a heap for task ordering on my own. That was a genuine improvement suggested by AI.

### Phase 3 — Smart Features
The AI helped me implement four features I wasn't sure how to approach:

**Sorting by time slot:** I didn't know how to sort on a custom order (morning before afternoon before evening). AI showed me the `TIME_ORDER` dictionary trick — map strings to integers and sort on those.

**Recurring tasks:** I debated whether `mark_complete()` should return a new Task or add it directly to the pet. The AI argued for returning it (single responsibility principle) and having `Scheduler.mark_task_complete()` add it to the pet. That separation made testing much easier.

**Conflict detection:** I didn't know how to compare two time windows. AI explained the interval overlap formula: `a.start < b.end and b.start < a.end`. Adding `start_dt`/`end_dt` to `ScheduledTask` was its suggestion so I wouldn't have to re-parse strings inside the detection loop.

**`filter_tasks` signature:** The AI suggested making `pet_name` and `completed` both optional with a default of `None` so the caller can filter on one, both, or neither. That's a pattern I'll use again.

### Phase 4 — Testing & UI
For tests, I described the behaviors I wanted to verify in plain English, and AI translated them into pytest fixtures and test methods. The trickiest fix was when two tests shared a fixture that already had a pet attached — isolating them with a fresh `busy_owner` / `busy_pet` pair was something I hadn't caught on my own.

For the Streamlit UI, I asked AI to show me which Streamlit components to use for each piece of data (`st.metric`, `st.table`, `st.expander`, `st.warning`) and how to persist objects across re-renders using `st.session_state`. The four-tab layout (Pets / Tasks / Schedule / Insights) was a structure the AI proposed and I kept it because it separates data entry from analysis clearly.

---

## What I Would Do Differently

1. **Start with tests sooner.** I wrote most of the system before writing any tests, which meant some bugs hid until Phase 3. Writing even two tests per class at the start would have caught the `completed` attribute being missing from the original `Task` skeleton.

2. **Be more specific in prompts.** Early prompts like "create a skeleton" returned stubs with `pass` everywhere. Later I learned to say "implement this method, handle these edge cases, and return this type" — AI's output was much more usable.

3. **Ask AI to explain, not just generate.** The most valuable moments were when I asked *why* a data structure or pattern was chosen, not just *what* to write. That's where I actually learned something.

---

## AI as a Collaborator

AI worked best as a senior pair-programmer who could explain trade-offs and catch gaps in my design. It was less useful when I gave it vague prompts or when I asked it to do things that were really design decisions I needed to make myself (like what features the app should have). The clearer and more specific my prompts, the better the output.

The final codebase is mine — I understood every method before it went in, debugged it when tests failed, and made every major design call. AI sped up the parts where I knew *what* I wanted but not the exact *how*.
