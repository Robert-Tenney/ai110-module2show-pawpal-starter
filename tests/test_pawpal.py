"""
tests/test_pawpal.py
--------------------
Test suite for PawPal+ logic layer.
 
Run from the repo root with:
    python -m pytest
    python -m pytest -v          # verbose — shows each test name
    python -m pytest --cov       # with coverage report
"""
 
from datetime import date, time
 
import pytest
 
from pawpal_system import DailySchedule, Owner, Pet, Scheduler, Task, TaskDetail
 
 
# ─────────────────────────────────────────────
# Shared fixtures
# ─────────────────────────────────────────────
 
@pytest.fixture
def sample_task() -> Task:
    """A basic walk task with no detail attached."""
    return Task(
        task_type="walk",
        description="Morning walk",
        duration_min=30,
        priority="high",
    )
 
 
@pytest.fixture
def sample_pet() -> Pet:
    """A dog with no tasks yet."""
    return Pet(name="Biscuit", species="dog", breed="Golden Retriever")
 
 
@pytest.fixture
def sample_owner(sample_pet: Pet) -> Owner:
    """An owner with one pet already added."""
    owner = Owner(name="Sarah Chen", email="sarah@example.com")
    owner.add_pet(sample_pet)
    return owner
 
 
# ─────────────────────────────────────────────
# REQUIRED TEST 1 — Task completion
# ─────────────────────────────────────────────
 
class TestTaskCompletion:
    """Verify that mark_complete() / mark_incomplete() update task status."""
 
    def test_task_starts_incomplete(self, sample_task: Task) -> None:
        """A freshly created task should not be completed."""
        assert sample_task.is_completed is False
 
    def test_mark_complete_sets_flag(self, sample_task: Task) -> None:
        """Calling mark_complete() must set is_completed to True."""
        sample_task.mark_complete()
        assert sample_task.is_completed is True
 
    def test_mark_incomplete_resets_flag(self, sample_task: Task) -> None:
        """Calling mark_incomplete() after completing must reset the flag."""
        sample_task.mark_complete()
        sample_task.mark_incomplete()
        assert sample_task.is_completed is False
 
    def test_mark_complete_idempotent(self, sample_task: Task) -> None:
        """Marking complete twice should not raise and flag stays True."""
        sample_task.mark_complete()
        sample_task.mark_complete()
        assert sample_task.is_completed is True
 
 
# ─────────────────────────────────────────────
# REQUIRED TEST 2 — Task addition to a Pet
# ─────────────────────────────────────────────
 
class TestPetTaskAddition:
    """Verify that adding tasks to a Pet increases the task count."""
 
    def test_pet_starts_with_no_tasks(self, sample_pet: Pet) -> None:
        """A new pet should have an empty task list."""
        assert len(sample_pet.get_tasks()) == 0
 
    def test_adding_one_task_increases_count(
        self, sample_pet: Pet, sample_task: Task
    ) -> None:
        """After adding one task, task count must be 1."""
        sample_pet.add_task(sample_task)
        assert len(sample_pet.get_tasks()) == 1
 
    def test_adding_multiple_tasks_increases_count(self, sample_pet: Pet) -> None:
        """Adding three tasks should result in a count of 3."""
        for task_type in ("walk", "feeding", "medication"):
            sample_pet.add_task(
                Task(task_type=task_type, description=f"{task_type} task", duration_min=10)
            )
        assert len(sample_pet.get_tasks()) == 3
 
    def test_added_task_links_to_pet(self, sample_pet: Pet, sample_task: Task) -> None:
        """The task's pet_id should match the pet's pet_id after being added."""
        sample_pet.add_task(sample_task)
        assert sample_task.pet_id == sample_pet.pet_id
 
    def test_get_tasks_returns_copy(self, sample_pet: Pet, sample_task: Task) -> None:
        """Mutating the returned list should not affect the pet's internal list."""
        sample_pet.add_task(sample_task)
        returned = sample_pet.get_tasks()
        returned.clear()
        assert len(sample_pet.get_tasks()) == 1
 
 
# ─────────────────────────────────────────────
# Bonus tests — Owner & Scheduler
# ─────────────────────────────────────────────
 
class TestOwner:
    def test_owner_add_pet(self, sample_owner: Owner, sample_pet: Pet) -> None:
        """Owner should have exactly one pet (added in fixture)."""
        assert len(sample_owner.get_pets()) == 1
 
    def test_get_all_tasks_aggregates_across_pets(self, sample_owner: Owner) -> None:
        """get_all_tasks() should return tasks from all pets combined."""
        pet2 = Pet(name="Luna", species="cat")
        sample_owner.add_pet(pet2)
 
        # 2 tasks on first pet
        for label in ("walk", "feeding"):
            sample_owner.get_pets()[0].add_task(
                Task(task_type=label, description=label, duration_min=10)
            )
        # 1 task on second pet
        pet2.add_task(Task(task_type="grooming", description="brush", duration_min=10))
 
        assert len(sample_owner.get_all_tasks()) == 3
 
    def test_get_all_pending_excludes_completed(self, sample_owner: Owner, sample_pet: Pet) -> None:
        """Completed tasks should not appear in get_all_pending_tasks()."""
        t1 = Task(task_type="walk",    description="walk",  duration_min=30)
        t2 = Task(task_type="feeding", description="feed",  duration_min=10)
        sample_pet.add_task(t1)
        sample_pet.add_task(t2)
        t1.mark_complete()
 
        pending = sample_owner.get_all_pending_tasks()
        assert len(pending) == 1
        assert pending[0].task_type == "feeding"
 
 
class TestScheduler:
    def test_build_schedule_contains_pet_tasks(
        self, sample_pet: Pet, sample_task: Task
    ) -> None:
        """A built schedule should include all tasks added to the pet."""
        sample_task.set_detail(scheduled_time=time(8, 0))
        sample_pet.add_task(sample_task)
 
        scheduler = Scheduler()
        sched = scheduler.build_schedule_for_pet(sample_pet, on_date=date.today())
        assert len(sched.tasks) == 1
 
    def test_generate_plan_respects_time_budget(self, sample_pet: Pet) -> None:
        """Tasks whose total duration exceeds the budget should be dropped."""
        for i in range(5):
            t = Task(
                task_type="walk",
                description=f"walk {i}",
                duration_min=60,
                priority="medium",
            )
            t.set_detail(scheduled_time=time(i + 6, 0))
            sample_pet.add_task(t)
 
        scheduler = Scheduler()
        sched = scheduler.build_schedule_for_pet(
            sample_pet, on_date=date.today(), time_budget_min=120
        )
        plan = sched.generate_plan()
        total = sum(t.duration_min for t in plan)
        assert total <= 120
 
    def test_generate_plan_high_priority_first(self, sample_pet: Pet) -> None:
        """High-priority tasks should appear before low-priority ones in the plan."""
        low = Task(task_type="grooming", description="groom", duration_min=10, priority="low")
        low.set_detail(scheduled_time=time(7, 0))   # earlier time, lower priority
        high = Task(task_type="medication", description="meds", duration_min=5, priority="high")
        high.set_detail(scheduled_time=time(9, 0))
 
        sample_pet.add_task(low)
        sample_pet.add_task(high)
 
        scheduler = Scheduler()
        sched = scheduler.build_schedule_for_pet(sample_pet, on_date=date.today())
        plan = sched.generate_plan()
 
        assert plan[0].priority == "high"
        assert plan[1].priority == "low"