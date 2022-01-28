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
        httpAuth = credentials.authorize(httplib2.Http())  # Авторизуемся в системе
        self.service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)  # Выбираем работу с таблицами и 4 версию API
        '''
        CREDENTIALS_FILE = 'stock-spreadsheets-9974a749b7e4.json'
        ranking_page = '1C_uAagRb_GV7tu8X1fbJIM9SRtH3bAcc-n61SP8muXg'
        credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        httpAuth = credentials.authorize(httplib2.Http())  # Авторизуемся в системе
        service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)  # Выбираем работу с таблицами и 4 версию API
        '''

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

        # performing the ranking
        df_1 = pd.DataFrame(fixed_range, columns=headers)
        df_1['Rank-MarketCap'] = df_1['Рыночная капитализация, $млн.'].rank(ascending=True).astype(int)
        df_1['Rank-Стоимость компании'] = df_1['Стоимость компании, $млн.'].rank(ascending=True).astype(int)
        df_1['normalized_PS'] = [round(float(df_1.loc[value, 'P/S'])+1000, 2) if df_1.loc[value, 'P/S'] >0 else round(float(df_1.loc[value, 'P/S'])+10000 ,2) for value in df_1.index]
        df_1['Rank-PS'] = df_1['normalized_PS'].rank(ascending=False).astype(int)
        df_1['normalized_PE'] = [round(float(df_1.loc[value, 'P/E']) + 1000, 2) if df_1.loc[value, 'P/E'] > 0 else round(float(df_1.loc[value, 'P/E']) + 10000, 2) for value in df_1.index]
        df_1['Rank-PE'] = df_1['normalized_PE'].rank(ascending=False).astype(int)
        df_1['normalized_PB'] = [round(float(100000), 2) if type(df_1.loc[value, 'P/B']) == str else round(float(df_1.loc[value, 'P/B']) + 1000, 2) if df_1.loc[value, 'P/B'] > 0 else round(float(df_1.loc[value, 'P/B']) + 10000, 2)  for value in df_1.index]
        df_1['Rank-PB'] = df_1['normalized_PB'].rank(ascending=False).astype(int)
        df_1['normalized_Mar'] = [round(float(df_1.loc[value, 'Маржинальность']) + 100, 2) for value in df_1.index]
        df_1['Rank-Margin'] = df_1['normalized_Mar'].rank(ascending=True).astype(int)
        df_1['normalized_FCF'] = [round(float(df_1.loc[value, 'FreeCashFlow']) + 999999999999, 0) for value in df_1.index]
        df_1['Rank-FCF'] = df_1['normalized_FCF'].rank(ascending=True).astype(int)
        df_1['Rank-Debt'] = df_1['DebtToEquity'].rank(ascending=False).astype(int)
        df_1['normalized_ROA'] = [round(float(df_1.loc[value, 'ROA_ReturnOnAssets']) + 1, 10) for value in df_1.index]
        df_1['Rank-ROA'] = df_1['normalized_ROA'].rank(ascending=True).astype(int)
        df_1['normalized_EBITDA'] = [round(float(df_1.loc[value, 'EBITDA']) + 999999999999, 0) for value in df_1.index]
        df_1['Rank-EBITDA'] = df_1['normalized_EBITDA'].rank(ascending=True).astype(int)
        df_1['normalized_Target'] = [round(float(df_1.loc[value, 'TargetMedianPrice']/df_1.loc[value, 'latest_Close']), 2) if (df_1.loc[value, 'TargetMedianPrice'] >0 and df_1.loc[value, 'latest_Close'] >0) else round(float(0.99), 0) for value in df_1.index]
        df_1['Rank-Target'] = df_1['normalized_Target'].rank(ascending=True).astype(int)
        df_1['normalized_Long'] = [round(float(df_1.loc[value, 'verdict_whole_period']) + 1000, 0) for value in df_1.index]
        df_1['Rank-Long'] = df_1['normalized_Long'].rank(ascending=True).astype(int)
        df_1['Rank-DropProb'] = df_1['probability_to_drop_over_40'].rank(ascending=False).astype(int)
        df_1['normalized_1050_slope'] = [round(float(df_1.loc[value, 'ma_buy_now_10_50_decisions']) + 100, 0) for value in df_1.index]
        df_1['Rank-1050_slope'] = df_1['normalized_1050_slope'].rank(ascending=True).astype(int)
        df_1['normalized_5_10_slope'] = [round(float(df_1.loc[value, 'ma_buy_now_5_10_decisions']) + 100, 0) for value in df_1.index]
        df_1['Rank-5_10_slope'] = df_1['normalized_5_10_slope'].rank(ascending=True).astype(int)
        df_1['Rank_formula'] = [round(float(df_1.loc[value, 'Rank-MarketCap']*15 +
                                            df_1.loc[value, 'Rank-Стоимость компании']) +
                                            df_1.loc[value, 'Rank-PS'] +
                                            df_1.loc[value, 'Rank-PE'] +
                                            df_1.loc[value, 'Rank-PB'] +
                                            df_1.loc[value, 'Rank-Margin']*14 +
                                            df_1.loc[value, 'Rank-FCF']*13 +
                                            df_1.loc[value, 'Rank-Debt']*5 +
                                            df_1.loc[value, 'Rank-ROA']*3 +
                                            df_1.loc[value, 'Rank-EBITDA'] +
                                            df_1.loc[value, 'Rank-Target']*2 +
                                            df_1.loc[value, 'Rank-Long']*11 +
                                            df_1.loc[value, 'Rank-DropProb']*12 +
                                            df_1.loc[value, 'Rank-1050_slope'] +
                                            df_1.loc[value, 'Rank-5_10_slope'], 0) for value in df_1.index]
        df_1['Rank_FINAL'] = df_1['Rank_formula'].rank(ascending=True).astype(int)
        rank_sum = df_1['Rank_FINAL'].cumsum().values.tolist()[-1]
        df_1['Rate_Share'] = [round(float(df_1.loc[value, 'Rank_FINAL']) / rank_sum, 50) for value in df_1.index]
        df_1.sort_values("Rate_Share", ascending=False, inplace=True)
        df_1['Cumm'] = df_1['Rate_Share'].cumsum()
        df_1['Share_Rank'] = [int(1) if df_1.loc[value, 'Cumm'] < 0.039  else int(2) if df_1.loc[value, 'Cumm'] < 0.15  else int(3) for value in df_1.index]

        # df_1.drop(columns=['Rate_Share'])

        # self.SheetSavingLocal(df_1)
        self.G_Sheet_filling(df_1)


    def SheetSavingLocal(self, dataset):
        output_dir = f'C:\\Users\\Ilia\\Documents\\Python_projects\\Stock_analysis\\baseline_analysis\\stock_rank\\G2_test_output.xlsx'
        writer = pd.ExcelWriter(output_dir, engine='xlsxwriter')
        dataset.to_excel(writer, sheet_name='new', index=True)
        writer.save()
        print(f'The result is saved locally!')


    def G_Sheet_filling(self, dataframe):

        # working with the insiders deals page - first, reading the current data to clear them up
        stock_report_page = '11lzBveJVUSqtFJHLvy9Z3vcvqaBaFzuciFiHDAj0Nvg'
        page = 'Report'
        report_page_data = self.service.spreadsheets().values().get(spreadsheetId=stock_report_page, range=f'{page}!A:BJ',
                                                                    valueRenderOption='FORMATTED_VALUE',
                                                                    dateTimeRenderOption='FORMATTED_STRING').execute()

        # report_page_df = pd.DataFrame(report_page_data.get("values")[1:], columns=report_page_data.get("values")[0])  # in case if the df type is needed in future
        sheet_data = report_page_data.get("values")
        headers = report_page_data.get("values")[0]

        # clear_data
        clear_up_range = []  # выбираем заполненные значения, определяем нулевую матрицу для обнуления страницы
        for _ in sheet_data:  # число строк с текущим заполнением
            clear_up_range.append([str('')] * len(headers))

        null_matrix = self.service.spreadsheets().values().batchUpdate(spreadsheetId=stock_report_page, body={
            "valueInputOption": "USER_ENTERED",
            "data": [{"range": f"{page}",
                      "majorDimension": "ROWS",
                      "values": clear_up_range}]
        }).execute()

        # making appropriate range from the new dataframe
        new_data_values = dataframe.values.tolist()
        new_d = [dataframe.columns.values.tolist()]
        for i in new_data_values:
            new_d.append([str(i[:1][0])] + i[1:])
        print(f'{new_d[0]}\n\n\n {new_d[1]}')


        resource = {"majorDimension": "ROWS", "values": new_d}
        range = f"{page}!A:BJ";
        self.service.spreadsheets().values().append(
            spreadsheetId=stock_report_page,
            range=range,
            body=resource,
            valueInputOption="USER_ENTERED"
        ).execute()


if __name__ == '__main__':
    RankingClass().preparing_rank_sheets()
