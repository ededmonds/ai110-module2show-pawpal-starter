# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
============================================================
  🐾 PawPal+ Daily Schedule
  Owner : Jordan
  Pet   : 🐶 Mochi (age 3)
  Hours : 07:00 – 20:00
============================================================

  1. 🔴 Feeding
     Time     : 07:00 AM → 07:10 AM
     Duration : 10 min
     Priority : High
     Why      : Scheduled at 07:00 AM (morning) because it is a high-priority task and placed first.

  2. 🔴 Litter box cleaning
     Time     : 07:10 AM → 07:20 AM
     Duration : 10 min
     Priority : High
     Why      : Scheduled at 07:10 AM (morning) because it is a high-priority task and placed first.

  3. 🔴 Morning walk
     Time     : 07:20 AM → 07:50 AM
     Duration : 30 min
     Priority : High
     Notes    : Use harness
     Why      : Scheduled at 07:20 AM (morning) because it is a high-priority task and placed first. Note: Use harness

  4. 🟡 Playtime
     Time     : 07:50 AM → 08:10 AM
     Duration : 20 min
     Priority : Medium
     Why      : Scheduled at 07:50 AM (morning) after all high-priority tasks are handled.

  5. 🟢 Brushing
     Time     : 08:10 AM → 08:25 AM
     Duration : 15 min
     Priority : Low
     Notes    : Luna is sensitive around ears
     Why      : Scheduled at 08:10 AM (morning) as a low-priority task, fitted into remaining time. Note: Luna is sensitive around ears
============================================================
  ✅ 5 task(s) scheduled  |  ⏱ 85 / 780 min used
============================================================

```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
(ai110-module2show-pawpal-starter) ericedmonds@Erics-MacBook-Pro-2 ai110-module2show-pawpal-starter % python -m pytest
===================================================================================== test session starts =====================================================================================
platform darwin -- Python 3.13.12, pytest-7.0.0, pluggy-1.6.0
rootdir: /Users/ericedmonds/PycharmProjects/ai110-module2show-pawpal-starter
plugins: anyio-4.14.1
collected 2 items                                                                                                                                                                             

tests/test_pawpal.py ..                                                                                                                                                                 [100%]

====================================================================================== 2 passed in 0.04s ======================================================================================

```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

## Smarter Scheduling

| Feature | Method | Description |
|---|---|---|
| Sorting | `Scheduler.sort_by_time()` | Sorts tasks by time slot: morning → afternoon → evening → any |
| Filtering | `Scheduler.filter_tasks()` | Filters tasks by pet name and/or completion status |
| Recurring tasks | `Scheduler.mark_task_complete()` | Marks a task done and auto-creates the next occurrence for daily/weekly tasks |
| Conflict detection | `Scheduler.detect_conflicts()` | Checks scheduled tasks for overlapping time windows and returns warning strings |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
