import time
from concurrent.futures.thread import ThreadPoolExecutor
import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

from src.common.log import logger
from src.common.yaml_reader import conf_get
from src.modules.score_and_level import score_and_level_hours_to_update
from src.modules.steam_interface import steam_interface_hours_to_update
from src.modules.telnet_client import telnet_client_hours_to_update


def thread_scheduler():
    scheduler = BlockingScheduler()
    scheduler.add_job(telnet_client_hours_to_update, 'cron', day_of_week='0-6', hour='0-23', minute='00', next_run_time=datetime.datetime.now(), max_instances=3)
    scheduler.add_job(steam_interface_hours_to_update, 'cron', day_of_week='0-6', hour='0-23', minute='10', next_run_time=datetime.datetime.now() + datetime.timedelta(minutes=1), max_instances=3)
    scheduler.add_job(score_and_level_hours_to_update, 'cron', day_of_week='0-6', hour='0-23', minute='20', next_run_time=datetime.datetime.now() + datetime.timedelta(minutes=5), max_instances=3)
    scheduler.start()


if __name__ == '__main__':
    # main func
    # executor = ThreadPoolExecutor(max_workers=1)
    # executor.submit(thread_scheduler)
    thread_scheduler()