# -*- coding: utf-8 -*-

import logging, random, warnings, httplib2, apiclient.discovery
import numpy as np
from scipy.stats import norm
import pandas as pd
from datetime import datetime, date, timedelta
import yfinance as yf
import pandas_datareader.data as pdr
from oauth2client.service_account import ServiceAccountCredentials

warnings.filterwarnings('ignore')
pd.options.mode.chained_assignment = None  # default='warn'


class RankingClass():
    def __init__(self):
        # Получение списка акций  из готового листа Google Sheet
        self.CREDENTIALS_FILE = 'stock-spreadsheets-9974a749b7e4.json'
        tickers_page = '1s6uIbhIX4IYCmFYhfWgEklFqtLX95ky7GmJNRvVexeM'
        self.ranking_page = '1C_uAagRb_GV7tu8X1fbJIM9SRtH3bAcc-n61SP8muXg'
        credentials = ServiceAccountCredentials.from_json_keyfile_name(self.CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        # credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        httpAuth = credentials.authorize(httplib2.Http())  # Авторизуемся в системе
        self.service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)  # Выбираем работу с таблицами и 4 версию API

        # reading data
        results = self.service.spreadsheets().values().batchGet(spreadsheetId=tickers_page, ranges='A:R', valueRenderOption='FORMATTED_VALUE', dateTimeRenderOption='FORMATTED_STRING').execute()
        sheet_values = results['valueRanges'][0]['values']
        values = sheet_values[1:]  # текущий рабочий список (весь!)

        self.tickers_list = []  # текущий рабочий список для работы с yfinance без излишек (если будет нужен, в скрипте не используется!)
        for i in values:
            if i[-2] == 'yfinance':
                self.tickers_list.append(i[1])

        # making split of tickers pool, so that Google connection wouldn't bring the ConnectionError!
        chunks_arrays = np.array_split(self.tickers_list, int(len(self.tickers_list)/500))  # arrays splited by particular length (500 pcs for our case) in one list
        self.chunks_list = []
        for i in chunks_arrays:
            self.chunks_list.append(i.tolist())

        self.start = date.today() - timedelta(days=365 * 2)
        self.end = date.today()

    def yfinance_data(self, comp):
        try:
            yf.pdr_override()
            data = pdr.get_data_yahoo(comp, self.start, self.end, threads=False)
            # data = pdr.get_data_yahoo(comp, start, end, threads=False)
            data['PriceDiff'] = data['Close'].shift(-1) - data['Close']
            data['Return'] = data['PriceDiff'] / data['Close']
    
            # Create a new column direction.
            # The list cmprehension means: if the price difference is larger than 0, donate as 1, otherwise, doate 0
            data['Direction'] = [1 if data['PriceDiff'].loc[ei] > 0 else 0 for ei in data.index]
    
            # making mean average for 10 and 50 days
            data['ma50'] = data['Close'].rolling(50).mean()
            data['ma10'] = data['Close'].rolling(10).mean()
            data['ma5'] = data['Close'].rolling(5).mean()
    
            data['Shares'] = [1 if data.loc[ei, 'ma10'] > data.loc[ei, 'ma5'] else 0 for ei in data.index]
            data['Close1'] = data['Close'].shift(-1)
            data['Profit'] = [data.loc[ei, 'Close1'] - data.loc[ei, 'Close'] if data.loc[ei, 'Shares'] == 1 else 0 for ei in data.index]
            data['wealth'] = data['Profit'].cumsum()
            verdict_whole_period = round(data['wealth'][-2], 2)   # todo: make sure this is to a unified value
    
            data['LogReturn'] = np.log(data['Close']).shift(-1) - np.log(data['Close'])
            mu = data['LogReturn'].mean()  # approximate mean
            sigma = data['LogReturn'].std(ddof=1)  # variance of the log daily return
    
            # what is the chance of losing over _n_% in a day?
            mu220 = 220 * mu
            sigma220 = 220 ** 0.5 * sigma
            prob_to_drop_over_40 = norm.cdf(-0.4, mu220, sigma220)
            buy_now_10_50__decision = round(data['ma10'][-2] - data['ma50'][-2], 2)  # 'Buy' if ...
            buy_now_5_10__decision = round(data['ma5'][-2] - data['ma10'][-2], 2)  # 'Buy' if ...
    
            listed_values = data.values.tolist()
            latest_close_price = round(listed_values[-1][4], 2)
            latest_ma5 = round(listed_values[-1][-6], 2)
            latest_ma10 = round(listed_values[-1][-7], 2)
            latest_ma50 = round(listed_values[-1][-8], 2)
            stock_list_data = [verdict_whole_period, round(prob_to_drop_over_40 * 100, 2), round(buy_now_10_50__decision, 2), round(buy_now_5_10__decision, 2), latest_ma50, latest_ma10, latest_ma5, latest_close_price]
            checked_stock_list_data = []
            check_list = [None, 'N/A', 'Nan']
            for i in stock_list_data:
                if i in check_list:
                    i = 0
                    checked_stock_list_data.append(i)
                else: checked_stock_list_data.append(i)
    
            return checked_stock_list_data
        
        except:
            checked_stock_list_data = None
            return checked_stock_list_data

    # stock_market fundamental data from yfinance
    def spreadsheet_forming_after_check(self):
        new_results_rank = self.service.spreadsheets().values().batchGet(spreadsheetId=self.ranking_page, ranges='Update!A:AE', valueRenderOption='FORMATTED_VALUE', dateTimeRenderOption='FORMATTED_STRING').execute()
        # new_results_rank = service.spreadsheets().values().batchGet(spreadsheetId=ranking_page, ranges='Update!A:AE', valueRenderOption='FORMATTED_VALUE', dateTimeRenderOption='FORMATTED_STRING').execute()
        rank_sheet_values = new_results_rank['valueRanges'][0]['values']
        data_range = rank_sheet_values[1:]
        if len(data_range) > 1550:
            print(f'seems like the first part worked fine, passing double-work\nCurrently have {len(data_range)} tickers in Update sheet')
        else:
            print(f'gathering data for {len(self.tickers_list)} tickers')

            # reading the ranking page to clear it up
            old_results_rank = self.service.spreadsheets().values().batchGet(spreadsheetId=self.ranking_page, ranges='A:AE', valueRenderOption='FORMATTED_VALUE', dateTimeRenderOption='FORMATTED_STRING').execute()
            # old_results_rank = service.spreadsheets().values().batchGet(spreadsheetId=ranking_page, ranges='A:AE', valueRenderOption='FORMATTED_VALUE', dateTimeRenderOption='FORMATTED_STRING').execute()
            rank_sheet_values = old_results_rank['valueRanges'][0]['values']
            headers = rank_sheet_values[0]

            # clear_data
            rank_clear_up_range = []  # выбираем заполненные значения, определяем нулевую матрицу для обнуления страницы
            for _ in rank_sheet_values:  # число строк с текущим заполнением
                rank_clear_up_range.append([str('')] * len(headers))

            null_matrix = self.service.spreadsheets().values().batchUpdate(spreadsheetId=self.ranking_page, body={
                "valueInputOption": "USER_ENTERED",
                "data": [{"range": "Update",
                          "majorDimension": "ROWS",
                          "values": rank_clear_up_range}]
            }).execute()

            # заполнение "шапки"
            results = self.service.spreadsheets().values().batchUpdate(spreadsheetId=self.ranking_page, body={
                "valueInputOption": "USER_ENTERED",
                "data": [{"range": "Update",
                          "majorDimension": "ROWS",
                          "values": [headers]}]
            }).execute()

            for chunk in self.chunks_list:
                # Коннект к Google Sheet внутри куска тикеров (so that Google connection wouldn't bring the ConnectionError!)
                crede_s = ServiceAccountCredentials.from_json_keyfile_name(self.CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
                http_Auth = crede_s.authorize(httplib2.Http())  # Авторизуемся в системе
                serv_e = apiclient.discovery.build('sheets', 'v4', http=http_Auth)

                for ticker in chunk:
                    from_yfinance = self.yfinance_data(ticker)
                    try:
                        t_info = yf.Ticker(ticker).info

                        try:
                            company_name = t_info.get('shortName')
                        except TypeError:
                            company_name = None

                        try:
                            sector = t_info.get('sector')
                        except TypeError:
                            sector = None

                        try:
                            country = t_info.get('country')
                        except TypeError:
                            country = None

                        try:
                            m_cap = round(t_info.get('marketCap') / 1000000, 2)
                        except TypeError:
                            m_cap = None

                        try:
                            enterp_val = round(t_info.get('enterpriseValue') / 1000000, 2)
                        except TypeError:
                            enterp_val = None

                        try:
                            P_S_12_m = round(t_info.get('priceToSalesTrailing12Months'), 2)
                        except TypeError:
                            P_S_12_m = None

                        try:
                            P_B = round(t_info.get('priceToBook'), 2)
                        except TypeError:
                            P_B = None

                        try:
                            marg = round(t_info.get('profitMargins'), 3)
                        except TypeError:
                            marg = None

                        try:
                            enterprToRev = t_info.get('enterpriseToRevenue')
                        except TypeError:
                            enterprToRev = None

                        try:
                            enterprToEbitda = t_info.get('enterpriseToEbitda')
                        except TypeError:
                            enterprToEbitda = None

                        try:
                            yr_div = round(t_info.get('trailingAnnualDividendYield'), 3) if t_info.get('trailingAnnualDividendYield') is not None else 0
                        except TypeError:
                            yr_div = None

                        try:
                            exDivDate = datetime.fromtimestamp(t_info.get('exDividendDate'))
                        except TypeError:
                            exDivDate = None

                        try:
                            five_yr_div_yield = t_info.get('fiveYearAvgDividendYield') if t_info.get('fiveYearAvgDividendYield') is not None else 0
                        except TypeError:
                            five_yr_div_yield = None

                        try:
                            div_date = exDivDate.strftime('%d.%m.%y')
                        except AttributeError:
                            div_date = 'Без дивидендов'

                        try:
                            FreeCashFlow = t_info.get('freeCashflow') if t_info.get('freeCashflow') is not None else 0
                        except TypeError:
                            FreeCashFlow = None

                        try:
                            DebtToEquity = t_info.get('debtToEquity') if t_info.get('debtToEquity') is not None else 0
                        except TypeError:
                            DebtToEquity = None

                        try:
                            ROA_ReturnOnAssets = t_info.get('returnOnAssets') if t_info.get('returnOnAssets') is not None else 0
                        except TypeError:
                            ROA_ReturnOnAssets = None

                        try:
                            EBITDA = t_info.get('ebitda') if t_info.get('ebitda') is not None else 0
                        except TypeError:
                            EBITDA = None

                        try:
                            TargetMedianPrice = t_info.get('targetMedianPrice') if t_info.get('targetMedianPrice') is not None else 0
                        except TypeError:
                            TargetMedianPrice = None

                        try:
                            NumberOfAnalystOpinions = t_info.get('numberOfAnalystOpinions') if t_info.get('numberOfAnalystOpinions') is not None else 0
                        except TypeError:
                            NumberOfAnalystOpinions = None

                        try:
                            Trailing_EPS_EarningsPerShare = t_info.get('trailingEps') if t_info.get('trailingEps') is not None else 0
                        except TypeError:
                            Trailing_EPS_EarningsPerShare = None

                        latest_close = from_yfinance[-1]

                        try:
                            P_E = round((latest_close / Trailing_EPS_EarningsPerShare), 2)
                        except ZeroDivisionError:
                            P_E = 0

                        final_text = [[str(date.today()), ticker, company_name, sector, country, m_cap, enterp_val, P_S_12_m, P_E, P_B, marg, enterprToRev, enterprToEbitda, yr_div, five_yr_div_yield, div_date, FreeCashFlow, DebtToEquity, ROA_ReturnOnAssets, EBITDA, TargetMedianPrice, NumberOfAnalystOpinions, Trailing_EPS_EarningsPerShare] + from_yfinance]
                        # заполнение
                        resource = {"majorDimension": "ROWS", "values": final_text}
                        range = "Update!A:AE";
                        serv_e.spreadsheets().values().append(spreadsheetId=self.ranking_page, range=range, body=resource, valueInputOption="USER_ENTERED").execute()

                        print(f'Done for: {ticker}, {self.tickers_list.index(ticker) + 1} out of {len(self.tickers_list)}, chunk: {self.chunks_list.index(chunk) + 1}')

                    except:
                        print(f'Exception at yf getting data, might be TypeError etc.')
                        pass

            self.backup_to_retro()

    def backup_to_retro(self):
        # Backup for Retro sheet

        # reading the ranking page to clear it up
        new_results_rank = self.service.spreadsheets().values().batchGet(spreadsheetId=self.ranking_page, ranges='Update!A:AE', valueRenderOption='FORMATTED_VALUE', dateTimeRenderOption='FORMATTED_STRING').execute()
        # new_results_rank = service.spreadsheets().values().batchGet(spreadsheetId=ranking_page, ranges='Update!A:AE', valueRenderOption='FORMATTED_VALUE', dateTimeRenderOption='FORMATTED_STRING').execute()
        rank_sheet_values = new_results_rank['valueRanges'][0]['values']
        data_range = rank_sheet_values[1:]

        # connecting once again
        crede_s_2 = ServiceAccountCredentials.from_json_keyfile_name(self.CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        # crede_s_2 = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        http_Auth_2 = crede_s_2.authorize(httplib2.Http())  # Авторизуемся в системе
        serv_e_2 = apiclient.discovery.build('sheets', 'v4', http=http_Auth_2)

        new_resource = {"majorDimension": "ROWS", "values": data_range}
        range = "Retro!A:AE";
        serv_e_2.spreadsheets().values().append(spreadsheetId=self.ranking_page, range=range, body=new_resource, valueInputOption="USER_ENTERED").execute()
        # serv_e_2.spreadsheets().values().append(spreadsheetId=ranking_page, range=range, body=new_resource, valueInputOption="USER_ENTERED").execute()
        print(f'Done at all!')
