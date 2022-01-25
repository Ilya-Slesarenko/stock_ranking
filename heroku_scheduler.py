import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from ranking_part_to_G import RankingClass as scf
from w2w_total_change import RankingClass as wtc
from parse_insiders_1 import InsidersDeals

shed = BlockingScheduler(timezone="Europe/Moscow")

def job_function_1():
    scf().spreadsheet_forming()

def job_function_2():
    wtc().total_change_calc()
    
def job_function_3():
    InsidersDeals().PerformAll()

shed.add_job(job_function_1, 'cron', day_of_week='sun', hour=2, minute=5)  # sun (Sunday night : 2 ; 5)
shed.add_job(job_function_2, 'cron', day_of_week='sun', hour=10, minute=10)  # sun (Sunday - Monday morning)
# shed.add_job(job_function_3, 'cron', day_of_week='wed', hour=16, minute=24)  # set to !!! 8 and 5, sun (Sunday)
shed.start()
