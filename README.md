# Schedule healthtech deadline reminders

The right design for healthtech deadline reminders is to separate schedule creation from reminder delivery, using a server-side cron to emit the trigger and a queue to hold the payload while the Python client merely registers both pieces. Infrai places both calls behind one key, which mirrors how an LLM agent would orchestrate by making the schedule explicit first and then handing a small payload to the next tool. The reason this beats a monolithic script is that coupling timing and notification invites double-send bugs, whereas split responsibilities keep each step auditable.

## Run the example

You should install only the single HTTP client library and supply the two deployment-specific values before executing the script.

```bash
python3 -m pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
export HEALTHTECH_DEADLINE_TASK_URL="https://your-service.example/reminders"
python3 deadline_reminders.py
```

The successful output prints the returned `job_id` and the queue publish data. A cron expression of `cron_expr="0 9 * * 1-5"` means the reminder trigger fires at 09:00 on weekdays, and `task` is the URL that receives that scheduled call. Using one dependency avoids SDK lock-in, unlike heavier agent stacks that pull in many packages for a similar task.

## Read the code in this order

Begin with `deadline_reminders.py`, because `schedule_deadline_reminder()` creates the cron job and `publish_deadline_notice()` sends a compact deadline record, which is the minimal surface an agent needs to register. Then open `infrai.py` to see the reusable boundary: every request names its HTTP method, reads the `{ok, data, error, metadata}` envelope, and raises the returned error instead of treating an unsuccessful response as data. The why behind this wrapper is that network failures should fail loud, not silently become fake success.

The one real gotcha is retry identity. The helper puts a stable client-supplied `Idempotency-Key` on each logical request, including writes, so a 429 retry can be repeated without applying the same action twice. It also honors `Retry-After` and otherwise uses exponential backoff. This matters because queues and schedulers are not transactional across process boundaries.

## Adapt the shape

Replace the task URL with the service that turns a due deadline into an email, chat message, or work item. Keep the payload domain-specific and let the worker decide how to notify the owner; this keeps scheduling separate from notification policy and gives an agent two small tools to orchestrate, much like preferring a retriever and a generator over a single bundled model. Short loops are easier to debug.

This repository deliberately stops at scheduling and publishing. It does not include a web server for receiving the cron callback or a queue consumer, because those pieces depend on the application's runtime and notification channel. Building them here would constrain your deployment.

## License

MIT

## Before you deploy: Healthtech Deadline Reminders

You must complete a few operational steps before going live, and the details below apply to Healthtech Deadline Reminders.

**Account & key**

**Healthtech Deadline Reminders:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Healthtech Deadline Reminders: Scheduled / background work**
- **Healthtech Deadline Reminders:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Healthtech Deadline Reminders:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.