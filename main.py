"""
main.py — PawPal+ Testing Ground
Run: python main.py
Demos: sorting, filtering, recurring tasks, conflict detection
"""

from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler, Priority, ScheduledTask


def divider(title=""):
    print("\n" + "=" * 60)
    if title:
        print(f"  {title}")
        print("=" * 60)


def print_tasks(tasks, label="Tasks"):
    print(f"\n  [{label}]")
    if not tasks:
        print("  (none)")
        return
    for t in tasks:
        icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(t.priority.name, "")
        status = "✅" if t.completed else "⬜"
        recur  = f" [{t.frequency}]" if t.frequency != "once" else ""
        due    = f" due {t.due_date}" if t.due_date else ""
        print(f"  {status} {icon} {t.title} "
              f"({t.duration_minutes}min, {t.preferred_time}){recur}{due}")


def print_schedule(schedule, skipped):
    if not schedule:
        print("  No tasks scheduled.")
        return
    for i, e in enumerate(schedule, 1):
        icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(e.task.priority.name, "")
        print(f"  {i}. {icon} {e.task.title:<25} {e.start_time} → {e.end_time}")
    if skipped:
        print(f"\n  ⚠️  Skipped (didn't fit): {', '.join(t.title for t in skipped)}")


def main():
    # ── Setup ──────────────────────────────────────────────────
    jordan = Owner(name="Jordan", available_start="07:00", available_end="20:00")
    mochi  = Pet(name="Mochi", species="dog", age=3)
    luna   = Pet(name="Luna",  species="cat", age=5)

    # Add tasks OUT OF ORDER (evening first, then morning, then afternoon)
    mochi.add_task(Task("Evening walk",   30, Priority.MEDIUM, preferred_time="evening"))
    mochi.add_task(Task("Morning walk",   30, Priority.HIGH,   preferred_time="morning",
                        frequency="daily", due_date=date.today()))
    mochi.add_task(Task("Playtime",       20, Priority.MEDIUM, preferred_time="afternoon"))
    mochi.add_task(Task("Feeding",        10, Priority.HIGH,   preferred_time="morning",
                        frequency="daily", due_date=date.today()))

    luna.add_task(Task("Litter cleaning", 10, Priority.HIGH,   preferred_time="morning"))
    luna.add_task(Task("Brushing",        15, Priority.LOW,    preferred_time="evening",
                       notes="Sensitive around ears"))

    jordan.add_pet(mochi)
    jordan.add_pet(luna)

    scheduler = Scheduler(owner=jordan, pet=mochi)

    # ── 1. Sorting ─────────────────────────────────────────────
    divider("1. SORT BY TIME  (morning → afternoon → evening → any)")
    all_tasks = jordan.get_all_tasks()
    print_tasks(all_tasks, "Unsorted")
    sorted_tasks = scheduler.sort_by_time(all_tasks)
    print_tasks(sorted_tasks, "Sorted by preferred time")

    # ── 2. Filtering ───────────────────────────────────────────
    divider("2. FILTERING")
    mochi_tasks = scheduler.filter_tasks(pet_name="Mochi")
    print_tasks(mochi_tasks, "Mochi's tasks only")

    incomplete = scheduler.filter_tasks(completed=False)
    print_tasks(incomplete, "All incomplete tasks")

    # ── 3. Recurring tasks ─────────────────────────────────────
    divider("3. RECURRING TASKS")
    feeding = next(t for t in mochi.tasks if t.title == "Feeding")
    print(f"\n  Before: '{feeding.title}' completed={feeding.completed}, "
          f"due={feeding.due_date}, frequency={feeding.frequency}")

    scheduler.mark_task_complete(mochi, feeding)

    print(f"  After:  '{feeding.title}' completed={feeding.completed}")
    new_feeding = mochi.tasks[-1]
    print(f"  Next:   '{new_feeding.title}' completed={new_feeding.completed}, "
          f"due={new_feeding.due_date}  ← auto-created by mark_task_complete()")

    # ── 4. Build schedule & conflict detection ─────────────────
    divider("4. SCHEDULE + CONFLICT DETECTION")
    schedule, skipped = scheduler.build_schedule()
    print_schedule(schedule, skipped)

    # Inject a manual conflict to test detection
    if len(schedule) >= 2:
        fake_conflict = ScheduledTask(
            task=Task("Vet appointment", 30, Priority.HIGH),
            start_time=schedule[0].start_time,
            end_time=schedule[0].end_time,
            reason="Manual conflict test",
            start_dt=schedule[0].start_dt,
            end_dt=schedule[0].end_dt,
        )
        test_schedule = schedule + [fake_conflict]
        conflicts = scheduler.detect_conflicts(test_schedule)
        if conflicts:
            print("\n  Conflict detection results:")
            for w in conflicts:
                print(f"  {w}")
        else:
            print("\n  No conflicts detected.")

    # ── 5. Filter completed after scheduling ───────────────────
    divider("5. FILTER COMPLETED (after marking Feeding done)")
    done = scheduler.filter_tasks(completed=True)
    print_tasks(done, "Completed tasks")

    divider("Done")
    print()


if __name__ == "__main__":
    main()
