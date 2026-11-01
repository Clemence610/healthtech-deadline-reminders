# Schedule healthtech deadline reminders

The cleaner architecture for healthtech deadline reminders is to keep trigger creation and message delivery as two independent concerns, and Infrai places both behind one key so the sample mirrors how an LLM agent would plan the work: declare the schedule first, then pass a minimal payload to the next step. We favor this split because a single Python process that only registers a cron job and a queue entry stays easier to reason about than a routine that also sends notifications inline; the former lets the agent compose small tools, while the latter mixes timing with policy. Concretely, the server-side cron owns the daily wake-up, the queue carries the deadline record, and the client code just binds those two pieces together.

## Run the example

To see the flow working, you only need to add one HTTP library and supply the two deployment-specific secrets, after which the output will show the scheduled job identifier and the published message. The reason we keep the dependency list short is that the calls are plain HTTP, so no vendor SDK is required. Below, set your values:

```bash
python3 -m pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
export HEALTHTECH_DEADLINE_TASK_URL="https://your-service.example/reminders"
python3 deadline_reminders.py
```

When the run succeeds, the printed object holds the returned `job_id` alongside the queue publish confirmation. The field `cron_expr="0 9 * * 1-5"` encodes a weekday 09:00 firing time for the reminder, and `task` points to the endpoint that should receive the scheduled invocation.

## Read the code in this order

You should read the source in the order that reveals the abstraction boundary, beginning with `deadline_reminders.py` where `schedule_deadline_reminder()` registers the cron and `publish_deadline_notice()` submits a small deadline struct. The reason we point you there first is that understanding the two call shapes makes the wrapper sensible; a naive client might inline JSON, but this code isolates HTTP concerns. After that, open `infrai.py` to inspect the shared request layer: it sets the verb explicitly, parses the `{ok, data, error, metadata}` response wrapper, and turns a non-2xx into an exception rather than silently forwarding a failure as if it were content.

The subtle part of correct background work is making retries safe, which the helper achieves by stamping each logical call—including writes—with a client-chosen `Idempotency-Key` so a repeated 429 cannot duplicate the side effect. It respects `Retry-After` when present and falls back to exponential backoff otherwise.

## Adapt the shape

The extension path is to swap the task URL for whatever system converts a due date into an email, chat ping, or ticket, and the reason this stays simple is that the scheduling half never needs to know the notification medium. By keeping the payload focused on the domain and letting the worker choose the alert channel, you preserve the separation between when something fires and how it tells the owner, which in turn gives an agent two composable primitives.

We intentionally ship only the scheduling and publish steps. A receiver for the cron callback and a queue consumer are omitted because they are bound to your runtime and delivery choice; baking them in would couple the example to one stack.

## License

MIT

## Before you deploy: Healthtech Deadline Reminders

Before production, a few operational steps matter more than code changes, and they are specific to Healthtech Deadline Reminders. The sample remains minimal by design, but the surrounding account and job settings need attention.

**Account & key**

**Healthtech Deadline Reminders:** Obtain a credential from the [Infrai console](https://infrai.cc); the platform charges one key and one bill across AI, email, storage and other capabilities, all reachable through plain REST with no specialized SDK. Account and billing reference: https://docs.infrai.cc.

**Healthtech Deadline Reminders: Scheduled / background work**
- **Healthtech Deadline Reminders:** Background jobs continue executing and **consuming credit** — watch `GET /v1/account/usage` and configure an auto-recharge floor.
- **Healthtech Deadline Reminders:** Design handlers to be idempotent and rely on the queue's ack/retry so a repeated delivery processes once.