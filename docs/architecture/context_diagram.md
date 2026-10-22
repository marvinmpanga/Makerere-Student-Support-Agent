# Context Diagram

The expanded systems-design views are maintained in `01-system-context.md` through `08-end-to-end-activity.md`.

```mermaid
flowchart LR
    Student -->|question| Agent[Student Support Agent]
    Agent -->|retrieves approved information| Knowledge[(Knowledge Sources)]
    Agent -->|answer with boundaries| Student
    Agent -->|escalates| Staff[Relevant University Office]
    Staff -->|verified updates| Knowledge
```

The application supports discovery and explanation; it does not replace authorized university staff or make binding decisions.
