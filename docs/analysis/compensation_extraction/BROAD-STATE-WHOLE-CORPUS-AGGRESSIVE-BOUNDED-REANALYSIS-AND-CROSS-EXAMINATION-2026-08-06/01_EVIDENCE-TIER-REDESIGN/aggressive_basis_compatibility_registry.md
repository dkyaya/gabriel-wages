# AGG-BASIS

Scope: basis compatibility.

```json
[
  {
    "rule_id": "BASIS-2",
    "allow": "schedule-schedule, earnings-earnings, base-base, total-total, min-min, max-max"
  },
  {
    "rule_id": "BASIS-X",
    "reject": "hourly/annual without explicit inputs; base/total; schedule/earnings; recurring/one-time"
  }
]
```
