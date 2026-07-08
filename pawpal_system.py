"""
PawPal+ Logic Layer
--------------------
All backend classes for the pet care scheduling system.
Four core classes:
  - Task       : a care activity with duration and priority
  - Pet        : the animal being cared for (owns its tasks)
  - Owner      : the person responsible for care (owns pets, provides all tasks)
  - Scheduler  : builds and explains a daily care plan

ScheduledTask is a result object returned by Scheduler.
"""

from dataclasses import dataclass, field
from typing import List
from datetime import datetime, timedelta
from enum import IntEnum
from collections import defaultdict, deque
import heapq


# ─────────────────────────────────────────────
# Priority Enum  (replaces magic string dict)
# ─────────────────────────────────────────────

class Priority(IntEnum):
    LOW    = 1
    MEDIUM = 2
    HIGH   = 3

    @classmethod
    def from_str(cls, label: str) -> "Priority":
        """Convert 'high'/'medium'/'low' string to Priority enum."""
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
    """
    title: str
    duration_minutes: int
    priority: Priority
    preferred_time: str = "any"
    notes: str = ""

    def priority_value(self) -> int:
        """Return numeric rank for sorting (HIGH=3, MEDIUM=2, LOW=1)."""
        return int(self.priority)

    def __lt__(self, other: "Task") -> bool:
        """Enable heapq comparison — shorter duration wins on tie."""
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
        """Return an emoji representing the species."""
        return {"dog": "🐶", "cat": "🐱"}.get(self.species, "🐾")

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet."""
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
        """Validate time format on creation."""
        try:
            datetime.strptime(self.available_start, "%H:%M")
            datetime.strptime(self.available_end, "%H:%M")
        except ValueError:
            raise ValueError("available_start and available_end must be in HH:MM format (e.g. '07:00')")

    def available_minutes(self) -> int:
        """Return total available minutes between start and end."""
        start = datetime.strptime(self.available_start, "%H:%M")
        end   = datetime.strptime(self.available_end,   "%H:%M")
        return int((end - start).total_seconds() / 60)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's care list."""
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Task]:
        """
        Collect every task from every pet this owner has.
        Scheduler calls this instead of receiving tasks directly.
        """
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
    """
    task: Task
    start_time: str
    end_time: str
    reason: str


# ─────────────────────────────────────────────
# Scheduler
# ─────────────────────────────────────────────

class Scheduler:
    """
    Builds a daily care schedule for a pet given an owner's availability.

    Scheduling strategy:
      1. Pull all tasks from owner.get_all_tasks()
      2. Group by preferred_time using _group_by_time()
      3. Build a heapq priority queue via _build_heap()
      4. Place tasks sequentially; skip any that exceed available_end
      5. Store results in history deque (max 10 sessions)

    Attributes:
        owner   : the Owner whose time window and pets are used
        pet     : the primary pet being scheduled for
        history : deque of past schedule results (max 10)
    """

    def __init__(self, owner: Owner, pet: Pet):
        self.owner = owner
        self.pet = pet
        self.history: deque = deque(maxlen=10)

    def build_schedule(self):
        """
        Pull tasks from owner, sort via heap, fit into available window.

        Returns:
            schedule : List[ScheduledTask] — tasks that were placed
            skipped  : List[Task]          — tasks that didn't fit
        """
        tasks = self.owner.get_all_tasks()
        if not tasks:
            return [], []

        heap = self._build_heap(tasks)
        time_groups = self._group_by_time(tasks)

        schedule: List[ScheduledTask] = []
        skipped: List[Task] = []

        current  = datetime.strptime(self.owner.available_start, "%H:%M")
        end_day  = datetime.strptime(self.owner.available_end,   "%H:%M")

        while heap:
            _, _, task = heapq.heappop(heap)
            end = current + timedelta(minutes=task.duration_minutes)

            if end > end_day:
                skipped.append(task)
                continue

            reason = self._explain(task, current)
            schedule.append(ScheduledTask(
                task=task,
                start_time=current.strftime("%I:%M %p"),
                end_time=end.strftime("%I:%M %p"),
                reason=reason,
            ))
            current = end

        self.history.appendleft(schedule)
        return schedule, skipped

    def _build_heap(self, tasks: List[Task]) -> list:
        """
        Build a min-heap ordered by descending priority,
        then ascending duration on ties.

        Returns:
            list — heapified list of (-priority, duration, task) tuples
        """
        heap = []
        for task in tasks:
            heapq.heappush(heap, (-task.priority_value(), task.duration_minutes, task))
        return heap

    def _group_by_time(self, tasks: List[Task]) -> defaultdict:
        """
        Group tasks by their preferred_time slot.

        Returns:
            defaultdict(list) keyed by "morning"/"afternoon"/"evening"/"any"
        """
        groups = defaultdict(list)
        for task in tasks:
            groups[task.preferred_time].append(task)
        return groups

    def _explain(self, task: Task, start_time: datetime) -> str:
        """
        Generate a human-readable reason for why this task
        was scheduled at the given time.

        Returns:
            str — explanation sentence
        """
        hour = start_time.hour
        time_label = (
            "morning"   if hour < 12
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