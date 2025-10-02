# app/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
from .fetch_dart import fetch_dart_today
from .fetch_news_naver import fetch_naver_news
from .normalizer import normalize_recent
from .scorer import init_db_and_seed
import time, datetime as dt, logging

# 🔊 로깅 기본 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("cb.scheduler")


def _listener(event):
    if event.exception:
        log.error(f"JOB ERROR: {event.job_id}", exc_info=True)
    else:
        log.info(f"JOB OK: {event.job_id} (ran at {event.scheduled_run_time})")


def main():
    init_db_and_seed()
    sch = BackgroundScheduler(
        timezone="Asia/Seoul", job_defaults={"coalesce": True, "max_instances": 1}
    )
    sch.add_listener(_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED)

    # 👇 시작 즉시 1회 실행(시작 확인용)
    sch.add_job(
        fetch_dart_today, "date", next_run_time=dt.datetime.now(), id="dart_once"
    )
    sch.add_job(
        fetch_naver_news, "date", next_run_time=dt.datetime.now(), id="naver_once"
    )
    sch.add_job(
        normalize_recent, "date", next_run_time=dt.datetime.now(), id="norm_once"
    )

    # ⏱ 주기 작업
    sch.add_job(fetch_dart_today, "cron", minute="*/5", id="dart_5m")
    sch.add_job(fetch_naver_news, "cron", minute="*/4", id="naver_4m")
    sch.add_job(normalize_recent, "cron", minute="*/5", id="norm_5m")

    sch.start()
    log.info("Scheduler started. Jobs: %s", [j.id for j in sch.get_jobs()])
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        log.info("Shutting down scheduler...")
        sch.shutdown()


if __name__ == "__main__":
    main()
