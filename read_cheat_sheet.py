import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

def get_gsheet_data(sheet_name, sheet_index=0):
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    
    credentials = ServiceAccountCredentials.from_json_keyfile_name('dciff-266121-51580f9f5256.json', scope)
    gc = gspread.authorize(credentials)
    wks = gc.open(sheet_name).get_worksheet(sheet_index)
    data = wks.get_all_values()
    headers = data.pop(0)    
    return pd.DataFrame(data, columns=headers)

def get_countries():
    countries = df.columns[list(df.columns).index('Australia'):]
    return [country for country in countries if country!='United States']

df = get_gsheet_data('2020 DCIFF Films')
cols = []
cols = get_countries() if not len(cols) else cols
cnt_only = False
cnt_floor = 1

for col in cols:
    cnt = df[col].apply(lambda x: 0 if not len(x) else 1).sum()
    if cnt>cnt_floor:
        print(col, cnt)
        if not cnt_only:
            for idx, row in df.loc[df[col]=='1'].iterrows():
                print('{}\n{}\n{}'.format(row['Title'], row['Category'], row['Synopsis']))
                if row['Screener']!='':
                    print('{}'.format(row['Screener']))
                    if row['Screener Password']!='':
                        print('pw: {}'.format(row['Screener Password']))
                print('\n')
                    