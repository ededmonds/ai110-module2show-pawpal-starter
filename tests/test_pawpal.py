# test_pawpal.py

from pawpal_system import Task, Pet, Priority


def test_mark_complete():
    """Verify mark_complete() changes task status to True."""
    task = Task(
        title="Morning walk",
        duration_minutes=30,
        priority=Priority.HIGH,
    )
    assert task.completed == False
    task.mark_complete()
    assert task.completed == True
    print("✅ test_mark_complete passed")


def test_add_task_increases_count():
    """Verify adding a task to a Pet increases its task count."""
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task(
        title="Feeding",
        duration_minutes=10,
        priority=Priority.HIGH,
    ))
    assert len(pet.tasks) == 1

    pet.add_task(Task(
        title="Playtime",
        duration_minutes=20,
        priority=Priority.MEDIUM,
    ))
    assert len(pet.tasks) == 2
    print("✅ test_add_task_increases_count passed")


if __name__ == "__main__":
    test_mark_complete()