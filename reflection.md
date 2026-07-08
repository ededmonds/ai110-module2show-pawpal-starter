# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?
- Classes add:
- Task - title, duration, priority, preferred time , notes 
- Pet -name, species, age , special needs 
- Owner - name , availability, preferences
- Scheduler - sorts tasks by priority ( high first , then medium, then low ), fits them into the owner's availability window sequentially
- UI
- Sidebar - owner and pet info
- add/delete tasks
- build schedule generates the day plan with expandable cards showing start /end time and explanation for each task
- warns about any tasks that couldn't be fit

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
AI stated that Missing Relationships the Owner has no direct link to Pet. In the real world an owner owns pets, but right now Scheduler holds both separately. Consider adding a pets list to Owner:
-PRIORITY_RANK is a global dict instead of an Enum. If someone passes priority="High" (capital H) or typos it, priority_value() will silently return None. Replacing it with an Enum catches this at assignment time.
available_start and available_end are plain strings with no validation. If someone passes "7:00" instead of "07:00", datetime.strptime will crash inside build_schedule. Add validation in __post_init__:
- build_schedule has no guard for an empty task list — it should return ([], []) immediately.
- Task needs __lt__ so it works with heapq without errors when two tasks have equal priority:
pythondef __lt__(self, other):
    return self.duration_minutes < other.duration_minutes
Scheduler is missing _build_heap() and _group_by_time() stubs that were in your UML diagram but didn't make it into the skeleton.
Overall — the structure is solid. The main gaps are input validation, the missing Owner → Pet relationship, and the __lt__ method on Task.
- 
## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
