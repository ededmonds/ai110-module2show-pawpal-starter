"""
PawPal+ Logic Layer
--------------------
All backend classes for the pet care scheduling system.
Four core classes:
  - Task       : a care activity with duration, priority, and recurrence
  - Pet        : the animal being cared for (owns its tasks)
  - Owner      : the person responsible for care (owns pets, provides all tasks)
  - Scheduler  : builds, sorts, filters, and validates a daily care plan

ScheduledTask is a result object returned by Scheduler.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timedelta, date
from enum import IntEnum
from collections import defaultdict, deque
import heapq


# ─────────────────────────────────────────────
# Priority Enum
# ─────────────────────────────────────────────

class Priority(IntEnum):
    LOW    = 1
    MEDIUM = 2
    HIGH   = 3

    @classmethod
    def from_str(cls, label: str) -> "Priority":
        """Convert a string label like 'high' to the matching Priority enum value."""
        return cls[label.upper()]


# ─────────────────────────────────────────────
# Task
# ─────────────────────────────────────────────

@dataclass
class Task:
    """
    Represents a single pet care activity.

    Attributes:
        title            : human-readable name (e.g. "Morning walk")
        duration_minutes : how long the task takes
        priority         : Priority enum value (HIGH, MEDIUM, LOW)
        preferred_time   : "morning", "afternoon", "evening", or "any"
        notes            : optional extra context
        completed        : whether the task has been done
        frequency        : "once", "daily", or "weekly"
        due_date         : optional date the task is due
    """
    title: str
    duration_minutes: int
    priority: Priority
    preferred_time: str = "any"
    notes: str = ""
    completed: bool = False
    frequency: str = "once"
    due_date: Optional[date] = None

    def priority_value(self) -> int:
        """Return the numeric priority rank used for heap sorting."""
        return int(self.priority)

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task done; return a new Task for next occurrence if recurring."""
        self.completed = True
        base_date = self.due_date or date.today()
        if self.frequency == "daily":
            return Task(
                title=self.title,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                preferred_time=self.preferred_time,
                notes=self.notes,
                frequency=self.frequency,
                due_date=base_date + timedelta(days=1),
            )
        if self.frequency == "weekly":
            return Task(
                title=self.title,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                preferred_time=self.preferred_time,
                notes=self.notes,
                frequency=self.frequency,
                due_date=base_date + timedelta(weeks=1),
            )
        return None

    def __lt__(self, other: "Task") -> bool:
        """Compare tasks by duration so heapq can break priority ties."""
        return self.duration_minutes < other.duration_minutes


# ─────────────────────────────────────────────
# Pet
# ─────────────────────────────────────────────

@dataclass
class Pet:
    """
    Represents the pet being cared for.

    Attributes:
        name          : pet's name
        species       : "dog", "cat", or "other"
        age           : age in years
        special_needs : any medical or behavioral notes
        tasks         : list of Task objects assigned to this pet
    """
    name: str
    species: str
    age: int = 1
    special_needs: str = ""
    tasks: List[Task] = field(default_factory=list)

    def species_emoji(self) -> str:
        """Return a species-appropriate emoji for display purposes."""
        return {"dog": "🐶", "cat": "🐱"}.get(self.species, "🐾")

    def add_task(self, task: Task) -> None:
        """Append a Task to this pet's task list."""
        self.tasks.append(task)


# ─────────────────────────────────────────────
# Owner
# ─────────────────────────────────────────────

@dataclass
class Owner:
    """
    Represents the pet owner and their availability.

    Attributes:
        name            : owner's name
        available_start : start of free time in "HH:MM" format
        available_end   : end of free time in "HH:MM" format
        preferences     : freeform notes about scheduling preferences
        pets            : list of Pet objects this owner is responsible for
    """
    name: str
    available_start: str = "07:00"
    available_end: str = "20:00"
    preferences: str = ""
    pets: List[Pet] = field(default_factory=list)

    def __post_init__(self):
        """Validate that available_start and available_end are in HH:MM format."""
        try:
            datetime.strptime(self.available_start, "%H:%M")
            datetime.strptime(self.available_end,   "%H:%M")
        except ValueError:
            raise ValueError(
                "available_start and available_end must be HH:MM format (e.g. '07:00')"
            )

    def available_minutes(self) -> int:
        """Calculate total available minutes between start and end times."""
        start = datetime.strptime(self.available_start, "%H:%M")
        end   = datetime.strptime(self.available_end,   "%H:%M")
        return int((end - start).total_seconds() / 60)

    def add_pet(self, pet: Pet) -> None:
        """Append a Pet to this owner's list of pets."""
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Task]:
        """Collect and return every task from every pet this owner manages."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks


# ─────────────────────────────────────────────
# ScheduledTask  (result object)
# ─────────────────────────────────────────────

@dataclass
class ScheduledTask:
    """
    A Task that has been placed on the schedule.

    Attributes:
        task       : the original Task object
        start_time : formatted start time string (e.g. "07:00 AM")
        end_time   : formatted end time string
        reason     : explanation of why/when this task was scheduled
        start_dt   : raw datetime for conflict checking
        end_dt     : raw datetime for conflict checking
    """
    task: Task
    start_time: str
    end_time: str
    reason: str
    start_dt: datetime = field(default=None)
    end_dt: datetime   = field(default=None)


# ─────────────────────────────────────────────
# Scheduler
# ─────────────────────────────────────────────

class Scheduler:
    """
    Builds, sorts, filters, and validates a daily care schedule.

    Attributes:
        owner   : the Owner whose time window and pets are used
        pet     : the primary pet being scheduled for
        history : deque of past schedule results (max 10)
    """

    # Time-of-day ordering for sort_by_time
    TIME_ORDER = {"morning": 0, "afternoon": 1, "evening": 2, "any": 3}

    def __init__(self, owner: Owner, pet: Pet):
        self.owner = owner
        self.pet = pet
        self.history: deque = deque(maxlen=10)

    # ── Core scheduling ──────────────────────────────────────

    def build_schedule(self):
        """Pull tasks from owner, sort via heap, and fit them into the available window."""
        tasks = self.owner.get_all_tasks()
        if not tasks:
            return [], []

        heap = self._build_heap(tasks)
        schedule: List[ScheduledTask] = []
        skipped:  List[Task]          = []

        current = datetime.strptime(self.owner.available_start, "%H:%M")
        end_day = datetime.strptime(self.owner.available_end,   "%H:%M")

        while heap:
            _, _, task = heapq.heappop(heap)
            end = current + timedelta(minutes=task.duration_minutes)

            if end > end_day:
                skipped.append(task)
                continue

            schedule.append(ScheduledTask(
                task=task,
                start_time=current.strftime("%I:%M %p"),
                end_time=end.strftime("%I:%M %p"),
                reason=self._explain(task, current),
                start_dt=current,
                end_dt=end,
            ))
            current = end

        self.history.appendleft(schedule)
        return schedule, skipped

    # ── Sorting ──────────────────────────────────────────────

    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by preferred_time slot: morning → afternoon → evening → any."""
        return sorted(
            tasks,
            key=lambda t: self.TIME_ORDER.get(t.preferred_time, 3)
        )

    # ── Filtering ────────────────────────────────────────────

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> List[Task]:
        """Filter owner's tasks by pet name and/or completion status."""
        if pet_name:
            tasks = [
                t
                for pet in self.owner.pets
                if pet.name == pet_name
                for t in pet.tasks
            ]
        else:
            tasks = self.owner.get_all_tasks()

        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]

        return tasks

    # ── Recurring tasks ──────────────────────────────────────

    def mark_task_complete(self, pet: Pet, task: Task) -> None:
        """Mark a task complete and auto-add the next occurrence if it recurs."""
        next_task = task.mark_complete()
        if next_task:
            pet.add_task(next_task)

    # ── Conflict detection ───────────────────────────────────

    def detect_conflicts(self, schedule: List[ScheduledTask]) -> List[str]:
        """Return warning strings for any overlapping tasks in the schedule."""
        warnings = []
        for i in range(len(schedule)):
            for j in range(i + 1, len(schedule)):
                a, b = schedule[i], schedule[j]
                if a.start_dt and b.start_dt:
                    if a.start_dt < b.end_dt and b.start_dt < a.end_dt:
                        warnings.append(
                            f"⚠️  Conflict: '{a.task.title}' "
                            f"({a.start_time} – {a.end_time}) overlaps with "
                            f"'{b.task.title}' ({b.start_time} – {b.end_time})"
                        )
        return warnings

    # ── Private helpers ──────────────────────────────────────

    def _build_heap(self, tasks: List[Task]) -> list:
        """Build a max-priority min-heap from the task list for ordered scheduling."""
        heap = []
        for task in tasks:
            heapq.heappush(heap, (-task.priority_value(), task.duration_minutes, task))
        return heap

    def _group_by_time(self, tasks: List[Task]) -> defaultdict:
        """Group tasks into a dict keyed by preferred time slot."""
        groups = defaultdict(list)
        for task in tasks:
            groups[task.preferred_time].append(task)
        return groups

    def _explain(self, task: Task, start_time: datetime) -> str:
        """Generate a plain-English explanation of why a task was scheduled at a given time."""
        hour = start_time.hour
        time_label = (
            "morning" if hour < 12
            else "afternoon" if hour < 17
            else "evening"
        )
        base = f"Scheduled at {start_time.strftime('%I:%M %p')} ({time_label}) "
        if task.priority == Priority.HIGH:
            base += "because it is a high-priority task and placed first."
        elif task.priority == Priority.MEDIUM:
            base += "after all high-priority tasks are handled."
        else:
            base += "as a low-priority task, fitted into remaining time."
        if task.notes:
            base += f" Note: {task.notes}"
        return base
