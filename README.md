# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

══════════════════════════════════════════════════════════════
  TODAY'S SCHEDULE  —  Sarah Chen
══════════════════════════════════════════════════════════════
┌────────────────────────────────────────────────────────────┐
│   Biscuit  ·  2026-06-25                                   │
│   Budget: 480 min  |  Used: 95 min  |  Free: 385 min       │
├────────────────────────────────────────────────────────────┤
│   [○] 07:30 AM  WALK         Morning walk @ Riverside Park  (30 min, high)  │
│   [○] 08:00 AM  FEEDING      Breakfast — 1 cup dry kibble  (10 min, high)   │
│   [○] 08:05 AM  MEDICATION   Allergy tablet | Give 10 mg Apoquel with food  │
│   [○] 10:00 AM  ENRICHMENT   Puzzle feeder / training session @ Backyard    │
│   [○] 06:00 PM  WALK         Evening neighbourhood walk @ Block loop        │
└────────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────────┐
│   Luna  ·  2026-06-25                                      │
│   Budget: 480 min  |  Used: 20 min  |  Free: 460 min       │
├────────────────────────────────────────────────────────────┤
│   [○] 07:45 AM  FEEDING      Breakfast — wet food (1 pouch)  (5 min, high)  │
│   [○] 07:50 AM  MEDICATION   Thyroid medication | ½ pill Methimazole        │
│   [○] 11:00 AM  GROOMING     Brush coat — 10-minute session  (10 min, low)  │
└────────────────────────────────────────────────────────────┘
══════════════════════════════════════════════════════════════

  Total tasks across all pets : 8
  Pending (not yet completed) : 8

  After marking Biscuit's walk done:
  Pending tasks : 7

## 🧪 Testing PawPal+

```bash
python main.py
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
