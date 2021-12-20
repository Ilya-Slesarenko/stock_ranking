import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from ranking_part_to_G import RankingClass

def job_function():
    print(f'gathering started... {str(datetime.datetime.now())}')
    RankingClass().spreadsheet_forming()

shed = BlockingScheduler()
shed.add_job(job_function, 'cron', day_of_week='mon', hour=14, minute=30)  # launch on Saturday morning (6 AM Moscow time)
# shed.add_job(job_function, 'cron', day_of_week='sun', hour=3, minute=3)  # launch on Sunday morning (6 AM Moscow time)
shed.start()
