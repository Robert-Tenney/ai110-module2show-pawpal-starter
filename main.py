from datetime import date, time
from pawpal_system import Owner, Pet, Task, Scheduler
 
W = 62   # display width constant
 
def section(title: str) -> None:
    print(f"\n{'─' * W}\n  {title}\n{'─' * W}")
 
 
def main() -> None:
    scheduler = Scheduler()
 
    # ── Setup: owner + two pets ───────────────────────────────────────────
    sarah   = Owner(name="Sarah Chen", email="sarah@example.com", phone="555-0101")
    biscuit = Pet(name="Biscuit", species="dog", breed="Golden Retriever", age_years=3)
    luna    = Pet(name="Luna",    species="cat", breed="Siamese",          age_years=5)
 
    scheduler.register_owner(sarah)
    scheduler.add_pet_to_owner(biscuit, sarah)
    scheduler.add_pet_to_owner(luna,    sarah)
 
    # ── Tasks added OUT OF ORDER to demo sorting ──────────────────────────
    evening_walk = Task(
        task_type="walk", description="Evening neighbourhood walk",
        duration_min=30, priority="medium", frequency="daily",
    )
    evening_walk.set_detail(scheduled_time=time(18, 0), location="Block loop")
 
    enrichment = Task(
        task_type="enrichment", description="Puzzle feeder / training session",
        duration_min=20, priority="medium", frequency="daily",
    )
    enrichment.set_detail(scheduled_time=time(10, 0), location="Backyard")
 
    meds = Task(
        task_type="medication", description="Allergy tablet",
        duration_min=5, priority="high", frequency="daily",
    )
    meds.set_detail(scheduled_time=time(8, 5), notes="Give 10 mg Apoquel with food")
 
    breakfast = Task(
        task_type="feeding", description="Breakfast — 1 cup dry kibble",
        duration_min=10, priority="high", frequency="daily",
    )
    breakfast.set_detail(scheduled_time=time(8, 0))
 
    # Intentionally added LAST even though it's the earliest time
    walk = Task(
        task_type="walk", description="Morning walk around Riverside Park",
        duration_min=30, priority="high", frequency="daily",
    )
    walk.set_detail(scheduled_time=time(7, 30), location="Riverside Park")
 
    for task in [evening_walk, enrichment, meds, breakfast, walk]:
        biscuit.add_task(task)
 
    # Luna's tasks
    luna_breakfast = Task(
        task_type="feeding", description="Breakfast — wet food (1 pouch)",
        duration_min=5, priority="high", frequency="daily",
    )
    luna_breakfast.set_detail(scheduled_time=time(7, 45))
 
    luna_meds = Task(
        task_type="medication", description="Thyroid medication",
        duration_min=5, priority="high", frequency="daily",
    )
    luna_meds.set_detail(
        scheduled_time=time(7, 50),
        notes="½ pill of Methimazole, hide in treat",
    )
 
    grooming = Task(
        task_type="grooming", description="Brush coat — 10-minute session",
        duration_min=10, priority="low", is_recurring=False,
    )
    grooming.set_detail(scheduled_time=time(11, 0))
 
    for task in [luna_breakfast, luna_meds, grooming]:
        luna.add_task(task)
 
    today = date.today()
 
    # ══════════════════════════════════════════════════════════════════════
    # DEMO 1 — Full schedule (tasks sorted by priority then time)
    # ══════════════════════════════════════════════════════════════════════
    section("DEMO 1 — Full Daily Schedule")
    print(scheduler.format_all_schedules(sarah, on_date=today))
 
    # ══════════════════════════════════════════════════════════════════════
    # DEMO 2 — Sorting: sort_by_time()
    # Added tasks out of order above; sort_by_time() fixes that.
    # ══════════════════════════════════════════════════════════════════════
    section("DEMO 2 — Sorting by scheduled time  (sort_by_time)")
    all_tasks     = scheduler.get_all_tasks(sarah)
    sorted_tasks  = scheduler.sort_by_time(all_tasks)
 
    print("  Tasks sorted chronologically across both pets:\n")
    for t in sorted_tasks:
        time_str = t.detail.scheduled_time.strftime("%I:%M %p") if t.detail else "--:--"
        print(f"    {time_str}  {t.task_type.upper():<12}  {t.description}")
 
    # ══════════════════════════════════════════════════════════════════════
    # DEMO 3 — Filtering: filter_tasks()
    # ══════════════════════════════════════════════════════════════════════
    section("DEMO 3 — Filtering tasks  (filter_tasks)")
 
    # 3a. Filter by pet name
    biscuit_tasks = scheduler.filter_tasks(all_tasks, pet_name="Biscuit", owner=sarah)
    print(f"  Biscuit's tasks only ({len(biscuit_tasks)} total):")
    for t in scheduler.sort_by_time(biscuit_tasks):
        print(f"    {t.display()}")
 
    # 3b. Mark some tasks done, then filter by status
    walk.mark_complete()          # mark_complete now returns next occurrence
    luna_breakfast.mark_complete()
    pending = scheduler.filter_tasks(all_tasks, completed=False)
    done    = scheduler.filter_tasks(all_tasks, completed=True)
    print(f"\n  After marking 2 tasks complete:")
    print(f"    Pending : {len(pending)} tasks")
    print(f"    Done    : {len(done)} tasks")
 
    # 3c. Combined filter — only pending tasks for Biscuit
    biscuit_pending = scheduler.filter_tasks(
        all_tasks, pet_name="Biscuit", completed=False, owner=sarah
    )
    print(f"\n  Biscuit's pending tasks ({len(biscuit_pending)}):")
    for t in scheduler.sort_by_time(biscuit_pending):
        print(f"    {t.display()}")
 
    # ══════════════════════════════════════════════════════════════════════
    # DEMO 4 — Recurring tasks: complete_and_reschedule()
    # ══════════════════════════════════════════════════════════════════════
    section("DEMO 4 — Recurring tasks  (complete_and_reschedule)")
 
    print(f"  Completing Biscuit's medication (daily recurring)…")
    next_meds = scheduler.complete_and_reschedule(meds, biscuit)
 
    if next_meds:
        print(f"  ✓  '{meds.description}' marked done for {meds.due_date}")
        print(f"  ↺  Next occurrence auto-created for {next_meds.due_date}")
        print(f"     Same time? {next_meds.detail.scheduled_time.strftime('%I:%M %p')}")
    else:
        print("  (task was not recurring — no next occurrence created)")
 
    # Weekly recurring example
    weekly_bath = Task(
        task_type="grooming", description="Bath time",
        duration_min=20, priority="low",
        is_recurring=True, frequency="weekly",
    )
    weekly_bath.set_detail(scheduled_time=time(14, 0))
    biscuit.add_task(weekly_bath)
 
    next_bath = scheduler.complete_and_reschedule(weekly_bath, biscuit)
    if next_bath:
        print(f"\n  Weekly 'Bath time' completed for {weekly_bath.due_date}")
        print(f"  ↺  Next bath auto-scheduled for {next_bath.due_date}  (7 days later)")
 
    # ══════════════════════════════════════════════════════════════════════
    # DEMO 5 — Conflict detection: detect_conflicts()
    # ══════════════════════════════════════════════════════════════════════
    section("DEMO 5 — Conflict detection  (detect_conflicts)")
 
    # 5a. No conflicts yet on Biscuit's schedule
    biscuit_sched = scheduler.build_schedule_for_pet(biscuit, on_date=today)
    conflicts_before = scheduler.detect_conflicts(biscuit_sched)
    print("  Before adding conflicting task:")
    print(f"  {scheduler.format_conflicts(conflicts_before)}")
 
    # 5b. Add a task at 08:00 — same as breakfast — to trigger a conflict
    clash_task = Task(
        task_type="vet_call", description="Call vet to confirm appointment",
        duration_min=10, priority="medium",
    )
    clash_task.set_detail(scheduled_time=time(8, 0))   # ← same as breakfast!
    biscuit_sched.add_task(clash_task)
 
    conflicts_after = scheduler.detect_conflicts(biscuit_sched)
    print("\n  After adding 'Call vet' at 08:00 AM (same as Breakfast):")
    print(f"  {scheduler.format_conflicts(conflicts_after)}")
 
    # ── Summary stats ──────────────────────────────────────────────────────
    section("Summary")
    total   = scheduler.get_all_tasks(sarah)
    pending = scheduler.get_pending_tasks(sarah)
    print(f"  Total tasks across both pets : {len(total)}")
    print(f"  Pending                      : {len(pending)}")
    print(f"  Completed                    : {len(total) - len(pending)}")
    print()
 
 
if __name__ == "__main__":
    main()