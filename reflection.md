# PawPal+ Project Reflection

## 1. System Design
Allow a user to add a pet, Allow a user to assign and track requested tasks(i.e Where and when to take the pet out for a walk, what time, type and dosage of meds their pet needs to take) and create a scheduel for each day the pet is being cared for. 
**a. Initial design**
Allow a user to add a pet, Allow a user to assign and track requested tasks(i.e Where and when to take the pet out for a walk, what time, type and dosage of meds their pet needs to take) and create a scheduel for each day the pet is being cared for. 
Owner/Pet(assigns an owner value to a listed pet),
Time,task and details(assigns a relationship between a task, at what time it needs to be done and what exactly needs to be done i.e taking a dog out for a walk at a near by park at 11:45 am)

**b. Design changes**

No the desgin did not change much from when I initally implemented it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

Sorting uses sort_by_time(), which calls sorted() with a lambda key on task.detail.scheduled_time — tasks with no time set fall to the end. Filtering uses filter_tasks(), which narrows a task list by pet name, completion status, or both. Recurring tasks are handled by mark_complete(), which clones the finished task and sets its due_date forward by one day or one week using timedelta. Conflict detection uses detect_conflicts(), which checks for two tasks sharing the exact same time slot and returns a warning object instead of crashing.
**b. Tradeoffs**

The conflict detector only catches tasks scheduled at the exact same time. It won't warn you if a 30-minute walk at 8:00 and a feeding at 8:10 overlap in practice. This was a deliberate choice — checking for duration overlap is more complex and depends on duration estimates being accurate, which user-entered data often isn't. The simpler approach is easier to read and covers the most common mistake
---

## 3. AI Collaboration

**a. How you used AI**

I used AI to help trouble shoot code and to help make my summaries more clear and precise in the form of detecting spelling and grammar errors.In additon I used AI to reformat some responses to include emojis since I have no idea on how to do it.
**b. Judgment and verification**

I really couldn't find a moment where I disagreed with the output the AI(Claude) gave me since I used the same logic I tend to need being precise and detailed instruction on what is needed for the output.

---

## 4. Testing and Verification

**a. What you tested**

I tested to see what would happen if someone entered the same information multiple times which is important since it could cause the system to repeat the same outputs mutliple times which could cause the application to crash.

**b. Confidence**

I am fairly confident that my scheduler works but if I had more time to test it I would have been more rigerous in testing to see how it would respond to a user added multiple pets 

---

## 5. Reflection

**a. What went well**

I was the most satified with using an AI program to help me ensure everying this was phrased corrected and using it to include icons in my response since it look like a fun thing to do.

**b. What you would improve**

If I had another iteration I am not really sure what I would add

**c. Key takeaway**

One important thing I learned is that with exteremtly detailed instructions on what you need AI programs rarely produces incorrect or invalid outputs
