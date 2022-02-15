import datetime, time
from apscheduler.schedulers.blocking import BlockingScheduler
from ranking_part_to_G import RankingClass as scf
from rank_G_double_check import RankingClass as scf_double_check
from ranking_part_to_G_2 import RankingClass as scf_2
# from parse_insiders_1 import InsidersDeals

def job_function_1():
    scf().spreadsheet_forming()
    time.sleep(10)
    scf_double_check().spreadsheet_forming_after_check()
    time.sleep(10)
    scf_2().PerformAll() # perform the 2-nd part right after the first one

shed = BlockingScheduler(timezone="Europe/Moscow")
      
shed.add_job(job_function_1, 'cron', day_of_week='sun', hour=5, minute=5) 
# shed.add_job(job_function_2, 'cron', day_of_week='sun', hour=10, minute=5)  # sun (Sunday morning (say, 10 AM)
# shed.add_job(job_function_3, 'cron', day_of_week='mon', hour=16, minute=37)  # sun (Monday morning)
shed.start()
