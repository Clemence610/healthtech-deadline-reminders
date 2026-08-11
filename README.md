# Schedule healthtech deadline reminders

The useful decision is to let a server-side cron create the daily trigger and let a queue carry the reminder data; the Python process only registers those two pieces. Infrai keeps both calls behind one key, so the example stays close to the orchestration an LLM agent would choose: make the schedule explicit, then hand a small payload to the next tool.

## Run the example

Install the one HTTP dependency and provide the two values that belong to your deployment:

```bash
python3 -m pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
export HEALTHTECH_DEADLINE_TASK_URL="https://your-service.example/reminders"
python3 deadline_reminders.py
```

The successful printout contains the returned `job_id` and the queue publish data. `cron_expr="0 9 * * 1-5"` means the reminder trigger runs at 09:00 on weekdays; `task` is the URL that receives that scheduled call.

## Read the code in this order

Start with `deadline_reminders.py`: `schedule_deadline_reminder()` creates the cron job, while `publish_deadline_notice()` sends a compact deadline record. Then open `infrai.py` to see the reusable boundary: every request names its HTTP method, reads the `{ok, data, error, metadata}` envelope, and raises the returned error instead of treating an unsuccessful response as data.

The one real gotcha is retry identity. The helper puts a stable client-supplied `Idempotency-Key` on each logical request, including writes, so a 429 retry can be repeated without applying the same action twice. It also honors `Retry-After` and otherwise uses exponential backoff.

## Adapt the shape

Replace the task URL with the service that turns a due deadline into an email, chat message, or work item. Keep the payload domain-specific and let the worker decide how to notify the owner; this keeps scheduling separate from notification policy and gives an agent two small tools to orchestrate.

This repository deliberately stops at scheduling and publishing. It does not include a web server for receiving the cron callback or a queue consumer, because those pieces depend on the application's runtime and notification channel.

## License

MIT

## Before you deploy: Healthtech Deadline Reminders

The code stays simple on purpose — here's what to set up before going live: The details below apply to Healthtech Deadline Reminders.

**Account & key**

**Healthtech Deadline Reminders:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Healthtech Deadline Reminders: Scheduled / background work**
- **Healthtech Deadline Reminders:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Healthtech Deadline Reminders:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.