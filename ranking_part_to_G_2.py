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
        self.stock_report_page = '11lzBveJVUSqtFJHLvy9Z3vcvqaBaFzuciFiHDAj0Nvg'
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
        results_rank_updated = self.service.spreadsheets().values().batchGet(spreadsheetId=self.ranking_page, ranges='Update!A:AE', valueRenderOption='FORMATTED_VALUE', dateTimeRenderOption='FORMATTED_STRING').execute()
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
        df_R1 = pd.DataFrame(fixed_range, columns=headers)
        df_R1['Rank-MarketCap'] = df_R1['Рыночная капитализация, $млн.'].rank(ascending=True).astype(int)
        df_R1['Rank-Стоимость компании'] = df_R1['Стоимость компании, $млн.'].rank(ascending=True).astype(int)
        df_R1['normalized_PS'] = [round(float(df_R1.loc[value, 'P/S'])+1000, 2) if df_R1.loc[value, 'P/S'] >0 else round(float(df_R1.loc[value, 'P/S'])+10000 ,2) for value in df_R1.index]
        df_R1['Rank-PS'] = df_R1['normalized_PS'].rank(ascending=False).astype(int)
        df_R1['normalized_PE'] = [round(float(df_R1.loc[value, 'P/E']) + 1000, 2) if df_R1.loc[value, 'P/E'] > 0 else round(float(df_R1.loc[value, 'P/E']) + 10000, 2) for value in df_R1.index]
        df_R1['Rank-PE'] = df_R1['normalized_PE'].rank(ascending=False).astype(int)
        df_R1['normalized_PB'] = [round(float(100000), 2) if type(df_R1.loc[value, 'P/B']) == str else round(float(df_R1.loc[value, 'P/B']) + 1000, 2) if df_R1.loc[value, 'P/B'] > 0 else round(float(df_R1.loc[value, 'P/B']) + 10000, 2)  for value in df_R1.index]
        df_R1['Rank-PB'] = df_R1['normalized_PB'].rank(ascending=False).astype(int)
        df_R1['normalized_Mar'] = [round(float(df_R1.loc[value, 'Маржинальность']) + 100, 2) for value in df_R1.index]
        df_R1['Rank-Margin'] = df_R1['normalized_Mar'].rank(ascending=True).astype(int)
        df_R1['normalized_FCF'] = [round(float(df_R1.loc[value, 'FreeCashFlow']) + 999999999999, 0) for value in df_R1.index]
        df_R1['Rank-FCF'] = df_R1['normalized_FCF'].rank(ascending=True).astype(int)
        df_R1['Rank-Debt'] = df_R1['DebtToEquity'].rank(ascending=False).astype(int)
        df_R1['normalized_ROA'] = [round(float(df_R1.loc[value, 'ROA_ReturnOnAssets']) + 1, 10) for value in df_R1.index]
        df_R1['Rank-ROA'] = df_R1['normalized_ROA'].rank(ascending=True).astype(int)
        df_R1['normalized_EBITDA'] = [round(float(df_R1.loc[value, 'EBITDA']) + 999999999999, 0) for value in df_R1.index]
        df_R1['Rank-EBITDA'] = df_R1['normalized_EBITDA'].rank(ascending=True).astype(int)
        df_R1['normalized_Target'] = [round(float(df_R1.loc[value, 'TargetMedianPrice']/df_R1.loc[value, 'latest_Close']), 2) if (df_R1.loc[value, 'TargetMedianPrice'] >0 and df_R1.loc[value, 'latest_Close'] >0) else round(float(0.99), 0) for value in df_R1.index]
        df_R1['Rank-Target'] = df_R1['normalized_Target'].rank(ascending=True).astype(int)
        df_R1['normalized_Long'] = [round(float(df_R1.loc[value, 'verdict_whole_period']) + 1000, 0) for value in df_R1.index]
        df_R1['Rank-Long'] = df_R1['normalized_Long'].rank(ascending=True).astype(int)
        df_R1['Rank-DropProb'] = df_R1['probability_to_drop_over_40'].rank(ascending=False).astype(int)
        df_R1['normalized_1050_slope'] = [round(float(df_R1.loc[value, 'ma_buy_now_10_50_decisions']) + 100, 0) for value in df_R1.index]
        df_R1['Rank-1050_slope'] = df_R1['normalized_1050_slope'].rank(ascending=True).astype(int)
        df_R1['normalized_5_10_slope'] = [round(float(df_R1.loc[value, 'ma_buy_now_5_10_decisions']) + 100, 0) for value in df_R1.index]
        df_R1['Rank-5_10_slope'] = df_R1['normalized_5_10_slope'].rank(ascending=True).astype(int)
        df_R1['Rank_formula'] = [round(float(df_R1.loc[value, 'Rank-MarketCap']*12 +
                                            df_R1.loc[value, 'Rank-Стоимость компании']) +
                                            df_R1.loc[value, 'Rank-PS'] +
                                            df_R1.loc[value, 'Rank-PE'] +
                                            df_R1.loc[value, 'Rank-PB'] +
                                            df_R1.loc[value, 'Rank-Margin'] +
                                            df_R1.loc[value, 'Rank-FCF'] +
                                            df_R1.loc[value, 'Rank-Debt'] +
                                            df_R1.loc[value, 'Rank-ROA']*13 +
                                            df_R1.loc[value, 'Rank-EBITDA'] +
                                            df_R1.loc[value, 'Rank-Target'] +
                                            df_R1.loc[value, 'Rank-Long']*8 +
                                            df_R1.loc[value, 'Rank-DropProb'] +
                                            df_R1.loc[value, 'Rank-1050_slope'] +
                                            df_R1.loc[value, 'Rank-5_10_slope']*15 , 0) for value in df_R1.index]

        df_R1['Rank_FINAL'] = df_R1['Rank_formula'].rank(ascending=True).astype(int)
        rank_sum = df_R1['Rank_FINAL'].cumsum().values.tolist()[-1]
        df_R1['Rate_Share'] = [round(float(df_R1.loc[value, 'Rank_FINAL']) / rank_sum, 50) for value in df_R1.index]
        df_R1.sort_values("Rate_Share", ascending=False, inplace=True)
        df_R1['Cumm'] = df_R1['Rate_Share'].cumsum()
        df_R1['Share_Rank'] = [int(1) if df_R1.loc[value, 'Cumm'] < 0.039  else int(2) if df_R1.loc[value, 'Cumm'] < 0.15  else int(3) for value in df_R1.index]
        # df_R1.drop(columns=['Rate_Share'])

        # self.SheetSavingLocal(df_R1, 'R1')
        self.G_Sheet_filling(df_R1, 'R1', 'A:BJ')
        print(f'R1 Done')


        #doing the same, with R2 ranking
        df_R2 = pd.DataFrame(fixed_range, columns=headers)
        df_R2['Rank-MarketCap'] = df_R2['Рыночная капитализация, $млн.'].rank(ascending=True).astype(int)
        df_R2['Rank-Стоимость компании'] = df_R2['Стоимость компании, $млн.'].rank(ascending=True).astype(int)
        df_R2['normalized_PS'] = [round(float(df_R2.loc[value, 'P/S']) + 1000, 2) if df_R2.loc[value, 'P/S'] > 0 else round(float(df_R2.loc[value, 'P/S']) + 10000, 2) for value in df_R2.index]
        df_R2['Rank-PS'] = df_R2['normalized_PS'].rank(ascending=False).astype(int)
        df_R2['normalized_PE'] = [round(float(df_R2.loc[value, 'P/E']) + 1000, 2) if df_R2.loc[value, 'P/E'] > 0 else round(float(df_R2.loc[value, 'P/E']) + 10000, 2) for value in df_R2.index]
        df_R2['Rank-PE'] = df_R2['normalized_PE'].rank(ascending=False).astype(int)
        df_R2['normalized_PB'] = [round(float(100000), 2) if type(df_R2.loc[value, 'P/B']) == str else round(float(df_R2.loc[value, 'P/B']) + 1000, 2) if df_R2.loc[value, 'P/B'] > 0 else round(float(df_R2.loc[value, 'P/B']) + 10000, 2) for value in df_R2.index]
        df_R2['Rank-PB'] = df_R2['normalized_PB'].rank(ascending=False).astype(int)
        df_R2['normalized_Mar'] = [round(float(df_R2.loc[value, 'Маржинальность']) + 100, 2) for value in df_R2.index]
        df_R2['Rank-Margin'] = df_R2['normalized_Mar'].rank(ascending=True).astype(int)
        df_R2['normalized_FCF'] = [round(float(df_R2.loc[value, 'FreeCashFlow']) + 999999999999, 0) for value in df_R2.index]
        df_R2['Rank-FCF'] = df_R2['normalized_FCF'].rank(ascending=True).astype(int)
        df_R2['Rank-Debt'] = df_R2['DebtToEquity'].rank(ascending=False).astype(int)
        df_R2['normalized_ROA'] = [round(float(df_R2.loc[value, 'ROA_ReturnOnAssets']) + 1, 10) for value in df_R2.index]
        df_R2['Rank-ROA'] = df_R2['normalized_ROA'].rank(ascending=True).astype(int)
        df_R2['normalized_EBITDA'] = [round(float(df_R2.loc[value, 'EBITDA']) + 999999999999, 0) for value in df_R2.index]
        df_R2['Rank-EBITDA'] = df_R2['normalized_EBITDA'].rank(ascending=True).astype(int)
        df_R2['normalized_Target'] = [round(float(df_R2.loc[value, 'TargetMedianPrice'] / df_R2.loc[value, 'latest_Close']), 2) if (df_R2.loc[value, 'TargetMedianPrice'] > 0 and df_R2.loc[value, 'latest_Close'] > 0) else round(float(0.99), 0) for value in df_R2.index]
        df_R2['Rank-Target'] = df_R2['normalized_Target'].rank(ascending=True).astype(int)
        df_R2['normalized_Long'] = [round(float(df_R2.loc[value, 'verdict_whole_period']) + 1000, 0) for value in df_R2.index]
        df_R2['Rank-Long'] = df_R2['normalized_Long'].rank(ascending=True).astype(int)
        df_R2['Rank-DropProb'] = df_R2['probability_to_drop_over_40'].rank(ascending=False).astype(int)
        df_R2['normalized_1050_slope'] = [round(float(df_R2.loc[value, 'ma_buy_now_10_50_decisions']) + 100, 0) for value in df_R2.index]
        df_R2['Rank-1050_slope'] = df_R2['normalized_1050_slope'].rank(ascending=True).astype(int)
        df_R2['normalized_5_10_slope'] = [round(float(df_R2.loc[value, 'ma_buy_now_5_10_decisions']) + 100, 0) for value in df_R2.index]
        df_R2['Rank-5_10_slope'] = df_R2['normalized_5_10_slope'].rank(ascending=True).astype(int)
        df_R2['Rank_formula'] = [round(float(df_R2.loc[value, 'Rank-MarketCap'] * 15 +
                                             df_R2.loc[value, 'Rank-Стоимость компании']) +
                                       df_R2.loc[value, 'Rank-PS'] +
                                       df_R2.loc[value, 'Rank-PE'] +
                                       df_R2.loc[value, 'Rank-PB'] +
                                       df_R2.loc[value, 'Rank-Margin'] * 14 +
                                       df_R2.loc[value, 'Rank-FCF'] * 13 +
                                       df_R2.loc[value, 'Rank-Debt'] * 5 +
                                       df_R2.loc[value, 'Rank-ROA'] * 3 +
                                       df_R2.loc[value, 'Rank-EBITDA'] +
                                       df_R2.loc[value, 'Rank-Target'] * 2 +
                                       df_R2.loc[value, 'Rank-Long'] * 11 +
                                       df_R2.loc[value, 'Rank-DropProb'] * 12 +
                                       df_R2.loc[value, 'Rank-1050_slope'] +
                                       df_R2.loc[value, 'Rank-5_10_slope'], 0) for value in df_R2.index]
        df_R2['Rank_FINAL'] = df_R2['Rank_formula'].rank(ascending=True).astype(int)
        rank_sum = df_R2['Rank_FINAL'].cumsum().values.tolist()[-1]
        df_R2['Rate_Share'] = [round(float(df_R2.loc[value, 'Rank_FINAL']) / rank_sum, 50) for value in df_R2.index]
        df_R2.sort_values("Rate_Share", ascending=False, inplace=True)
        df_R2['Cumm'] = df_R2['Rate_Share'].cumsum()
        df_R2['Share_Rank'] = [int(1) if df_R2.loc[value, 'Cumm'] < 0.039 else int(2) if df_R2.loc[value, 'Cumm'] < 0.15 else int(3) for value in df_R2.index]
        # df_R2.drop(columns=['Rate_Share'])

        # self.SheetSavingLocal(df_R2, 'R2')
        self.G_Sheet_filling(df_R2, 'R2', 'A:BJ')
        print(f'R2 Done')


        #doing the same with R3 ranking
        df_R3 = pd.DataFrame(fixed_range, columns=headers)
        df_R3['Rank-MarketCap'] = df_R3['Рыночная капитализация, $млн.'].rank(ascending=True).astype(int)
        df_R3['Rank-Стоимость компании'] = df_R3['Стоимость компании, $млн.'].rank(ascending=True).astype(int)
        df_R3['normalized_PS'] = [round(float(df_R3.loc[value, 'P/S']) + 1000, 2) if df_R3.loc[value, 'P/S'] > 0 else round(float(df_R3.loc[value, 'P/S']) + 10000, 2) for value in df_R3.index]
        df_R3['Rank-PS'] = df_R3['normalized_PS'].rank(ascending=False).astype(int)
        df_R3['normalized_PE'] = [round(float(df_R3.loc[value, 'P/E']) + 1000, 2) if df_R3.loc[value, 'P/E'] > 0 else round(float(df_R3.loc[value, 'P/E']) + 10000, 2) for value in df_R3.index]
        df_R3['Rank-PE'] = df_R3['normalized_PE'].rank(ascending=False).astype(int)
        df_R3['normalized_PB'] = [round(float(100000), 2) if type(df_R3.loc[value, 'P/B']) == str else round(float(df_R3.loc[value, 'P/B']) + 1000, 2) if df_R3.loc[value, 'P/B'] > 0 else round(float(df_R3.loc[value, 'P/B']) + 10000, 2) for value in df_R3.index]
        df_R3['Rank-PB'] = df_R3['normalized_PB'].rank(ascending=False).astype(int)
        df_R3['normalized_Mar'] = [round(float(df_R3.loc[value, 'Маржинальность']) + 100, 2) for value in df_R3.index]
        df_R3['Rank-Margin'] = df_R3['normalized_Mar'].rank(ascending=True).astype(int)
        df_R3['normalized_FCF'] = [round(float(df_R3.loc[value, 'FreeCashFlow']) + 999999999999, 0) for value in df_R3.index]
        df_R3['Rank-FCF'] = df_R3['normalized_FCF'].rank(ascending=True).astype(int)
        df_R3['Rank-Debt'] = df_R3['DebtToEquity'].rank(ascending=False).astype(int)
        df_R3['normalized_ROA'] = [round(float(df_R3.loc[value, 'ROA_ReturnOnAssets']) + 1, 10) for value in df_R3.index]
        df_R3['Rank-ROA'] = df_R3['normalized_ROA'].rank(ascending=True).astype(int)
        df_R3['normalized_EBITDA'] = [round(float(df_R3.loc[value, 'EBITDA']) + 999999999999, 0) for value in df_R3.index]
        df_R3['Rank-EBITDA'] = df_R3['normalized_EBITDA'].rank(ascending=True).astype(int)
        df_R3['normalized_Target'] = [round(float(df_R3.loc[value, 'TargetMedianPrice'] / df_R3.loc[value, 'latest_Close']), 2) if (df_R3.loc[value, 'TargetMedianPrice'] > 0 and df_R3.loc[value, 'latest_Close'] > 0) else round(float(0.99), 0) for value in df_R3.index]
        df_R3['Rank-Target'] = df_R3['normalized_Target'].rank(ascending=True).astype(int)
        df_R3['normalized_Long'] = [round(float(df_R3.loc[value, 'verdict_whole_period']) + 1000, 0) for value in df_R3.index]
        df_R3['Rank-Long'] = df_R3['normalized_Long'].rank(ascending=True).astype(int)
        df_R3['Rank-DropProb'] = df_R3['probability_to_drop_over_40'].rank(ascending=False).astype(int)
        df_R3['normalized_1050_slope'] = [round(float(df_R3.loc[value, 'ma_buy_now_10_50_decisions']) + 100, 0) for value in df_R3.index]
        df_R3['Rank-1050_slope'] = df_R3['normalized_1050_slope'].rank(ascending=True).astype(int)
        df_R3['normalized_5_10_slope'] = [round(float(df_R3.loc[value, 'ma_buy_now_5_10_decisions']) + 100, 0) for value in df_R3.index]
        df_R3['Rank-5_10_slope'] = df_R3['normalized_5_10_slope'].rank(ascending=True).astype(int)
        df_R3['Rank_formula'] = [round(float(df_R3.loc[value, 'Rank-MarketCap'] *1 +
                                             df_R3.loc[value, 'Rank-Стоимость компании']) +
                                       df_R3.loc[value, 'Rank-PS']*15 +
                                       df_R3.loc[value, 'Rank-PE'] +
                                       df_R3.loc[value, 'Rank-PB']*5 +
                                       df_R3.loc[value, 'Rank-Margin'] *4 +
                                       df_R3.loc[value, 'Rank-FCF'] * 1 +
                                       df_R3.loc[value, 'Rank-Debt'] *2 +
                                       df_R3.loc[value, 'Rank-ROA'] *8 +
                                       df_R3.loc[value, 'Rank-EBITDA'] *3 +
                                       df_R3.loc[value, 'Rank-Target'] *14 +
                                       df_R3.loc[value, 'Rank-Long'] *1 +
                                       df_R3.loc[value, 'Rank-DropProb'] *1 +
                                       df_R3.loc[value, 'Rank-1050_slope'] *10 +
                                       df_R3.loc[value, 'Rank-5_10_slope'] *1 , 0) for value in df_R3.index]

        df_R3['Rank_FINAL'] = df_R3['Rank_formula'].rank(ascending=True).astype(int)
        rank_sum = df_R3['Rank_FINAL'].cumsum().values.tolist()[-1]
        df_R3['Rate_Share'] = [round(float(df_R3.loc[value, 'Rank_FINAL']) / rank_sum, 50) for value in df_R3.index]
        df_R3.sort_values("Rate_Share", ascending=False, inplace=True)
        df_R3['Cumm'] = df_R3['Rate_Share'].cumsum()
        df_R3['Share_Rank'] = [int(1) if df_R3.loc[value, 'Cumm'] < 0.039 else int(2) if df_R3.loc[value, 'Cumm'] < 0.15 else int(3) for value in df_R3.index]
        # df_R3.drop(columns=['Rate_Share'])

        # self.SheetSavingLocal(df_R3, 'R3')
        self.G_Sheet_filling(df_R3, 'R3', 'A:BJ')
        print(f'R3 Done')

    def target_changes(self):
        retro_ranks = self.service.spreadsheets().values().batchGet(spreadsheetId=self.ranking_page, ranges='Retro!A:AE', valueRenderOption='FORMATTED_VALUE', dateTimeRenderOption='FORMATTED_STRING').execute()
        # retro_ranks = service.spreadsheets().values().batchGet(spreadsheetId=ranking_page, ranges='Retro!A:AE', valueRenderOption='FORMATTED_VALUE', dateTimeRenderOption='FORMATTED_STRING').execute()
        retro_rank_sheet_values = retro_ranks['valueRanges'][0]['values'][1:]
        retro_dates_list = []
        for d in retro_rank_sheet_values:
            try:
                retro_date = datetime.datetime.strptime(d[0], '%Y-%m-%d').date()
            except:
                retro_date = datetime.datetime.strptime(d[0], '%d.%m.%Y').date()
            if retro_date not in retro_dates_list:
                retro_dates_list.append(retro_date)


        list_last = []
        list_prev = []
        for i in retro_rank_sheet_values:
            try:
                retro_date = datetime.datetime.strptime(i[0], '%Y-%m-%d').date()
            except:
                retro_date = datetime.datetime.strptime(i[0], '%d.%m.%Y').date()
            if retro_date == retro_dates_list[-2]:
                list_prev.append(i)
            elif retro_date == retro_dates_list[-1]:
                list_last.append(i)
            else:
                pass

        headers = ['Time_key', 'Change_since_t_key', 'Ticker', 'Comp_Name', 'Target_now', 'Target_was', 'Target_change_usd', 'Target_change_share', 'Close_now', 'Close_prev', 'Module_share']
        targets_changed_list = []
        for a in list_last:
            float_target_a = float(a[20].replace(',','.'))
            for b in list_prev:
                float_target_b = float(b[20].replace(',','.'))
                if a[1] == b[1] and float_target_a != float_target_b:
                    change_delta = float_target_a - float_target_b
                    share_change_pct = (change_delta / float_target_b)*100
                    module_share_pct = share_change_pct if share_change_pct >= 0 else share_change_pct * -1
                    targets_changed_list.append([a[0], b[0], a[1], a[2], a[20], b[20], round(change_delta, 2), round(share_change_pct, 2), a[30], b[30], round(module_share_pct ,2)])

        sorted_tcl = sorted(targets_changed_list, key=lambda x: x[-1], reverse = True)
        tcl_df = pd.DataFrame(sorted_tcl, columns=headers)
        self.G_Sheet_filling(tcl_df, 'target_changed', 'A:K')
        print('Target_change done')


    def G_Sheet_filling(self, dataframe, sheet_title, columns_range):
        # working with the insiders deals page - first, reading the current data to clear them up
        page = sheet_title
        columns_r = columns_range
        report_page_data = self.service.spreadsheets().values().get(spreadsheetId=self.stock_report_page, range=f'{page}!{columns_r}', valueRenderOption='FORMATTED_VALUE', dateTimeRenderOption='FORMATTED_STRING').execute()
        # report_page_data = service.spreadsheets().values().get(spreadsheetId=self.stock_report_page, range=f'{page}!{columns_r}', valueRenderOption='FORMATTED_VALUE', dateTimeRenderOption='FORMATTED_STRING').execute()

        # report_page_df = pd.DataFrame(report_page_data.get("values")[1:], columns=report_page_data.get("values")[0])  # in case if the df type is needed in future
        sheet_data = report_page_data.get("values")
        headers = report_page_data.get("values")[0]

        # clear_data
        clear_up_range = []  # выбираем заполненные значения, определяем нулевую матрицу для обнуления страницы
        for _ in sheet_data:  # число строк с текущим заполнением
            clear_up_range.append([str('')] * len(headers))
        # print(f'\n\n{len(clear_up_range)}\n\n{len(clear_up_range[1])}\n\n')

        null_matrix = self.service.spreadsheets().values().batchUpdate(spreadsheetId=self.stock_report_page, body={
            "valueInputOption": "USER_ENTERED",
            "data": [{"range": f'{page}!{columns_r}',
                      "majorDimension": "ROWS",
                      "values": clear_up_range}]
        }).execute()

        # making appropriate range from the new dataframe
        new_data_values = dataframe.values.tolist()
        new_d = [headers]
        for i in new_data_values:
            new_d.append([str(i[:1][0])] + i[1:])


        new_data_filling = self.service.spreadsheets().values().batchUpdate(spreadsheetId=self.stock_report_page, body={
            "valueInputOption": "USER_ENTERED",
            "data": [{"range": f'{page}!{columns_r}',
                      "majorDimension": "ROWS",
                      "values": new_d}]
        }).execute()


    def w2w_total_change(self):
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
        self.G_Sheet_filling(df_needed, 'w2w_change', 'A:B')
        print('w2w_total_change_done!')


    def PerformAll(self):
        self.preparing_rank_sheets()
        self.target_changes()
        self.w2w_total_change()
        print('We\'re all set!')
