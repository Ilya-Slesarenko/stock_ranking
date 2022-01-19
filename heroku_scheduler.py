import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from ranking_part_to_G import RankingClass
from w2w_total_change import RankingClass
from parse_insiders_1 import InsidersDeals

shed = BlockingScheduler(timezone="Europe/Moscow")

def job_function_1():
    RankingClass().spreadsheet_forming()

def job_function_2():
    RankingClass().total_change_calc()
    
def job_function_3():
    InsidersDeals().PerformAll()

shed.add_job(job_function_1, 'cron', day_of_week='sun', hour=2, minute=5)  # sun (Sunday night)
shed.add_job(job_function_2, 'cron', day_of_week='sun', hour=5, minute=50)  # sun (Sunday - Monday morning)
shed.add_job(job_function_3, 'cron', day_of_week='wed', hour=16, minute=24)  # set to !!! 8 and 5, sun (Sunday)
shed.start()
