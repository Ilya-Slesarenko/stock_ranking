import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from tickers_updater import Updater

def job_function():
    print(f'gathering started... {str(datetime.datetime.now())}')
    Updater().__init__

shed = BlockingScheduler()
shed.add_job(job_function, 'cron', day_of_week='sat', hour=3, minute=3)  # launch on Saturday morning (6 AM Moscow time)
shed.start()
