# app/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
from .fetch_dart import fetch_dart_today
from .fetch_news_naver import fetch_naver_news
from .normalizer import normalize_recent
from .scorer import init_db_and_seed
from .trading_strategy import generate_signals
from .trading_executor import execute_signals, update_positions, monitor_positions
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
    sch = BackgroundScheduler(timezone="Asia/Seoul", job_defaults={"coalesce": True, "max_instances": 1})
    sch.add_listener(_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED)

    # 👇 시작 즉시 1회 실행(시작 확인용)
    sch.add_job(fetch_dart_today, "date", next_run_time=dt.datetime.now(), id="dart_once")
    sch.add_job(fetch_naver_news, "date", next_run_time=dt.datetime.now(), id="naver_once")
    sch.add_job(normalize_recent, "date", next_run_time=dt.datetime.now(), id="norm_once")

    # ⏱ 주기 작업 - 뉴스 수집 및 정규화
    sch.add_job(fetch_dart_today, "cron", minute="*/5", id="dart_5m")
    sch.add_job(fetch_naver_news, "cron", minute="*/4", id="naver_4m")
    sch.add_job(normalize_recent, "cron", minute="*/5", id="norm_5m")
    
    # 🤖 자동매매 작업
    sch.add_job(generate_signals, "cron", minute="*/5", id="trading_signal_5m")  # 5분마다 신호 생성
    sch.add_job(execute_signals, "cron", minute="*/10", id="trading_execute_10m")  # 10분마다 주문 실행
    sch.add_job(monitor_positions, "cron", minute="*/1", id="trading_monitor_1m")  # 1분마다 포지션 모니터링
    sch.add_job(update_positions, "cron", minute="*/30", id="trading_update_30m")  # 30분마다 평가 업데이트

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
