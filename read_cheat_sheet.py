import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import re 

def get_gsheet_data(sheet_name, sheet_index=0):
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    
    credentials = ServiceAccountCredentials.from_json_keyfile_name('dciff-266121-51580f9f5256.json', scope)
    gc = gspread.authorize(credentials)
    wks = gc.open(sheet_name).get_worksheet(sheet_index)
    data = wks.get_all_values()
    headers = data.pop(0)    
    return pd.DataFrame(data, columns=headers)

def get_countries(df):
    countries = df.columns[list(df.columns).index('Australia'):]
    return [country for country in countries if country!='United States']

def report_by_column(cols=[], cnt_only = False, cnt_floor = 0, event_info=False, screener=False):
    cols = countries if not len(cols) else cols
    for col in cols:
        cnt = df[col].apply(lambda x: 0 if not len(x) else 1).sum()
        if cnt>cnt_floor:
            if cnt_only:
                print(col, cnt)
            else:
                with open('event_info/' + col + '.txt', 'w') as f:
                    for idx, row in df.loc[df[col]=='1'].iterrows():
                            f.write(print_screener(row, event_info=event_info, screener=screener))

def report_title_list(titles):
    for idx, row in df.loc[df['title'].isin(titles)].iterrows():
        print_screener(row)

def print_screener(row, event_info=False, screener=False):
    result = '{0}\n{1}\n{2}'.format(row['Title'], row['Category'], row['Logline'])
    result = result.strip()
    if event_info and row['event_info']!='':
        result += '\n{}'.format(row['event_info'])
    if screener:
        if row['Screener']!='':
            result += '\n{}'.format(row['Screener'])
            if row['Screener Password']!='':
                result += '\npw: {}'.format(row['Screener Password'])
        else:
            result += '\nNo Screener Available. Please contact us for access.'
    result += '\n\n'
    return result

make_title_id = lambda x: x.replace(to_replace={'\s' : '_', '\W' : ''}, regex=True).str.lower()
make_datetime = lambda x: pd.to_datetime(x['date'] + ' 2020 ' + x['start'], errors='ignore').strftime('%a %b %-d, %-I:%M %p')
make_date = lambda x: pd.to_datetime(x['date'] + ' 2020', errors='ignore').strftime('%a %b %-d')

film = get_gsheet_data('2020 DCIFF Films')
countries = get_countries(film)
film['title_id'] = make_title_id(film['Title'])
venue = get_gsheet_data('venue')
program = get_gsheet_data('program')
schedule = get_gsheet_data('schedule')
schedule['title_id'] = make_title_id(schedule['title'])

df = pd.merge(film, schedule, on='title_id', how='left', suffixes=('', '_duplicate'))
df = pd.merge(df, program, on='program_id', how='left', suffixes=('', '_duplicate'))
df = pd.merge(df, venue, on='venue_id', how='left', suffixes=('', '_duplicate'))
df.fillna('', inplace=True)

df.loc[df['program_title']!='', 'event_info'] = df.apply(make_datetime, axis=1) + '\n' + df['venue_name'] + '\n' + df['address'] + '\nMetro: ' + df['metro']
df.loc[(df['program_title']!='') & (df['program_title']!=df['title']), 'event_info'] = df['program_title'] + '\n' + df['url'] + '\n' + df['event_info']
df['date'] = df.apply(lambda x: pd.to_datetime(x['date'] + ' 2020', errors='ignore'), axis=1)

#df.to_csv('tmp.csv')
#report_by_column(event_info=True, screener=False, cnt_floor=1)
sets = {#'gary' : ['The Ringmaster', 'The Dark End of the Street', 'Life in Synchro'], 
#        'eli' : ['love type d', 'the dark end of the street', "Abe's Story", 'life in synchro', 'soumaya', 'Maradona’s Legs', 'Lost and Found', 'The Dance', 'Up from the Streets'],
        'european union' : ["Free Fun",  "Daughter",  "Infraction",  "Soumaya",  "The Cage",  "Titan (Creative Spirit)",  "Watching The Pain of Others",  "Maradona’s Legs",  "Heat Wave",  "Abe's Story",  "the Ball's Run",  "Sea Shepherd",  "Flora"]#, 
#        'nell' : ["Ek Cup Chaha (One Cup of Tea)", "Maradona’s Legs", "The Dance", "Watching The Pain of Others", "SEMA", "Soumaya"], 
#        'lgbt' : ['Free Fun', 'Going Steady', 'Good Genes', 'The Holocaust is Over, Bitch', 'Where My Girls', 'Life in Synchro']
        }

for name, films in sets.items():
    with open('event_info/' + name + '.txt', 'w') as f:
        for idx, row in df.loc[df['title_id'].isin(make_title_id(pd.Series(films)))].sort_values(axis=0, by=['Category', 'Title', 'date']).iterrows():
            f.write(print_screener(row, event_info=True))
#cats = ['Narrative Feature', 'Documentary Feature', 'Series Episode', 'Animation', 'Narrative Short', 'Documentary Short']
#with open('event_info/all.txt', 'w') as f:
#    for cat in cats:
#        f.write(cat + '\n')
#        for idx, row in df.loc[df['Category']==cat].sort_values(axis=0, by=['Title', 'date']).iterrows():
#            f.write('\t{0}\n\t\t{1}'.format(row['Title'], row['Logline']))
#            if row['event_info']!='':
#                f.write('\n\t\t{}'.format(re.sub('\n', '\n\t\t', row['event_info'])))
#            if row['Screener']!='':
#                f.write('\n\t\t{}'.format(row['Screener']))
#                if row['Screener Password']!='':
#                    f.write('\n\t\tpw: {}'.format(row['Screener Password']))
#            else:
#                f.write('\n\t\tNo Screener Available. Please contact us for access.')
#            f.write('\n')
#    for idx, row in df.sort_values(axis=0, by=['Category', 'Title', 'date']).iterrows():
#        f.write(print_screener(row, event_info=True, screener=True))
report_by_column(event_info=True)
#report_by_column(['Cyprus', 'Czech Republic', 'France', 'Germany', 'Greece', 'Ireland', 'Italy', 'Portugal', 'Spain'])
#report_by_column(['United Kingdom'], event_info=True, screener=False)
#print(df.loc[df['Screener']==''][['Title', 'Category']].to_string(index=False))

