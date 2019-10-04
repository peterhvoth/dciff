from pathlib import Path
import pandas as pd
import re
from iso3166 import countries

def is_ec2():
    import socket
    name = socket.gethostname()
    if re.match('ip(?:-\d+){4}\.[\w-]+\.compute', name):
        return True
    else:
        return False

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

if is_ec2():
    import mysql.connector
    conn = mysql.connector.Connect(host='main.caqmcqa1ulqd.us-east-2.rds.amazonaws.com', user='admin', password='Dciff2020', database='common')
else:
    import sqlite3
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.text_factory = str

db = conn.cursor()

iso3166_list = pd.DataFrame([dict(item._asdict().items()) for item in countries])
iso3166_list = iso3166_list.append(country_errors(), sort=False)
name_stripper = lambda x: re.sub('\W', '', x).lower()

cols = pd.read_csv(interim_dir / 'map_columns.csv')
cols['newcol1'] = cols.apply(lambda x: x['newcol'] if pd.isna(x['category']) else x['category'] + '_' + x['newcol'], axis=1)

data = pd.DataFrame()
for filename in raw_dir.iterdir():
    if re.match('\d{4}', filename.stem) and filename.suffix=='.csv':
        df = pd.read_csv(filename, low_memory=False)
        data = data.append(df, ignore_index=True, sort=False)
#data = data.apply(lambda x: x.str.strip(), axis=1)
data.dropna(how='all', inplace=True)
data.rename(columns=dict(zip(cols.oldcol, cols.newcol1)), inplace=True)
data.to_csv(out_dir / 'all_wab_data.csv')
data[list(cols.loc[(cols.person==1) | (cols.film==1)]['newcol1'])].to_csv(out_dir / 'most_wab_data.csv')

data['genre_and_niche_list'] = data['genre_and_niche_list'].fillna('').map(lambda x: [i.strip() for i in x.split(',')])
#make_genre_table()
data['country_of_production_list'] = data['country_of_production_list'].fillna('').map(get_country_list)
data['country_of_filming_list'] = data['country_of_filming_list'].fillna('').map(get_country_list)

db.execute('CREATE TABLE film (' + 
           'id INTEGER PRIMARY KEY AUTOINCREMENT, ' + 
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
           'completion_date INT, ' + 
           'runtime INT, ' + 
           'budget_usd INT, ' + 
           'premiere VARCHAR(15))')

db.execute('CREATE TABLE film_genre (' + 
           'film_id INT NOT NULL, ' +
           'genre VARCHAR(50) NOT NULL)')

db.execute('CREATE TABLE film_country (' + 
           'film_id INT NOT NULL, ' +
           'country_alpha3 CHAR(3) NOT NULL, ' +
           'country_production BOOL, ' +
           'country_filming BOOL)')

db.execute('CREATE TABLE person (' + 
           'id INTEGER PRIMARY KEY AUTOINCREMENT,' + 
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
           'film_id INT NOT NULL, ' +
           'person_id INT NOT NULL, ' +
           'person_role VARCHAR(50))')

db.execute('CREATE TABLE person_country (' + 
           'person_id INT NOT NULL, ' +
           'country_alpha3 CHAR(3) NOT NULL)')

film_cols = [r['name'] for r in db.execute('PRAGMA table_info(film)') if r['cid']>0]
person_cols = {}
for category in cols.loc[cols.person==1 & cols.category.notna() & cols.category.ne('school')]['category'].drop_duplicates():
    person_cols[category] = {row['newcol1'] : row['newcol'] for idx, row in cols.loc[(cols.category==category) & (cols.person==1)].iterrows()}

for idx, row in data.iterrows():
    row.fillna('', inplace=True)
    db.execute('INSERT INTO film ({}) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'.format(', '.join(film_cols)), row[film_cols].values)
    film_id = db.execute('SELECT max(id) FROM film').fetchone()[0]
    for genre in row['genre_and_niche_list']:
        db.execute('INSERT INTO film_genre VALUES (?,?)', (film_id, genre))
    for country in row['country_of_production_list']:
        db.execute('INSERT INTO film_country VALUES (?,?,?,?)', (film_id, country, 1, 0))
    for country in row['country_of_filming_list']:
        db.execute('INSERT INTO film_country VALUES (?,?,?,?)', (film_id, country, 0, 1))

    for category in person_cols.keys():
        cur_cols = {key : val for key, val in person_cols[category].items() if val!='country'}
        df = row[cur_cols.keys()]
        if len(df.dropna(how='all')) > 0:
            db.execute('INSERT INTO person ({}) VALUES ({})'.format(', '.join(cur_cols.values()), ','.join('?'*len(cur_cols))), df.values)
            person_id = db.execute('SELECT max(id) FROM person').fetchone()[0]
            db.execute('INSERT INTO film_person VALUES (?,?,?)', (film_id, person_id, re.sub('\d+', '', category)))
            ctry_col = [key for key, val in person_cols[category].items() if val=='country']
            if len(ctry_col):
                ctry_data = re.sub('[Nn]one', '', row[ctry_col[0]])
                if ctry_data:
                    for ctry in get_country_list(ctry_data):
                        db.execute('INSERT INTO person_country VALUES (?,?)', (person_id, ctry))

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


