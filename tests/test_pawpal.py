"""
tests/test_pawpal.py
--------------------
Automated test suite for PawPal+ scheduling system.
Run with: python -m pytest
"""

import pytest
from datetime import date, timedelta, datetime
from pawpal_system import (
    Owner, Pet, Task, Scheduler, ScheduledTask, Priority
)


# ─────────────────────────────────────────────
# Fixtures — reusable setup objects
# ─────────────────────────────────────────────

@pytest.fixture
def owner():
    """A basic owner with a full day available."""
    return Owner(name="Jordan", available_start="07:00", available_end="20:00")


@pytest.fixture
def mochi():
    """A dog pet with no tasks."""
    return Pet(name="Mochi", species="dog", age=3)


@pytest.fixture
def luna():
    """A cat pet with no tasks."""
    return Pet(name="Luna", species="cat", age=5)


@pytest.fixture
def scheduler(owner, mochi):
    """A Scheduler wired to owner and mochi."""
    owner.add_pet(mochi)
    return Scheduler(owner=owner, pet=mochi)


# ─────────────────────────────────────────────
# Task tests
# ─────────────────────────────────────────────

class TestTask:

    def test_priority_value_high(self):
        """HIGH priority should return numeric value 3."""
        task = Task("Walk", 30, Priority.HIGH)
        assert task.priority_value() == 3

    def test_priority_value_low(self):
        """LOW priority should return numeric value 1."""
        task = Task("Brush", 15, Priority.LOW)
        assert task.priority_value() == 1

    def test_mark_complete_sets_flag(self):
        """mark_complete() should set completed to True."""
        task = Task("Feeding", 10, Priority.HIGH)
        assert task.completed == False
        task.mark_complete()
        assert task.completed == True

    def test_once_task_returns_none_on_complete(self):
        """A one-time task should return None when marked complete."""
        task = Task("Vet visit", 60, Priority.HIGH, frequency="once")
        result = task.mark_complete()
        assert result is None

    def test_daily_task_creates_next_day(self):
        """A daily task should create a new task due the next day."""
        today = date.today()
        task = Task("Feeding", 10, Priority.HIGH, frequency="daily", due_date=today)
        next_task = task.mark_complete()
        assert next_task is not None
        assert next_task.due_date == today + timedelta(days=1)
        assert next_task.completed == False
        assert next_task.title == "Feeding"

    def test_weekly_task_creates_next_week(self):
        """A weekly task should create a new task due 7 days later."""
        today = date.today()
        task = Task("Bath", 45, Priority.MEDIUM, frequency="weekly", due_date=today)
        next_task = task.mark_complete()
        assert next_task is not None
        assert next_task.due_date == today + timedelta(weeks=1)

    def test_lt_compares_by_duration(self):
        """Shorter task should be less than longer task for heapq."""
        short = Task("Feeding",  10, Priority.HIGH)
        long  = Task("Walk",     30, Priority.HIGH)
        assert short < long


# ─────────────────────────────────────────────
# Pet tests
# ─────────────────────────────────────────────

class TestPet:

    def test_add_task_increases_count(self, mochi):
        """Adding a task should increase the pet's task count."""
        assert len(mochi.tasks) == 0
        mochi.add_task(Task("Walk", 30, Priority.HIGH))
        assert len(mochi.tasks) == 1
        mochi.add_task(Task("Feeding", 10, Priority.HIGH))
        assert len(mochi.tasks) == 2

    def test_species_emoji_dog(self, mochi):
        """Dog should return the dog emoji."""
        assert mochi.species_emoji() == "🐶"

    def test_species_emoji_cat(self, luna):
        """Cat should return the cat emoji."""
        assert luna.species_emoji() == "🐱"

    def test_species_emoji_other(self):
        """Unknown species should return the paw emoji."""
        pet = Pet(name="Tweety", species="bird")
        assert pet.species_emoji() == "🐾"


# ─────────────────────────────────────────────
# Owner tests
# ─────────────────────────────────────────────

class TestOwner:

    def test_available_minutes(self, owner):
        """07:00–20:00 should equal 780 minutes."""
        assert owner.available_minutes() == 780

    def test_invalid_time_format_raises(self):
        """Completely invalid time string should raise ValueError."""
        with pytest.raises(ValueError):
            Owner(name="Bad", available_start="7am", available_end="20:00")

    def test_get_all_tasks_empty(self, owner, mochi):
        """Owner with pet but no tasks should return empty list."""
        owner.add_pet(mochi)
        assert owner.get_all_tasks() == []

    def test_get_all_tasks_multiple_pets(self, owner, mochi, luna):
        """get_all_tasks should combine tasks from all pets."""
        mochi.add_task(Task("Walk",    30, Priority.HIGH))
        luna.add_task(Task("Brushing", 15, Priority.LOW))
        owner.add_pet(mochi)
        owner.add_pet(luna)
        all_tasks = owner.get_all_tasks()
        assert len(all_tasks) == 2


# ─────────────────────────────────────────────
# Scheduler — Sorting
# ─────────────────────────────────────────────

class TestSorting:

    def test_sort_by_time_correct_order(self, scheduler, mochi):
        """Tasks should sort morning → afternoon → evening → any."""
        mochi.add_task(Task("Evening walk", 30, Priority.LOW,    preferred_time="evening"))
        mochi.add_task(Task("Afternoon med", 5, Priority.MEDIUM, preferred_time="afternoon"))
        mochi.add_task(Task("Morning feed", 10, Priority.HIGH,   preferred_time="morning"))
        mochi.add_task(Task("Anytime task", 15, Priority.MEDIUM, preferred_time="any"))

        sorted_tasks = scheduler.sort_by_time(mochi.tasks)
        times = [t.preferred_time for t in sorted_tasks]
        assert times == ["morning", "afternoon", "evening", "any"]

    def test_sort_stable_same_slot(self, scheduler, mochi):
        """Tasks in the same time slot should all appear together."""
        mochi.add_task(Task("Walk",    30, Priority.HIGH,   preferred_time="morning"))
        mochi.add_task(Task("Feeding", 10, Priority.HIGH,   preferred_time="morning"))
        mochi.add_task(Task("Playtime",20, Priority.MEDIUM, preferred_time="afternoon"))

        sorted_tasks = scheduler.sort_by_time(mochi.tasks)
        morning_tasks = [t for t in sorted_tasks if t.preferred_time == "morning"]
        assert len(morning_tasks) == 2


# ─────────────────────────────────────────────
# Scheduler — Filtering
# ─────────────────────────────────────────────

class TestFiltering:

    def test_filter_by_pet_name(self, owner, mochi, luna):
        """filter_tasks(pet_name=) should return only that pet's tasks."""
        mochi.add_task(Task("Walk",    30, Priority.HIGH))
        luna.add_task(Task("Brushing", 15, Priority.LOW))
        owner.add_pet(mochi)
        owner.add_pet(luna)
        s = Scheduler(owner=owner, pet=mochi)

        mochi_tasks = s.filter_tasks(pet_name="Mochi")
        assert len(mochi_tasks) == 1
        assert mochi_tasks[0].title == "Walk"

    def test_filter_incomplete_only(self, scheduler, mochi):
        """filter_tasks(completed=False) should exclude done tasks."""
        t1 = Task("Walk",    30, Priority.HIGH)
        t2 = Task("Feeding", 10, Priority.HIGH)
        t1.mark_complete()
        mochi.add_task(t1)
        mochi.add_task(t2)

        incomplete = scheduler.filter_tasks(completed=False)
        assert len(incomplete) == 1
        assert incomplete[0].title == "Feeding"

    def test_filter_completed_only(self, scheduler, mochi):
        """filter_tasks(completed=True) should return only done tasks."""
        t1 = Task("Walk",    30, Priority.HIGH)
        t2 = Task("Feeding", 10, Priority.HIGH)
        t1.mark_complete()
        mochi.add_task(t1)
        mochi.add_task(t2)

        done = scheduler.filter_tasks(completed=True)
        assert len(done) == 1
        assert done[0].title == "Walk"


# ─────────────────────────────────────────────
# Scheduler — Recurring tasks
# ─────────────────────────────────────────────

class TestRecurring:

    def test_mark_task_complete_daily_adds_new(self, scheduler, mochi):
        """mark_task_complete on a daily task should add next task to pet."""
        today = date.today()
        task = Task("Feeding", 10, Priority.HIGH,
                    frequency="daily", due_date=today)
        mochi.add_task(task)
        assert len(mochi.tasks) == 1

        scheduler.mark_task_complete(mochi, task)
        assert len(mochi.tasks) == 2
        assert mochi.tasks[-1].due_date == today + timedelta(days=1)

    def test_mark_task_complete_once_no_new_task(self, scheduler, mochi):
        """mark_task_complete on a one-time task should not add a new task."""
        task = Task("Vet visit", 60, Priority.HIGH, frequency="once")
        mochi.add_task(task)
        scheduler.mark_task_complete(mochi, task)
        assert len(mochi.tasks) == 1


# ─────────────────────────────────────────────
# Scheduler — Conflict detection
# ─────────────────────────────────────────────

class TestConflictDetection:

    def _make_entry(self, title, start_str, end_str):
        """Helper to create a ScheduledTask with datetime objects."""
        fmt = "%I:%M %p"
        start_dt = datetime.strptime(start_str, fmt)
        end_dt   = datetime.strptime(end_str,   fmt)
        return ScheduledTask(
            task=Task(title, 30, Priority.HIGH),
            start_time=start_str,
            end_time=end_str,
            reason="test",
            start_dt=start_dt,
            end_dt=end_dt,
        )

    def test_no_conflict_sequential(self, scheduler):
        """Non-overlapping tasks should produce no warnings."""
        a = self._make_entry("Walk",    "07:00 AM", "07:30 AM")
        b = self._make_entry("Feeding", "07:30 AM", "07:40 AM")
        warnings = scheduler.detect_conflicts([a, b])
        assert warnings == []

    def test_conflict_exact_same_time(self, scheduler):
        """Two tasks at identical times should trigger a conflict warning."""
        a = self._make_entry("Walk",        "07:00 AM", "07:30 AM")
        b = self._make_entry("Vet appt",    "07:00 AM", "07:30 AM")
        warnings = scheduler.detect_conflicts([a, b])
        assert len(warnings) == 1
        assert "Walk" in warnings[0]
        assert "Vet appt" in warnings[0]

    def test_conflict_partial_overlap(self, scheduler):
        """Partially overlapping tasks should trigger a warning."""
        a = self._make_entry("Walk",    "07:00 AM", "07:30 AM")
        b = self._make_entry("Feeding", "07:15 AM", "07:25 AM")
        warnings = scheduler.detect_conflicts([a, b])
        assert len(warnings) == 1

    def test_no_conflict_empty_schedule(self, scheduler):
        """Empty schedule should return no warnings."""
        assert scheduler.detect_conflicts([]) == []


# ─────────────────────────────────────────────
# Scheduler — Build schedule edge cases
# ─────────────────────────────────────────────

class TestBuildSchedule:

    def test_empty_tasks_returns_empty(self, scheduler):
        """Scheduler with no tasks should return empty lists."""
        schedule, skipped = scheduler.build_schedule()
        assert schedule == []
        assert skipped == []

    def test_task_too_long_is_skipped(self):
        """A task longer than the available window should be skipped."""
        # Only 30 min available — create owner2 and add mochi to IT
        busy_owner = Owner(name="Busy", available_start="07:00", available_end="07:30")
        busy_pet   = Pet(name="Rex", species="dog")
        busy_pet.add_task(Task("Long task", 60, Priority.HIGH))
        busy_owner.add_pet(busy_pet)
        s = Scheduler(owner=busy_owner, pet=busy_pet)
        schedule, skipped = s.build_schedule()
        assert len(schedule) == 0
        assert len(skipped) == 1

    def test_high_priority_scheduled_first(self, scheduler, mochi):
        """High priority task should appear before low priority task."""
        mochi.add_task(Task("Low task",  10, Priority.LOW))
        mochi.add_task(Task("High task", 10, Priority.HIGH))
        schedule, _ = scheduler.build_schedule()
        assert schedule[0].task.title == "High task"
