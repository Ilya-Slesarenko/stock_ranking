import xml.etree.ElementTree as ET
import re, time, json, urllib.request, ast, httplib2, apiclient.discovery
from pandas.io.json import json_normalize
from datetime import date, timedelta
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials



# In order to parse xml with no errors, Create a new class which overrides the user-agent with Mozilla.
class AppURLopener(urllib.request.FancyURLopener):
    version = "Mozilla/5.0"


class InsidersDeals():
    def __init__(self):

        # Получение списка акций  из готового листа Google Sheet для проверки (не брать то, что все равно не сможем оценить и купить!
        self.CREDENTIALS_FILE = 'stock-spreadsheets-9974a749b7e4.json'
        tickers_page = '1s6uIbhIX4IYCmFYhfWgEklFqtLX95ky7GmJNRvVexeM'
        credentials = ServiceAccountCredentials.from_json_keyfile_name(self.CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        httpAuth = credentials.authorize(httplib2.Http())  # Авторизуемся в системе
        self.service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)  # Выбираем работу с таблицами и 4 версию API

        # reading data
        results = self.service.spreadsheets().values().batchGet(spreadsheetId=tickers_page, ranges='A:R', valueRenderOption='FORMATTED_VALUE', dateTimeRenderOption='FORMATTED_STRING').execute()
        sheet_values = results['valueRanges'][0]['values']
        values = sheet_values[1:]  # текущий рабочий список (весь!)

        self.yf_working_tickers_list = []  # текущий рабочий список для работы с yfinance без излишек (если будет нужен, в скрипте не используется!)
        for i in values:
            if i[-2] == 'yfinance':
                self.yf_working_tickers_list.append(i[1])


        start = date.today()
        end = date.today() - timedelta(200)
        TOKEN = '8542ae672b4f1f3d12bf3bf51084a899955e9204cd05ea3888ef2be21b53e5ff'
        API = "https://api.sec-api.io?token=" + TOKEN
        filter = f"formType:\"4\" AND formType:(NOT \"N-4\") AND formType:(NOT \"4/A\") AND filedAt:[{str(end)} TO {str(start)}]"
        sort = [{"filedAt": {"order": "desc"}}]

        payload = {
            "query": {"query_string": {"query": filter}},
            "from": 0,
            "size": 20000,
            "sort": sort
        }

        # Format the payload to JSON bytes
        jsondata = json.dumps(payload)
        jsondataasbytes = jsondata.encode('utf-8')  # needs to be bytes

        # Instantiate the request
        req = urllib.request.Request(API)

        # Set the correct HTTP header: Content-Type = application/json
        req.add_header('Content-Type', 'application/json; charset=utf-8')
        # Set the correct length of your request
        req.add_header('Content-Length', len(jsondataasbytes))

        # Send the request to the API
        response = urllib.request.urlopen(req, jsondataasbytes)

        # Read the response
        res_body = response.read()
        # Transform the response into JSON
        self.filingsJson = json.loads(res_body.decode("utf-8"))


    # this is for testing ONLY!!!
    def compress_filings(self, filings):
        store = {}
        compressed_filings = []
        for filing in filings:
            filedAt = filing['filedAt']
            if filedAt in store: # and store[filedAt] < 5:  #  check if this is bigger - what happens!
                compressed_filings.append(filing)
                store[filedAt] += 1
            elif filedAt not in store:
                compressed_filings.append(filing)
                store[filedAt] = 1
        return compressed_filings


    # Download the XML version of the filing. If it fails wait for 5, 10, 15, ... seconds and try again.
    def download_xml(self, url):
        try:
            opener = AppURLopener()
            response = opener.open(url)
        except:
            print('Something went wrong. consider to use cycling trying')
            if tries < 5:
                time.sleep(5 * tries)
                download_xml(url, tries + 1)
        else:
            # decode the response into a string
            data = response.read().decode('utf-8')
            # set up the regular expression extractoer in order to get the relevant part of the filing
            matcher = re.compile('<\?xml.*ownershipDocument>', flags=re.MULTILINE|re.DOTALL)
            matches = matcher.search(data)
            # the first matching group is the extracted XML of interest
            try:
                xml = matches.group(0)
                # instantiate the XML object
                root = ET.fromstring(xml)
                return root
            except AttributeError:
                print(f'xml can\'t be given, check matches: {matches}')
                root = None
                return root


    # Calculate the total transaction amount in $ of a giving form 4 in XML
    def calculate_transaction_amount(self, xml):
        total = 0
        if xml is None:
            return total
        nonDerivativeTransactions = xml.findall("./nonDerivativeTable/nonDerivativeTransaction")
        for t in nonDerivativeTransactions:
            # D for disposed or A for acquired
            action = t.find('./transactionAmounts/transactionAcquiredDisposedCode/value').text
            # number of shares disposed/acquired
            shares = t.find('./transactionAmounts/transactionShares/value').text
            # price
            priceRaw = t.find('./transactionAmounts/transactionPricePerShare/value')
            price = 0 if priceRaw is None else priceRaw.text
            # set prefix to -1 if derivatives were disposed. set prefix to 1 if derivates were acquired.
            prefix = -1 if action == 'D' else 1
            # calculate transaction amount in $
            amount = prefix * float(shares) * float(price)
            total += amount
        return round(total, 2)


    # Take some other data form 4 in XML
    def find_owner(self, xml):
        report_owner = 'N/A'
        if xml is None:
            return report_owner
        owner_field = xml.findall("./reportingOwner/reportingOwnerId")#/rptOwnerName")
        for o in owner_field:
            report_owner = o.find('./rptOwnerName').text

        return report_owner


    # Download the XML for each filing
    # Calculate the total transaction amount per filing
    # Save the calculate transaction value to the filing dict with key 'nonDerivativeTransactions'
    def add_non_derivative_transaction_amounts(self):
        filings = self.compress_filings(self.filingsJson['filings'])
        for filing in filings:
            url = filing['linkToTxt']
            xml = self.download_xml(url)
            nonDerivativeTransactions = self.calculate_transaction_amount(xml)
            filing['nonDerivativeTransactions'] = nonDerivativeTransactions
            filing['rep_owner'] = self.find_owner(xml)
            print(f'Done for: {filings.index(filing)} out of {len(filings)}')
        return filings


    def ConvertBeforeSaving(self):
        # Running the function prints the URL of each filing fetched
        returned_filings = self.add_non_derivative_transaction_amounts()
        filings_final = json_normalize(returned_filings) #making dataframe, clear and understood
        # headers = filings_final.columns.values.tolist()  # ['id', 'accessionNo', 'cik', 'ticker', 'companyName', 'formType', 'description', 'filedAt', 'linkToTxt', 'linkToHtml', 'linkToXbrl', 'linkToFilingDetails', 'entities', 'documentFormatFiles', 'dataFiles', 'seriesAndClassesContracts', 'Information', 'periodOfReport', 'effectivenessDate', 'nonDerivativeTransactions', 'owner']
        values = filings_final.values.tolist()

        checklist = [None, 0, '']
        final_list = []
        for i in values:
            declare_id = i[0]
            central_index_key = i[2]
            declare_date = i[8]
            period_of_report = i[-4]
            ticker = i[3]
            company_name = i[4]
            amount = i[-2]
            owner = i[-1]
            link_to_txt = i[9]
            if ticker not in checklist and amount not in checklist and ticker in self.yf_working_tickers_list:
                final_list.append([declare_date, period_of_report, declare_id, central_index_key, ticker, company_name, amount, link_to_txt, owner])
            else:
                pass

        return final_list


    def PerformAll(self):
        list_headers = ['declare_date', 'period_of_report', 'declare_id', 'central_index_key', 'ticker', 'company_name', 'amount', 'linkToTxt', 'report_owner']
        final_list = self.ConvertBeforeSaving()
        val_df_2 = pd.DataFrame(final_list, columns=list_headers)
        val_df_3 = val_df_2.set_index('declare_date')

        temp_output_dir = 'C:\\Users\\Ilia\Documents\\Python_projects\\Stock_analysis\\Insider_trading\\output.xlsx'
        writer = pd.ExcelWriter(temp_output_dir, engine='xlsxwriter')
        val_df_3.to_excel(writer, sheet_name='result', index=True)
        writer.save()

        print(f'We\'re all set!')


if __name__ == '__main__':
    InsidersDeals().PerformAll()
