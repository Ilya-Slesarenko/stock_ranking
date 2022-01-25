# -*- coding: utf-8 -*-

import logging, random, warnings, httplib2, apiclient.discovery, datetime
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

warnings.filterwarnings('ignore')
pd.options.mode.chained_assignment = None  # default='warn'


class RankingClass():
    def __init__(self):
        # Получение списка акций  из готового листа Google Sheet
        self.CREDENTIALS_FILE = 'stock-spreadsheets-9974a749b7e4.json'
        self.ranking_page = '1C_uAagRb_GV7tu8X1fbJIM9SRtH3bAcc-n61SP8muXg'
        credentials = ServiceAccountCredentials.from_json_keyfile_name(self.CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        # credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        httpAuth = credentials.authorize(httplib2.Http())  # Авторизуемся в системе
        self.service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)  # Выбираем работу с таблицами и 4 версию API


    def preparing_rank_sheets(self):
        #reading the updated result now
        results_rank_updated = self.service.spreadsheets().values().batchGet(spreadsheetId=self.ranking_page, ranges='A:AE', valueRenderOption='FORMATTED_VALUE', dateTimeRenderOption='FORMATTED_STRING').execute()
        # results_rank_updated = service.spreadsheets().values().batchGet(spreadsheetId=ranking_page, ranges='A:AE', valueRenderOption='FORMATTED_VALUE', dateTimeRenderOption='FORMATTED_STRING').execute()
        rank_sheet_values_updated = results_rank_updated['valueRanges'][0]['values'][1:]

        # making int values, cause they are strings from the source!
        fixed_range = []
        for v in rank_sheet_values_updated:
            fixed_values = []
            fixed_values.append(datetime.datetime.strptime(v[0], '%Y-%m-%d').date())  # making the first value (date) as date object
            for i in v[1:]: # taking all values except the first one (date)
                try:
                    fixed_values.append(float(i.replace(',', '.')))
                except ValueError:
                    fixed_values.append(i)
            fixed_range.append(fixed_values)

        headers = results_rank_updated['valueRanges'][0]['values'][:1][0]

        # ['Time_key', 'Ticker', 'Полное наименование компании', 'Сектор', 'Страна', 'Рыночная капитализация, $млн.', 'Стоимость компании, $млн.', 'P/S', 'P/E', 'P/B', 'Маржинальность', 'Стоимость компании / Выручка',
        #  'Стоимость компании / EBITDA', 'Годовая дивидендная доходность', 'Див.доходность за 5 лет', 'Крайняя дата выплаты дивидендов', 'FreeCashFlow', 'DebtToEquity', 'ROA_ReturnOnAssets', 'EBITDA', 'TargetMedianPr
        # ice', 'NumberOfAnalystOpinions', 'Trailing_EPS_EarningsPerShare', 'verdict_whole_period', 'probability_to_drop_over_40', 'ma_buy_now_10_50_decisions', 'ma_buy_now_5_10_decisions', 'latest_ma_50', 'latest_ma_
        # 10', 'latest_ma_5', 'latest_Close']

        df_1 = pd.DataFrame(fixed_range, columns=headers)
        df_1['Rank-MarketCap'] = df_1['Рыночная капитализация, $млн.'].rank(ascending=True)
        df_1['Rank-Стоимость компании'] = df_1['Стоимость компании, $млн.'].rank(ascending=True)
        df_1['normalized_PS'] = [round(float(df_1.loc[value, 'P/S'])+1000, 2) if df_1.loc[value, 'P/S'] >0 else round(float(df_1.loc[value, 'P/S'])+10000 ,2) for value in df_1.index]
        df_1['Rank-PS'] = df_1['normalized_PS'].rank(ascending=False)
        
        # и так. далее - заменить все, далее - вставляем ранги и проводим группировку в итоговый свод

        # parameters for the sheet_1
        # Рыночная капитализация, $млн. ; Стоимость компании, $млн. ; P / S ; P / E ; P / B ; Маржинальность ; FreeCashFlow ; DebtToEquity ; ROA_ReturnOnAssets ; EBITDA ; TargetMedianPrice ; verdict_whole_period ; probability_to_drop_over_40 ; ma_buy_now_10_50_decisions ; ma_buy_now_5_10_decisions]
        params_res1 = [15, 1, 1, 1, 1, 14, 13, 5, 3, 1, 2, 11, 12, 1, 1]



if __name__ == '__main__':
    RankingClass().spreadsheet_forming()
