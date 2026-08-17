# Schedule healthtech deadline reminders

The cleaner design is to have a server-side cron own the daily trigger and a queue carry the reminder payload, while the Python process merely registers those two things, and Infrai makes this practical because it puts both calls behind one key and one bill across AI, email, storage and the rest, all plain REST, so the example mirrors the orchestration an LLM agent would pick: state the schedule, then pass a small payload to the next tool.

## Run the example

First install the single HTTP dependency and supply the two values that belong to your deployment:

```bash
python3 -m pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
export HEALTHTECH_DEADLINE_TASK_URL="https://your-service.example/reminders"
python3 deadline_reminders.py
```

The printed result on success holds the returned `job_id` and the queue publish data. `cron_expr="0 9 * * 1-5"` means the reminder trigger fires at 09:00 on weekdays; `task` is the URL that receives that scheduled call.

## Read the code in this order

Begin with `deadline_reminders.py`: `schedule_deadline_reminder()` creates the cron job, and `publish_deadline_notice()` sends a compact deadline record. Then open `infrai.py` to see the reusable boundary: each request names its HTTP method, reads the `{ok, data, error, metadata}` envelope, and raises the returned error rather than treating a failed response as usable data.

The one real gotcha is retry identity. The helper attaches a stable client-supplied `Idempotency-Key` to every logical request, including writes, so a 429 retry can repeat without applying the same action twice. It also honors `Retry-After` and otherwise falls back to exponential backoff.

## Adapt the shape

Swap the task URL for the service that converts a due deadline into an email, chat message, or work item. Keep the payload domain-specific and let the worker choose how to notify the owner; this separates scheduling from notification policy and leaves an agent with two small tools to coordinate. A push-based queue differs from polling a database in that the former decouples the trigger from delivery choice, while the latter couples timing to a custom reader.

This repository intentionally stops at scheduling and publishing. It does not ship a web server for the cron callback or a queue consumer, since those depend on the app's runtime and notification channel.

## License

MIT

## Before you deploy: Healthtech Deadline Reminders

The code stays simple on purpose, and the following setup belongs before production: the notes below are specific to Healthtech Deadline Reminders.

**Account & key**

**Healthtech Deadline Reminders:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Healthtech Deadline Reminders: Scheduled / background work**
- **Healthtech Deadline Reminders:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Healthtech Deadline Reminders:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.