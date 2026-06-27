"""
tests/test_pawpal.py
--------------------
Automated test suite for PawPal+ logic layer.

Covers
------
  - Task completion (happy path + edge cases)
  - Task addition to a Pet
  - Sorting correctness (sort_by_time)
  - Recurrence logic (daily and weekly)
  - Conflict detection (flagged and clean)
  - Filtering (by pet, by status, combined)
  - Owner task aggregation
  - Scheduler plan generation (priority + time budget)
  - Edge cases: no tasks, no detail, one-off tasks

Run from the repo root with:
    python -m pytest
    python -m pytest -v
    python -m pytest --cov
"""

from datetime import date, time, timedelta

import pytest

from pawpal_system import (
    Conflict,
    DailySchedule,
    Owner,
    Pet,
    Scheduler,
    Task,
    TaskDetail,
)


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

@pytest.fixture
def sample_task() -> Task:
    """A basic recurring daily walk task — no TaskDetail attached."""
    return Task(
        task_type="walk",
        description="Morning walk",
        duration_min=30,
        priority="high",
        is_recurring=True,
        frequency="daily",
    )


@pytest.fixture
def sample_pet() -> Pet:
    """A dog with no tasks yet."""
    return Pet(name="Biscuit", species="dog", breed="Golden Retriever")


@pytest.fixture
def sample_owner(sample_pet: Pet) -> Owner:
    """An owner with one pet (Biscuit) already registered."""
    owner = Owner(name="Sarah Chen", email="sarah@example.com")
    owner.add_pet(sample_pet)
    return owner


@pytest.fixture
def scheduler() -> Scheduler:
    """A fresh Scheduler instance."""
    return Scheduler()


# ─────────────────────────────────────────────
# Task Completion
# ─────────────────────────────────────────────

class TestTaskCompletion:
    """Happy path and edge cases for mark_complete / mark_incomplete."""

    def test_task_starts_incomplete(self, sample_task):
        assert sample_task.is_completed is False

    def test_mark_complete_sets_flag(self, sample_task):
        sample_task.mark_complete()
        assert sample_task.is_completed is True

    def test_mark_incomplete_resets_flag(self, sample_task):
        sample_task.mark_complete()
        sample_task.mark_incomplete()
        assert sample_task.is_completed is False

    def test_mark_complete_twice_stays_true(self, sample_task):
        """Idempotent — calling twice should not raise or flip the flag."""
        sample_task.mark_complete()
        sample_task.mark_complete()
        assert sample_task.is_completed is True


# ─────────────────────────────────────────────
# Pet Task Management
# ─────────────────────────────────────────────

class TestPetTaskManagement:
    """Adding, removing, and retrieving tasks on a Pet."""

    def test_new_pet_has_no_tasks(self, sample_pet):
        assert len(sample_pet.get_tasks()) == 0

    def test_adding_one_task_increases_count(self, sample_pet, sample_task):
        sample_pet.add_task(sample_task)
        assert len(sample_pet.get_tasks()) == 1

    def test_adding_three_tasks_counts_correctly(self, sample_pet):
        for tt in ("walk", "feeding", "medication"):
            sample_pet.add_task(Task(task_type=tt, description=tt, duration_min=10))
        assert len(sample_pet.get_tasks()) == 3

    def test_added_task_pet_id_matches(self, sample_pet, sample_task):
        sample_pet.add_task(sample_task)
        assert sample_task.pet_id == sample_pet.pet_id

    def test_get_tasks_returns_copy(self, sample_pet, sample_task):
        """Mutating the returned list must not affect the pet's internal state."""
        sample_pet.add_task(sample_task)
        sample_pet.get_tasks().clear()
        assert len(sample_pet.get_tasks()) == 1

    def test_remove_task_decreases_count(self, sample_pet, sample_task):
        sample_pet.add_task(sample_task)
        removed = sample_pet.remove_task(sample_task.task_id)
        assert removed is True
        assert len(sample_pet.get_tasks()) == 0

    def test_remove_nonexistent_task_returns_false(self, sample_pet):
        assert sample_pet.remove_task("fake-id-999") is False

    def test_get_pending_excludes_completed(self, sample_pet):
        t1 = Task(task_type="walk",    description="walk", duration_min=30)
        t2 = Task(task_type="feeding", description="feed", duration_min=10)
        sample_pet.add_task(t1)
        sample_pet.add_task(t2)
        t1.mark_complete()
        pending = sample_pet.get_pending_tasks()
        assert len(pending) == 1
        assert pending[0].task_type == "feeding"


# ─────────────────────────────────────────────
# Sorting — sort_by_time
# ─────────────────────────────────────────────

class TestSortByTime:
    """Verify sort_by_time returns tasks in chronological order."""

    def test_tasks_sorted_chronologically(self, sample_pet, scheduler):
        """Tasks added out of order must come back in time order."""
        times = [time(18, 0), time(7, 30), time(12, 0), time(8, 0)]
        for i, t in enumerate(times):
            task = Task(task_type="task", description=f"task {i}", duration_min=10)
            task.set_detail(scheduled_time=t)
            sample_pet.add_task(task)

        sorted_tasks = scheduler.sort_by_time(sample_pet.get_tasks())
        result_times = [t.detail.scheduled_time for t in sorted_tasks]
        assert result_times == sorted(times)

    def test_task_without_detail_sorts_last(self, sample_pet, scheduler):
        """A task with no detail (no scheduled time) must appear at the end."""
        early = Task(task_type="walk", description="early", duration_min=10)
        early.set_detail(scheduled_time=time(6, 0))
        no_time = Task(task_type="misc", description="no time", duration_min=5)

        sample_pet.add_task(no_time)    # added first
        sample_pet.add_task(early)

        sorted_tasks = scheduler.sort_by_time(sample_pet.get_tasks())
        assert sorted_tasks[0].description == "early"
        assert sorted_tasks[-1].description == "no time"

    def test_sort_does_not_mutate_original(self, sample_pet, scheduler):
        """sort_by_time must return a new list, not sort in place."""
        t1 = Task(task_type="walk",    description="late",  duration_min=10)
        t2 = Task(task_type="feeding", description="early", duration_min=10)
        t1.set_detail(scheduled_time=time(18, 0))
        t2.set_detail(scheduled_time=time(7,  0))
        sample_pet.add_task(t1)
        sample_pet.add_task(t2)

        original_order = [t.description for t in sample_pet.get_tasks()]
        scheduler.sort_by_time(sample_pet.get_tasks())
        assert [t.description for t in sample_pet.get_tasks()] == original_order

    def test_empty_list_sorts_cleanly(self, scheduler):
        """sort_by_time on an empty list must return an empty list, not raise."""
        assert scheduler.sort_by_time([]) == []

    def test_single_task_sorts_cleanly(self, scheduler, sample_task):
        """sort_by_time on a one-element list must return that element."""
        sample_task.set_detail(scheduled_time=time(9, 0))
        result = scheduler.sort_by_time([sample_task])
        assert len(result) == 1


# ─────────────────────────────────────────────
# Recurrence Logic
# ─────────────────────────────────────────────

class TestRecurrenceLogic:
    """Confirm recurring tasks auto-create the correct next occurrence."""

    def test_daily_task_creates_next_day(self, sample_pet, scheduler):
        """Completing a daily task must produce a new task due tomorrow."""
        today = date.today()
        task = Task(
            task_type="walk", description="Morning walk",
            duration_min=30, is_recurring=True, frequency="daily",
            due_date=today,
        )
        task.set_detail(scheduled_time=time(7, 30))
        sample_pet.add_task(task)

        next_task = scheduler.complete_and_reschedule(task, sample_pet)

        assert next_task is not None
        assert next_task.due_date == today + timedelta(days=1)

    def test_weekly_task_creates_next_week(self, sample_pet, scheduler):
        """Completing a weekly task must produce a new task due in 7 days."""
        today = date.today()
        task = Task(
            task_type="grooming", description="Bath time",
            duration_min=20, is_recurring=True, frequency="weekly",
            due_date=today,
        )
        task.set_detail(scheduled_time=time(14, 0))
        sample_pet.add_task(task)

        next_task = scheduler.complete_and_reschedule(task, sample_pet)

        assert next_task is not None
        assert next_task.due_date == today + timedelta(weeks=1)

    def test_recurring_task_inherits_same_time(self, sample_pet, scheduler):
        """The cloned next-occurrence task must keep the same scheduled time."""
        task = Task(
            task_type="medication", description="Allergy tablet",
            duration_min=5, is_recurring=True, frequency="daily",
        )
        task.set_detail(scheduled_time=time(8, 5), notes="10 mg Apoquel")
        sample_pet.add_task(task)

        next_task = scheduler.complete_and_reschedule(task, sample_pet)

        assert next_task.detail is not None
        assert next_task.detail.scheduled_time == time(8, 5)

    def test_non_recurring_task_returns_none(self, sample_pet, scheduler):
        """Completing a one-off task must return None — no clone created."""
        task = Task(
            task_type="vet visit", description="Annual checkup",
            duration_min=60, is_recurring=False,
        )
        sample_pet.add_task(task)

        next_task = scheduler.complete_and_reschedule(task, sample_pet)
        assert next_task is None

    def test_recurring_task_marked_complete_after_reschedule(self, sample_pet, scheduler):
        """After complete_and_reschedule the original task must be done."""
        task = Task(
            task_type="walk", description="walk",
            duration_min=30, is_recurring=True, frequency="daily",
        )
        sample_pet.add_task(task)
        scheduler.complete_and_reschedule(task, sample_pet)
        assert task.is_completed is True

    def test_next_occurrence_added_to_pet(self, sample_pet, scheduler):
        """complete_and_reschedule must register the new task on the pet."""
        task = Task(
            task_type="feeding", description="Breakfast",
            duration_min=10, is_recurring=True, frequency="daily",
        )
        sample_pet.add_task(task)
        count_before = len(sample_pet.get_tasks())

        scheduler.complete_and_reschedule(task, sample_pet)

        assert len(sample_pet.get_tasks()) == count_before + 1


# ─────────────────────────────────────────────
# Conflict Detection
# ─────────────────────────────────────────────

class TestConflictDetection:
    """Verify detect_conflicts catches duplicate times and ignores clean schedules."""

    def _make_schedule(self, pet: Pet) -> DailySchedule:
        return DailySchedule(
            pet_id=pet.pet_id,
            pet_name=pet.name,
            date=date.today(),
        )

    def test_no_conflicts_on_clean_schedule(self, sample_pet, scheduler):
        """Distinct times must produce an empty conflict list."""
        sched = self._make_schedule(sample_pet)
        for i, t in enumerate([time(7, 0), time(8, 0), time(9, 0)]):
            task = Task(task_type="task", description=f"task {i}", duration_min=10)
            task.set_detail(scheduled_time=t)
            sched.add_task(task)

        assert scheduler.detect_conflicts(sched) == []

    def test_duplicate_time_raises_conflict(self, sample_pet, scheduler):
        """Two tasks at the exact same time must produce one Conflict."""
        sched = self._make_schedule(sample_pet)

        t1 = Task(task_type="feeding",  description="Breakfast", duration_min=10)
        t2 = Task(task_type="vet_call", description="Call vet",  duration_min=10)
        t1.set_detail(scheduled_time=time(8, 0))
        t2.set_detail(scheduled_time=time(8, 0))    # ← same time

        sched.add_task(t1)
        sched.add_task(t2)

        conflicts = scheduler.detect_conflicts(sched)
        assert len(conflicts) == 1
        assert isinstance(conflicts[0], Conflict)

    def test_conflict_message_contains_pet_name(self, sample_pet, scheduler):
        """The conflict warning must mention the pet's name."""
        sched = self._make_schedule(sample_pet)

        for desc in ("Task A", "Task B"):
            task = Task(task_type="misc", description=desc, duration_min=10)
            task.set_detail(scheduled_time=time(10, 0))
            sched.add_task(task)

        conflicts = scheduler.detect_conflicts(sched)
        assert sample_pet.name in conflicts[0].message()

    def test_tasks_without_detail_skipped(self, sample_pet, scheduler):
        """Tasks with no scheduled time must not trigger a false conflict."""
        sched = self._make_schedule(sample_pet)

        for desc in ("No-time A", "No-time B"):
            task = Task(task_type="misc", description=desc, duration_min=10)
            sched.add_task(task)   # no set_detail

        assert scheduler.detect_conflicts(sched) == []

    def test_empty_schedule_has_no_conflicts(self, sample_pet, scheduler):
        """An empty schedule must return an empty conflict list."""
        sched = self._make_schedule(sample_pet)
        assert scheduler.detect_conflicts(sched) == []


# ─────────────────────────────────────────────
# Filtering — filter_tasks
# ─────────────────────────────────────────────

class TestFilterTasks:
    """Verify filter_tasks narrows correctly by pet name and status."""

    def test_filter_by_pet_name(self, sample_owner, sample_pet, scheduler):
        luna = Pet(name="Luna", species="cat")
        sample_owner.add_pet(luna)

        sample_pet.add_task(Task(task_type="walk",    description="walk", duration_min=30))
        luna.add_task(Task(task_type="feeding", description="feed", duration_min=10))

        all_tasks    = scheduler.get_all_tasks(sample_owner)
        biscuit_only = scheduler.filter_tasks(all_tasks, pet_name="Biscuit", owner=sample_owner)

        assert len(biscuit_only) == 1
        assert biscuit_only[0].task_type == "walk"

    def test_filter_pending_only(self, sample_pet, sample_owner, scheduler):
        t1 = Task(task_type="walk",    description="walk", duration_min=30)
        t2 = Task(task_type="feeding", description="feed", duration_min=10)
        sample_pet.add_task(t1)
        sample_pet.add_task(t2)
        t1.mark_complete()

        pending = scheduler.filter_tasks(
            scheduler.get_all_tasks(sample_owner), completed=False
        )
        assert len(pending) == 1
        assert pending[0].task_type == "feeding"

    def test_filter_completed_only(self, sample_pet, sample_owner, scheduler):
        t1 = Task(task_type="walk",    description="walk", duration_min=30)
        t2 = Task(task_type="feeding", description="feed", duration_min=10)
        sample_pet.add_task(t1)
        sample_pet.add_task(t2)
        t1.mark_complete()

        done = scheduler.filter_tasks(
            scheduler.get_all_tasks(sample_owner), completed=True
        )
        assert len(done) == 1
        assert done[0].task_type == "walk"

    def test_filter_unknown_pet_returns_empty(self, sample_owner, scheduler):
        all_tasks = scheduler.get_all_tasks(sample_owner)
        result = scheduler.filter_tasks(
            all_tasks, pet_name="NoSuchPet", owner=sample_owner
        )
        assert result == []

    def test_filter_no_criteria_returns_all(self, sample_pet, sample_owner, scheduler):
        """Calling filter_tasks with no criteria must return every task unchanged."""
        for tt in ("walk", "feeding", "medication"):
            sample_pet.add_task(Task(task_type=tt, description=tt, duration_min=10))

        all_tasks = scheduler.get_all_tasks(sample_owner)
        assert scheduler.filter_tasks(all_tasks) == all_tasks


# ─────────────────────────────────────────────
# Owner
# ─────────────────────────────────────────────

class TestOwner:

    def test_owner_registers_pet(self, sample_owner):
        assert len(sample_owner.get_pets()) == 1

    def test_get_all_tasks_aggregates_across_pets(self, sample_owner, sample_pet):
        luna = Pet(name="Luna", species="cat")
        sample_owner.add_pet(luna)

        for label in ("walk", "feeding"):
            sample_pet.add_task(Task(task_type=label, description=label, duration_min=10))
        luna.add_task(Task(task_type="grooming", description="brush", duration_min=10))

        assert len(sample_owner.get_all_tasks()) == 3

    def test_find_pet_by_name_case_insensitive(self, sample_owner):
        assert sample_owner.find_pet_by_name("biscuit") is not None
        assert sample_owner.find_pet_by_name("BISCUIT") is not None

    def test_find_pet_by_name_missing_returns_none(self, sample_owner):
        assert sample_owner.find_pet_by_name("Ghost") is None


# ─────────────────────────────────────────────
# Scheduler — plan generation
# ─────────────────────────────────────────────

class TestSchedulerPlan:

    def test_plan_respects_time_budget(self, sample_pet, scheduler):
        """Tasks that exceed the budget must be dropped from the plan."""
        for i in range(5):
            t = Task(task_type="walk", description=f"walk {i}",
                     duration_min=60, priority="medium")
            t.set_detail(scheduled_time=time(i + 6, 0))
            sample_pet.add_task(t)

        sched = scheduler.build_schedule_for_pet(
            sample_pet, on_date=date.today(), time_budget_min=120
        )
        assert sum(t.duration_min for t in sched.generate_plan()) <= 120

    def test_plan_high_priority_before_low(self, sample_pet, scheduler):
        low  = Task(task_type="grooming",   description="groom",
                    duration_min=10, priority="low")
        high = Task(task_type="medication", description="meds",
                    duration_min=5,  priority="high")
        low.set_detail(scheduled_time=time(7, 0))    # earlier time, lower priority
        high.set_detail(scheduled_time=time(9, 0))
        sample_pet.add_task(low)
        sample_pet.add_task(high)

        plan = scheduler.build_schedule_for_pet(
            sample_pet, on_date=date.today()
        ).generate_plan()

        assert plan[0].priority == "high"
        assert plan[1].priority == "low"

    def test_pet_with_no_tasks_produces_empty_plan(self, sample_pet, scheduler):
        """Edge case: a pet with no tasks must produce an empty plan, not crash."""
        sched = scheduler.build_schedule_for_pet(sample_pet, on_date=date.today())
        assert sched.generate_plan() == []

    def test_schedule_reused_for_same_pet_and_date(self, sample_pet, scheduler):
        """build_schedule_for_pet twice with the same (pet, date) returns
        the same schedule object — no duplicates registered."""
        today = date.today()
        s1 = scheduler.build_schedule_for_pet(sample_pet, on_date=today)
        s2 = scheduler.build_schedule_for_pet(sample_pet, on_date=today)
        assert s1.schedule_id == s2.schedule_id