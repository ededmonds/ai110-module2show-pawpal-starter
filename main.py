"""
main.py — PawPal+ Testing Ground
Run: python main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler, Priority


def print_schedule(schedule, skipped, owner, pet):
    width = 60
    print("=" * width)
    print(f"  🐾 PawPal+ Daily Schedule")
    print(f"  Owner : {owner.name}")
    print(f"  Pet   : {pet.species_emoji()} {pet.name} (age {pet.age})")
    print(f"  Hours : {owner.available_start} – {owner.available_end}")
    print("=" * width)

    if not schedule:
        print("  No tasks could be scheduled.")
    else:
        for i, entry in enumerate(schedule, start=1):
            priority_icon = {
                Priority.HIGH:   "🔴",
                Priority.MEDIUM: "🟡",
                Priority.LOW:    "🟢",
            }.get(entry.task.priority, "  ")

            print(f"\n  {i}. {priority_icon} {entry.task.title}")
            print(f"     Time     : {entry.start_time} → {entry.end_time}")
            print(f"     Duration : {entry.task.duration_minutes} min")
            print(f"     Priority : {entry.task.priority.name.capitalize()}")
            if entry.task.notes:
                print(f"     Notes    : {entry.task.notes}")
            print(f"     Why      : {entry.reason}")

    if skipped:
        print("\n" + "-" * width)
        print("  ⚠️  Tasks that didn't fit:")
        for t in skipped:
            print(f"     - {t.title} ({t.duration_minutes} min, {t.priority.name.capitalize()})")

    print("=" * width)
    total = sum(e.task.duration_minutes for e in schedule)
    available = owner.available_minutes()
    print(f"  ✅ {len(schedule)} task(s) scheduled  |  "
          f"⏱ {total} / {available} min used")
    print("=" * width)


def main():
    # ── Create Owner ──
    jordan = Owner(
        name="Jordan",
        available_start="07:00",
        available_end="20:00",
        preferences="Prefer morning walks",
    )

    # ── Create Pets ──
    mochi = Pet(name="Mochi", species="dog", age=3,
                special_needs="Needs harness for walks")
    luna  = Pet(name="Luna",  species="cat", age=5,
                special_needs="")

    # ── Add Tasks to Mochi (dog) ──
    mochi.add_task(Task(
        title="Morning walk",
        duration_minutes=30,
        priority=Priority.HIGH,
        preferred_time="morning",
        notes="Use harness",
    ))
    mochi.add_task(Task(
        title="Feeding",
        duration_minutes=10,
        priority=Priority.HIGH,
        preferred_time="morning",
    ))
    mochi.add_task(Task(
        title="Playtime",
        duration_minutes=20,
        priority=Priority.MEDIUM,
        preferred_time="afternoon",
    ))

    # ── Add Tasks to Luna (cat) ──
    luna.add_task(Task(
        title="Litter box cleaning",
        duration_minutes=10,
        priority=Priority.HIGH,
        preferred_time="morning",
    ))
    luna.add_task(Task(
        title="Brushing",
        duration_minutes=15,
        priority=Priority.LOW,
        preferred_time="evening",
        notes="Luna is sensitive around ears",
    ))

    # ── Register Pets with Owner ──
    jordan.add_pet(mochi)
    jordan.add_pet(luna)

    # ── Run Scheduler ──
    scheduler = Scheduler(owner=jordan, pet=mochi)
    schedule, skipped = scheduler.build_schedule()

    # ── Print Results ──
    print_schedule(schedule, skipped, jordan, mochi)


if __name__ == "__main__":
    main()
