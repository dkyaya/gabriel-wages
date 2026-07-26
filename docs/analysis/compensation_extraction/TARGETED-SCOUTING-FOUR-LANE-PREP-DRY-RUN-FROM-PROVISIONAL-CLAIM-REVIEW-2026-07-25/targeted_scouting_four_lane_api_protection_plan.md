# API protection plan

- One live lane at a time; separate prompt and preflight for every lane.
- Recommended 60–90 minute quiet interval between completed lanes; do not automate starts.
- Abort on lock/hash drift, authentication failure, schema drift, transport instability, or rate-limit escalation.
- Bounded retries only in the future authorized live prompt; never save secrets or raw prompts/responses.
- A completed lane relay must be inspected before the next lane begins.
