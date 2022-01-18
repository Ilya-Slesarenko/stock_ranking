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
        df_needed = df_1[['Time_key', 'latest_Close']].groupby(['Time_key']).sum().reset_index()
        self.Sheet_filling(df_needed)


    def Sheet_filling(self, dataframe):

        # first, reading the current data to clear them up
        report_page = '11lzBveJVUSqtFJHLvy9Z3vcvqaBaFzuciFiHDAj0Nvg'
        report_page_data = self.service.spreadsheets().values().get(spreadsheetId=report_page, range = 'w2w_change!A:B',
                                                                                 valueRenderOption='FORMATTED_VALUE',
                                                                                 dateTimeRenderOption='FORMATTED_STRING').execute()

        #report_page_df = pd.DataFrame(report_page_data.get("values")[1:], columns=report_page_data.get("values")[0])  # in case if the df type is needed in future
        rank_sheet = report_page_data.get("values")
        rank_head = report_page_data.get("values")[0]

        # clear_data
        rank_clear_up_range = []  # выбираем заполненные значения, определяем нулевую матрицу для обнуления страницы
        for _ in rank_sheet:  # число строк с текущим заполнением
            rank_clear_up_range.append([str('')] * len(rank_head))

        null_matrix = self.service.spreadsheets().values().batchUpdate(spreadsheetId=report_page, body={
            "valueInputOption": "USER_ENTERED",
            "data": [{"range": "w2w_change",
                      "majorDimension": "ROWS",
                      "values": rank_clear_up_range}]
        }).execute()

        # making appropriate range from the new dataframe
        new_data = dataframe.values.tolist()
        new_d = [dataframe.columns.values.tolist()]
        for i in new_data:
            new_d.append(i)

        # заполнение новыми данными
        results = self.service.spreadsheets().values().batchUpdate(spreadsheetId=report_page, body={
            "valueInputOption": "USER_ENTERED",
            "data": [{"range": "w2w_change",
                      "majorDimension": "ROWS",
                      "values": new_d}]
        }).execute()

        print(f' Done, we\'re all set!')
