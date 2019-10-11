from pathlib import Path
import pandas as pd
import re
from iso3166 import countries
from datetime import datetime
import sqlite3

def is_ec2():
    import socket
    name = socket.gethostname()
    if re.match('ip(?:-\d+){4}\.[\w-]+\.compute', name):
        return True
    else:
        return False

def get_col_type(tbl, col):
    if ec2:
        db.execute('SELECT column_type FROM information_schema.columns WHERE table_name=%s AND column_name=%s', (tbl, col))
        result = db.fetchone()
    else:
        result = [item['type'] for item in db.execute('PRAGMA table_info({})'.format(tbl)).fetchall() if item['name']==col]
    if len(result):
        return result[0]
    else:
        return ''

def fillna_by_coltype(df):
    df[[cur_cols[col] for table, col, type in col_types if table=='person' and re.search('char', type.lower())]].fillna('', inplace=True)
    df[[cur_cols[col] for table, col, type in col_types if table=='person' and re.match('int', type.lower())]].fillna(0, inplace=True)
    return df
    
def read_auth_table(key):
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
        country_list = re.sub('/', ',', country_list) #break Serbia/Montenegro apart
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

if ec2:
    auth = read_auth_table('rds1')
    import mysql.connector
    conn = mysql.connector.Connect(host='main.caqmcqa1ulqd.us-east-2.rds.amazonaws.com', user=auth['username'], password=auth['password'], database='wab')
else:
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.text_factory = str

db = conn.cursor()

tables = ['film', 'film_genre', 'film_country', 'person', 'film_person', 'person_country']
if ec2 and 1==1:
    for tbl in tables:
        db.execute('DROP TABLE {}'.format(tbl))

db.execute('CREATE TABLE film (' + 
           'id INTEGER PRIMARY KEY {}, '.format('AUTO_INCREMENT' if ec2 else 'AUTOINCREMENT') + 
           'wab_tracking_id VARCHAR(15), ' + 
           'application_date DATE, ' +
           'category VARCHAR(50), ' +
           'judging_status VARCHAR(15), ' + 
           'title_original VARCHAR(255), ' + 
           'title_english VARCHAR(255), ' + 
           'logline MEDIUMTEXT, ' + 
           'synopsis_3_line MEDIUMTEXT,' +  
           'synopsis_125_word MEDIUMTEXT, ' + 
           'synopsis_250_word MEDIUMTEXT, ' + 
           'project_submission_type VARCHAR(50),' +  
           'completion_date INTEGER, ' + 
           'runtime INTEGER, ' + 
           'budget_usd INTEGER, ' + 
           'premiere VARCHAR(15))')

db.execute('CREATE TABLE film_genre (' + 
           'film_id INTEGER NOT NULL, ' +
           'genre VARCHAR(50) NOT NULL)')

db.execute('CREATE TABLE film_country (' + 
           'film_id INTEGER NOT NULL, ' +
           'country_alpha3 CHAR(3) NOT NULL, ' +
           'country_production BOOL, ' +
           'country_filming BOOL)')

db.execute('CREATE TABLE person (' + 
           'id INTEGER PRIMARY KEY {},'.format('AUTO_INCREMENT' if ec2 else 'AUTOINCREMENT') + 
           'salutation VARCHAR(5),' + 
           'f_name VARCHAR(50),' + 
           'l_name VARCHAR(50),' + 
           'title VARCHAR(100),' + 
           'address VARCHAR(255),' + 
           'company VARCHAR(255),' + 
           'email VARCHAR(255),' + 
           'website_url VARCHAR(255),' + 
           'category VARCHAR(50),' + 
           'gender VARCHAR(5),' + 
           'citizenship VARCHAR(50))')

db.execute('CREATE TABLE film_person (' + 
           'film_id INTEGER NOT NULL, ' +
           'person_id INTEGER NOT NULL, ' +
           'person_role VARCHAR(50))')

db.execute('CREATE TABLE person_country (' + 
           'person_id INTEGER NOT NULL, ' +
           'country_alpha3 CHAR(3) NOT NULL)')

iso3166_list = pd.DataFrame([dict(item._asdict().items()) for item in countries])
iso3166_list = iso3166_list.append(country_errors(), sort=False)

cols = pd.read_csv(interim_dir / 'map_columns.csv')

film_cols = cols.loc[cols['film']==1][['index', 'oldcol', 'newcol']].drop_duplicates()
film_cols['type'] = film_cols.apply(lambda x: get_col_type('film', x['newcol']), axis=1)

person_cols = cols.loc[cols['person']==1][['index', 'oldcol', 'newcol', 'person_category']].drop_duplicates()
#person_cols['type'] = person_cols.apply(lambda x: get_col_type('person', x['newcol']), axis=1)

data = pd.DataFrame()
for filename in raw_dir.iterdir():
    if re.match('\d{4}', filename.stem) and filename.suffix=='.csv':
        df = pd.read_csv(filename, low_memory=False)
        data = data.append(df, ignore_index=True, sort=False)
#data = data.apply(lambda x: x.str.strip(), axis=1)
data.dropna(how='all', inplace=True)
data.rename(columns=dict(zip(cols.oldcol, cols.newcol)), inplace=True)
data.to_csv(out_dir / 'all_wab_data.csv')
data[list(cols.loc[(cols.person==1) | (cols.film==1)]['newcol'])].to_csv(out_dir / 'most_wab_data.csv')

data['application_date'] = data['application_date'].map(lambda x: datetime.strptime(x, '%m/%d/%Y').strftime('%Y-%m-%d'))
data['budget_usd'] = data['budget_usd'].str.replace('[^\d\.]', '')

data['genre_and_niche_list'] = data['genre_and_niche_list'].fillna('').map(lambda x: [i.strip() for i in x.split(',')])
#make_genre_table()
data['country_of_production_list'] = data['country_of_production_list'].fillna('').map(get_country_list)
data['country_of_filming_list'] = data['country_of_filming_list'].fillna('').map(get_country_list)

#if ec2:
#    db.execute('SELECT column_name FROM information_schema.columns WHERE table_name="film"')
#    film_cols = [name[0] for name in [row for row in db.fetchall()] if name[0]!='id'] 
#else:
#    film_cols = [row['name'] for row in db.execute('PRAGMA table_info(film)') if row['name']!='id']

param_mark = '%s' if ec2 else '?'
param_list = lambda num, str=param_mark: ','.join([str]*num)
for idx, row in data.iterrows():
    row[[col for col in film_cols.loc[film_cols.type.str.contains('char', case=False) & ~film_cols.type.isna()]['newcol']]].fillna('', inplace=True)
    row[[col for col in film_cols.loc[film_cols.type.str.match('int', case=False) & ~film_cols.type.isna()]['newcol']]].fillna(0, inplace=True)
    cur_cols = [col for col in film_cols.loc[film_cols.type.map(len)>0]['newcol']]

    #row[[col for table, col, type in col_types if table=='film' and re.match('int', type.lower())]].fillna(0, inplace=True)
    db.execute('INSERT INTO film ({}) VALUES ({})'.format(', '.join(cur_cols), param_list(len(cur_cols))), tuple(row[cur_cols].values))
    conn.commit()
    db.execute('SELECT max(id) FROM film')
    film_id = db.fetchone()[0]
    for genre in row['genre_and_niche_list']:
        db.execute('INSERT INTO film_genre VALUES ({})'.format(param_list(2)), (film_id, genre))
    for country in row['country_of_production_list']:
        db.execute('INSERT INTO film_country VALUES ({})'.format(param_list(4)), (film_id, country, 1, 0))
    for country in row['country_of_filming_list']:
        db.execute('INSERT INTO film_country VALUES ({})'.format(param_list(4)), (film_id, country, 0, 1))
    conn.commit()

    for category in person_cols['person_category'].drop_duplicates():
        df_cols = person_cols.loc[person_cols.person_category.eq(category)]['newcol'].drop_duplicates()
        tbl_cols = map(lambda x: re.sub(category + '_', '', x), df_cols)
        df = row[map(lambda x: category + '_' + x, [col for col in df_cols if len(get_col_type('person', col))>0])]
        if df.dropna(how='all').map(lambda x: len(str(x))).sum() > 0:
            db.execute('INSERT INTO person ({}) VALUES ({})'.format(', '.join(cur_cols), param_list(len(cur_cols))), tuple(df.values))
            conn.commit()
            db.execute('SELECT max(id) FROM person')
            person_id = db.fetchone()[0]
            db.execute('INSERT INTO film_person VALUES ({})'.format(param_list(3)), (film_id, person_id, re.sub('\d+', '', category)))
            if category + '_country' in ctry_col:
                ctry_data = re.sub('[Nn]one', '', row[ctry_col[0]])
                if ctry_data:
                    for ctry in get_country_list(ctry_data):
                        db.execute('INSERT INTO person_country VALUES ({})'.format(param_list(2)), (person_id, ctry))
            conn.commit()

db.execute('SELECT * FROM film LIMIT 10')
for row in db.fetchall():
    print(dict(row))
db.execute('SELECT * FROM film_genre LIMIT 10')
for row in db.fetchall():
    print(dict(row))
db.execute('SELECT * FROM film_country LIMIT 10')
for row in db.fetchall():
    print(dict(row))
db.execute('SELECT * FROM film_person LIMIT 10')
for row in db.fetchall():
    print(dict(row))
db.execute('SELECT * FROM person_country LIMIT 10')
for row in db.fetchall():
    print(dict(row))
print(list(missing_countries.keys()))


