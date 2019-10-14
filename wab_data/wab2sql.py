from pathlib import Path
import pandas as pd
import re
from iso3166 import countries
from datetime import datetime
import sqlalchemy
from sqlalchemy import create_engine, MetaData, Table, Column
from sqlalchemy import Integer, String, Date, Text, Boolean
from sqlalchemy import select, text

def is_ec2():
    import socket
    name = socket.gethostname()
    if re.match('ip(?:-\d+){4}\.[\w-]+\.compute', name):
        return True
    else:
        return False

def get_col_type(tbl, col):
    sql = text('SELECT column_type FROM information_schema.columns WHERE table_name=:tbl AND column_name=:col')
    result = db.execute(sql, tbl=tbl, col=col).fetchone()
    if result:
        return result[0]
    else:
        return ''

def read_auth_table(key):
    import sqlite3
    conn = sqlite3.connect('auth_info.db')
    conn.row_factory = sqlite3.Row
    db = conn.cursor()
    db.execute('SELECT username, password FROM main WHERE key=?', [key])
    return dict(db.fetchone())
    
def make_genre_table():
    genres = {}
    db.execute('CREATE TABLE genre (' + 
               'id INTEGER PRIMARY KEY AUTOINCREMENT, ' + 
               'name VARCHAR(50))')
    for item in data['genre_and_niche_list']:
        for genre in item: 
            genres[genre] = True    
    db.executemany('INSERT INTO genre (name) VALUES (?)', [(i,) for i in genres.keys()])

def get_country_list(country_list):
    result = []
    if len(country_list):
        country_list = re.sub('/', ',', str(country_list)) #break Serbia/Montenegro apart
        name_stripper = lambda x: re.sub('\W', '', x).lower()
        for country in country_list.split(','):
            result = iso3166_list.loc[(iso3166_list['alpha3']==country) | 
                                  (iso3166_list['name']==country) | 
                                  (iso3166_list['name'].map(name_stripper)==name_stripper(country)) |  
                                  (iso3166_list['name'].str.contains(re.escape(country)))]['alpha3'].values.tolist()
            if not result:
                missing_countries[country] = True
    return result

def country_errors():
    result = pd.DataFrame()
    errors = {'KOR': 'South Korea', 
              'CZE': 'Czech Republic', 
              'CIV': 'Cote d Ivoire', 
              'PRK': 'North Korea', 
              'PSE': 'Palestinian Territories'}
    result = iso3166_list.loc[iso3166_list['alpha3'].isin(errors.keys())].copy()
    result['name'] = result['alpha3'].apply(lambda x: errors[x])
    return result

data_dir = Path('data')
raw_dir = data_dir / 'raw'
interim_dir = data_dir / 'interim'
out_dir = data_dir / 'out'
missing_countries = {}
ec2 = is_ec2()

auth = read_auth_table('rds1')
host = 'main.caqmcqa1ulqd.us-east-2.rds.amazonaws.com' if ec2 else 'localhost'
connect_string = 'mysql+mysqldb://{}:{}@{}/{}?charset=utf8'.format(auth['username'], auth['password'], host, 'wab')
db = create_engine(connect_string, encoding='utf-8')
metadata = MetaData()

if 1==1:
    tables = ['film', 'film_genre', 'film_country', 'person', 'film_person', 'person_country']
    for tbl in tables:
        db.execute('DROP TABLE IF EXISTS {}'.format(tbl))

tbl_film = Table('film', metadata, 
           Column('id', Integer, primary_key=True), 
           Column('wab_tracking_id', String(15)), 
           Column('application_date', Date), 
           Column('category', String(50)), 
           Column('judging_status', String(15)), 
           Column('title_original', String(255)), 
           Column('title_english', String(255)), 
           Column('logline', Text), 
           Column('synopsis_3_line', Text), 
           Column('synopsis_125_word', Text), 
           Column('synopsis_250_word', Text), 
           Column('project_submission_type', String(50)), 
           Column('completion_date', Integer), 
           Column('runtime', Integer), 
           Column('budget_usd', Integer), 
           Column('premiere', String(15))
)

tbl_film_genre = Table('film_genre', metadata, 
           Column('film_id', Integer, nullable=False), 
           Column('genre', String(50), nullable=False)
)

tbl_film_country = Table('film_country', metadata, 
           Column('film_id', Integer, nullable=False), 
           Column('country_alpha3', String(3), nullable=False), 
           Column('country_production', Boolean), 
           Column('country_filming', Boolean)
)

tbl_person = Table('person', metadata, 
           Column('id', Integer, primary_key=True), 
           Column('salutation', String(5)), 
           Column('f_name', String(50)), 
           Column('l_name', String(50)), 
           Column('title', String(100)), 
           Column('address', String(255)), 
           Column('company', String(255)), 
           Column('country', String(255)), 
           Column('email', String(255)), 
           Column('website_url', String(255)), 
           Column('role', String(50)), 
           Column('gender', String(5)), 
           Column('citizenship', String(50))
)

tbl_film_person = Table('film_person', metadata, 
           Column('film_id', Integer, nullable=False), 
           Column('person_id', Integer, nullable=False), 
           Column('person_role', String(50))
)

tbl_person_country = Table('person_country', metadata, 
           Column('person_id', Integer, nullable=False), 
           Column('country_alpha3', String(3), nullable=False)
)

metadata.create_all(db)

iso3166_list = pd.DataFrame([dict(item._asdict().items()) for item in countries])
iso3166_list = iso3166_list.append(country_errors(), sort=False)

cols = pd.read_csv(interim_dir / 'map_columns.csv').fillna('')
cols['col_df'] = cols.apply(lambda x: x['role'] + '_' + x['col_tbl'] if x['role']!='' else x['col_tbl'], axis=1)
cols['type'] = cols.apply(lambda x: get_col_type(x['table'], x['col_tbl']) if x['table']!='' else '', axis=1)
cols['na_value'] = cols.apply(lambda x: '' if re.search('(char|text)', x['type']) else 0 if re.search('int', x['type']) else None, axis=1)

data = pd.DataFrame()
for filename in raw_dir.iterdir():
    if re.match('\d{4}', filename.stem) and filename.suffix=='.csv':
        df = pd.read_csv(filename, low_memory=False, encoding='utf8')
        data = data.append(df, ignore_index=True, sort=False)

data.dropna(how='all', inplace=True)
data.rename(columns=dict(zip(cols.oldcol, cols.col_df)), inplace=True)

data.to_csv(out_dir / 'all_wab_data.csv')
data[list(cols.loc[cols.table!='']['col_df'])].to_csv(out_dir / 'most_wab_data.csv')

data['application_date'] = data['application_date'].map(lambda x: datetime.strptime(x, '%m/%d/%Y').strftime('%Y-%m-%d'))
data['budget_usd'] = data['budget_usd'].str.replace('[^\d\.]', '')

data['genre_and_niche_list'] = data['genre_and_niche_list'].fillna('').map(lambda x: [i.strip() for i in x.split(',')])
#make_genre_table()
data['country_of_production_list'] = data['country_of_production_list'].fillna('').map(get_country_list)
data['country_of_filming_list'] = data['country_of_filming_list'].fillna('').map(get_country_list)

for col in data.columns:
    cur_val = cols.loc[cols.col_df==col]['na_value'].values[0]
    if cur_val is not None:
        data[col] = data[col].fillna(cur_val)

for idx, row in data.iterrows():
    cur_cols = cols.loc[(cols.table=='film') & (cols.type!='')]
    df = row[cur_cols['col_df']].rename(dict(zip(cur_cols['col_df'], cur_cols['col_tbl'])))
    result = db.execute(tbl_film.insert().values(df.to_dict()))
    film_id = result.inserted_primary_key
    for genre in row['genre_and_niche_list']:
        result = db.execute(tbl_film_genre.insert().values({'film_id' : film_id, 'genre' : genre}))
    for country in row['country_of_production_list']:
        result = db.execute(tbl_film_country.insert().values({'film_id' : film_id, 'country_alpha3' : country, 'country_production' : 1, 'country_filming' : 0}))
    for country in row['country_of_filming_list']:
        result = db.execute(tbl_film_country.insert().values({'film_id' : film_id, 'country_alpha3' : country, 'country_production' : 0, 'country_filming' : 1}))

    for role in cols.loc[cols.role!='']['role'].drop_duplicates():
        cur_cols = cols.loc[(cols.table=='person') & (cols.role==role) & (cols.type!='')]
        df = row[cur_cols['col_df'].to_list()]
        df = df.rename(index=dict(zip(cur_cols.col_df, cur_cols.col_tbl)))
        if df.dropna(how='all').map(lambda x: len(str(x))).sum() > 0:
            result = db.execute(tbl_person.insert().values(df.to_dict()))
            person_id = result.inserted_primary_key
            result = db.execute(tbl_film_person.insert().values({'film_id' : film_id, 'person_id' : person_id, 'person_role' : re.sub('\d+', '', role)}))
            for ctry_col in [col for col in row.index if col==role + '_country']:
                ctry_data = re.sub('[Nn]one', '', row[ctry_col])
                if ctry_data:
                    for ctry in get_country_list(ctry_data):
                        result = db.execute(tbl_person_country.insert().values({'person_id' : person_id, 'country_alpha3' : ctry}))

print(list(missing_countries.keys()))


