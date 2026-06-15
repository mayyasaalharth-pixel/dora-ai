#!/usr/bin/env python3
import os
import asyncio
import logging
import signal
import sys
import uvicorn
from threading import Thread

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

from src.scheduler import DailyScheduler
from src.api import app


def run_api():
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


async def main():
    print("=" * 60)
    print("نظام تجميع أخبار الذكاء الاصطناعي - AI News Aggregator")
    print("=" * 60)

    scheduler = DailyScheduler()

    if "--run-now" in sys.argv:
        logger.info("تشغيل دورة جلب الأخبار فوراً...")
        await scheduler.run_daily_pipeline()
        logger.info("اكتملت الدورة. يتم إيقاف النظام.")
        return

    api_thread = Thread(target=run_api, daemon=True)
    api_thread.start()
    logger.info("API متاح على http://localhost:8000")

    stop_event = asyncio.Event()

    def shutdown():
        logger.info("جاري إيقاف النظام...")
        scheduler.stop()
        stop_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, shutdown)
        except NotImplementedError:
            pass

    try:
        await scheduler.run_continuously()
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        scheduler.stop()
        logger.info("تم إيقاف النظام")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("تم إيقاف النظام بواسطة المستخدم")
