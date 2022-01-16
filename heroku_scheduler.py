import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from ranking_part_to_G import RankingClass

def job_function():
    print(f'gathering started... {str(datetime.datetime.now())}')
    RankingClass().spreadsheet_forming()

shed = BlockingScheduler(timezone="Europe/Moscow")
shed.add_job(job_function, 'cron', day_of_week='sun', hour=12, minute=25)  # 5 and 5, sun (Sunday)
shed.start()
