import time
from concurrent.futures.thread import ThreadPoolExecutor
import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

from src.common.log import logger
from src.common.yaml_reader import conf_get
from src.modules.score_and_level import ScoreAndLevel
from src.modules.steam_interface import SteamInterface
from src.modules.telnet_client import TelnetClient


def thread_scheduler():
    query_password = conf_get('ts3_server')['query_password']
    tc = TelnetClient(password=query_password)
    si = SteamInterface()
    sal = ScoreAndLevel()

    scheduler = BlockingScheduler()
    scheduler.add_job(tc.hours_to_update, 'cron', day_of_week='0-6', hour='0-23', minute='00', next_run_time=datetime.datetime.now())
    scheduler.add_job(si.hours_to_update, 'cron', day_of_week='0-6', hour='0-23', minute='10', next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=5))
    scheduler.add_job(sal.hours_to_update, 'cron', day_of_week='0-6', hour='0-23', minute='20', next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=20))
    scheduler.start()


if __name__ == '__main__':
    # main func
    executor = ThreadPoolExecutor(max_workers=3)
    executor.submit(thread_scheduler)
    while 1:
        time.sleep(10)