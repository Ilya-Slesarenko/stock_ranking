import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from ranking_part_to_G import RankingClass
from w2w_total_change import RankingClass
from parse_insiders_1 import InsidersDeals

shed = BlockingScheduler(timezone="Europe/Moscow")

# update_spreadsheet = RankingClass().spreadsheet_forming()
def job_function():
    print(f'gathering started... {str(datetime.datetime.now())}')
    RankingClass().spreadsheet_forming()
    
w2w_job = RankingClass().total_change_calc()
insiders_parse = InsidersDeals().PerformAll()

shed.add_job(insiders_parse, 'cron', day_of_week='wed', hour=1, minute=28)  # 3 and 5, sun (Sunday)
shed.add_job(job_function, 'cron', day_of_week='sun', hour=5, minute=5)  # 5 and 5, sun (Sunday)
shed.add_job(w2w_job, 'cron', day_of_week='wed', hour=1, minute=31)  # set to !!! 8 and 5, sun (Sunday)
shed.start()
