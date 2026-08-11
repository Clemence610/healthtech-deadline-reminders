"""Schedule a healthtech deadline webhook and publish one reminder example."""

import os

from infrai import infrai


def schedule_deadline_reminder() -> str:
    """Register a weekday reminder; the task URL receives the scheduled call."""
    job = infrai.cron.create(
        cron_expr="0 9 * * 1-5",
        task=os.environ["HEALTHTECH_DEADLINE_TASK_URL"],
    )
    return str(job["job_id"])


def publish_deadline_notice(deadline: str, owner: str) -> dict:
    """Put the reminder payload on the queue for the notification worker."""
    return infrai.queue.publish(
        queue="healthtech-deadlines",
        payload={"deadline": deadline, "owner": owner, "kind": "healthtech"}
    )


if __name__ == "__main__":
    job_id = schedule_deadline_reminder()
    try:
        notice = publish_deadline_notice("2026-09-30", "clinical-ops")
        print({"job_id": job_id, "notice": notice})
    finally:
        infrai.cron.delete(job_id)
