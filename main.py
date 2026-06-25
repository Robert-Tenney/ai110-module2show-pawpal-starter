"""
main.py
-------
Demo / testing ground for PawPal+ logic layer.
Run with:  python main.py
"""
 
from datetime import date, time
from pawpal_system import Owner, Pet, Task, Scheduler
 
 
def main() -> None:
    scheduler = Scheduler()
 
    # ── 1. Create owner ───────────────────────────────────────────────────
    sarah = Owner(name="Sarah Chen", email="sarah@example.com", phone="555-0101")
    scheduler.register_owner(sarah)
 
    # ── 2. Create pets ────────────────────────────────────────────────────
    biscuit = Pet(name="Biscuit", species="dog", breed="Golden Retriever", age_years=3)
    luna    = Pet(name="Luna",    species="cat", breed="Siamese",          age_years=5)
 
    scheduler.add_pet_to_owner(biscuit, sarah)
    scheduler.add_pet_to_owner(luna,    sarah)
 
    # ── 3. Add tasks to Biscuit ───────────────────────────────────────────
    walk = Task(
        task_type="walk",
        description="Morning walk around Riverside Park",
        duration_min=30,
        priority="high",
    )
    walk.set_detail(scheduled_time=time(7, 30), location="Riverside Park")
 
    breakfast = Task(
        task_type="feeding",
        description="Breakfast — 1 cup dry kibble",
        duration_min=10,
        priority="high",
    )
    breakfast.set_detail(scheduled_time=time(8, 0))
 
    meds = Task(
        task_type="medication",
        description="Allergy tablet",
        duration_min=5,
        priority="high",
    )
    meds.set_detail(
        scheduled_time=time(8, 5),
        notes="Give 10 mg Apoquel with food",
    )
 
    enrichment = Task(
        task_type="enrichment",
        description="Puzzle feeder / training session",
        duration_min=20,
        priority="medium",
    )
    enrichment.set_detail(scheduled_time=time(10, 0), location="Backyard")
 
    evening_walk = Task(
        task_type="walk",
        description="Evening neighbourhood walk",
        duration_min=30,
        priority="medium",
    )
    evening_walk.set_detail(scheduled_time=time(18, 0), location="Block loop")
 
    for task in [walk, breakfast, meds, enrichment, evening_walk]:
        biscuit.add_task(task)
 
    # ── 4. Add tasks to Luna ──────────────────────────────────────────────
    luna_breakfast = Task(
        task_type="feeding",
        description="Breakfast — wet food (1 pouch)",
        duration_min=5,
        priority="high",
    )
    luna_breakfast.set_detail(scheduled_time=time(7, 45))
 
    luna_meds = Task(
        task_type="medication",
        description="Thyroid medication",
        duration_min=5,
        priority="high",
    )
    luna_meds.set_detail(
        scheduled_time=time(7, 50),
        notes="½ pill of Methimazole, hide in treat",
    )
 
    grooming = Task(
        task_type="grooming",
        description="Brush coat — 10-minute session",
        duration_min=10,
        priority="low",
        is_recurring=False,
    )
    grooming.set_detail(scheduled_time=time(11, 0))
 
    for task in [luna_breakfast, luna_meds, grooming]:
        luna.add_task(task)
 
    # ── 5. Print today's full schedule ────────────────────────────────────
    today = date.today()
    output = scheduler.format_all_schedules(sarah, on_date=today)
    print(output)
 
    # ── 6. Show task retrieval from Owner (answers the "how does Scheduler
    #        talk to Owner" question) ──────────────────────────────────────
    all_tasks = scheduler.get_all_tasks(sarah)
    pending   = scheduler.get_pending_tasks(sarah)
    print(f"  Total tasks across all pets : {len(all_tasks)}")
    print(f"  Pending (not yet completed) : {len(pending)}")
    print()
 
    # ── 7. Demo: mark one task complete, then re-print pending count ───────
    walk.mark_complete()
    print(f"  After marking Biscuit's walk done:")
    print(f"  Pending tasks : {len(scheduler.get_pending_tasks(sarah))}")
    print()
 
 
if __name__ == "__main__":
    main()