# -*- coding: utf-8 -*-

import warnings, httplib2, apiclient.discovery
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
        httpAuth = credentials.authorize(httplib2.Http())  # Авторизуемся в системе
        self.service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)  # Выбираем работу с таблицами и 4 версию API


    # stock_market fundamental data from yfinance
    def total_change_calc(self):
        #reading the updated result
        results_rank_updated = self.service.spreadsheets().values().batchGet(spreadsheetId=self.ranking_page, ranges='Retro!A:AE', valueRenderOption='FORMATTED_VALUE', dateTimeRenderOption='FORMATTED_STRING').execute()
        rank_sheet_values_updated = results_rank_updated['valueRanges'][0]['values'][1:]

        fixed_range = []
        for v in rank_sheet_values_updated:
            fixed_values = []
            for i in v:
                try:
                    fixed_values.append(int(i.split(',')[0]))
                except ValueError:
                    fixed_values.append(i)
            fixed_range.append(fixed_values)

        headers = results_rank_updated['valueRanges'][0]['values'][:1][0]

        df_1 = pd.DataFrame(fixed_range, columns=headers)
        df_needed = df_1[['Time_key', 'latest_Close']].groupby(['Time_key']).sum()
        self.Sheet_filling(df_needed)


    def Sheet_filling(self, dataframe):

        # working with the insiders deals page - first, reading the current data to clear them up
        report_page = '1C_uAagRb_GV7tu8X1fbJIM9SRtH3bAcc-n61SP8muXg'
        report_page_data = self.service.spreadsheets().values().batchGet(spreadsheetId=report_page,
                                                                                 ranges='w2w_change!A:I',
                                                                                 valueRenderOption='FORMATTED_VALUE',
                                                                                 dateTimeRenderOption='FORMATTED_STRING').execute()
        rank_sheet_values = report_page_data['valueRanges'][0]['values']
        rank_head = rank_sheet_values[0]

        # clear_data
        rank_clear_up_range = []  # выбираем заполненные значения, определяем нулевую матрицу для обнуления страницы
        for _ in rank_sheet_values:  # число строк с текущим заполнением
            rank_clear_up_range.append([str('')] * len(rank_head))

        null_matrix = self.service.spreadsheets().values().batchUpdate(spreadsheetId=report_page, body={
            "valueInputOption": "USER_ENTERED",
            "data": [{"range": "w2w_change",
                      "majorDimension": "ROWS",
                      "values": rank_clear_up_range}]
        }).execute()

        # заполнение новыми данными
        results = self.service.spreadsheets().values().batchUpdate(spreadsheetId=report_page, body={
            "valueInputOption": "USER_ENTERED",
            "data": [{"range": "w2w_change",
                      "majorDimension": "ROWS",
                      "values": dataframe}]
        }).execute()
