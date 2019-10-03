from pathlib import Path
import pandas as pd
import re
import sqlite3
from iso3166 import countries

def get_genre():
    return True

def get_country_list(country_list):
    result = None
    if len(country_list):
        country_list = re.sub('/', ',', country_list) #break Serbia/Montenegro apart
        for country in country_list.split(','):
            country_stripped = re.sub('\W', '', country).lower()
            result = iso3166_list.loc[(iso3166_list['alpha3']==country) | 
                                  (iso3166_list['name']==country) | 
                                  (iso3166_list['stripped_name']==country_stripped) |  
                                  (iso3166_list['name'].str.contains(re.escape(country)))]['alpha3'].values.tolist()
            if not result:
                print(country)
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

iso3166_list = pd.DataFrame([dict(item._asdict().items()) for item in countries])
tmp = country_errors()
iso3166_list = iso3166_list.append(country_errors(), sort=False)
iso3166_list['stripped_name'] = iso3166_list['name'].str.lower().str.replace('\W', '')

cols = pd.read_csv(interim_dir / 'map_columns.csv')
cols['newcol1'] = cols.apply(lambda x: x['newcol'] if pd.isna(x['category']) else x['category'] + '_' + x['newcol'], axis=1)

if 1==0:
    conn = sqlite3.connect(':memory:')
    db = conn.cursor()
    db.execute('CREATE TABLE film (' + 
               'id INT NOT NULL AUTO_INCREMENT, ' + 
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
               'premiere VARCHAR(15),' +  
               'PRIMARY KEY(id))')
    
    db.execute('CREATE TABLE person (' + 
               'id INT NOT NULL AUTO_INCREMENT,' + 
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
               'citizenship VARCHAR(50),' + 
               'PRIMARY KEY(id))')
    
    db.execute('CREATE TABLE genre (' + 
               'id INT NOT NULL AUTO_INCREMENT, ' + 
               'name VARCHAR(50)'
               'PRIMARY KEY(id))')
    
    db.execute('CREATE TABLE country (' + 
               'official_name VARCHAR(75), ' +
               'common_name VARCHAR(75), ' +
               'alpha2 CHAR(2), ' + 
               'alpha3 CHAR(3), ' + 
               'numeric INT)')
    
    db.execute('CREATE TABLE film_person (' + 
               'film_id INT NOT NULL, '
               'person_id INT NOT NULL, '
               'person_role VARCHAR(50)')
    
    db.execute('CREATE TABLE film_genre (' + 
               'film_id INT NOT NULL, '
               'genre_id INT NOT NULL')
    
    db.execute('CREATE TABLE film_country (' + 
               'film_id INT NOT NULL, '
               'country_id INT NOT NULL, '
               'country_production BOOL, '
               'country_filming BOOL')

    db.execute('CREATE TABLE person_country (' + 
               'person_id INT NOT NULL, '
               'country_id INT NOT NULL')
    
data = pd.DataFrame()
for filename in raw_dir.iterdir():
    if re.match('\d{4}', filename.stem) and filename.suffix=='.csv':
        df = pd.read_csv(filename, low_memory=False)
        data = data.append(df, ignore_index=True, sort=False)
#data = data.apply(lambda x: x.str.strip(), axis=1)
data.dropna(how='all', inplace=True)
data.rename(columns=dict(zip(cols.oldcol, cols.newcol)), inplace=True)
#data.to_csv(out_dir / 'all_wab_data.csv')
data = data[list(cols.loc[(cols.person==1) | (cols.film==1)]['newcol'])]
#data.to_csv(out_dir / 'most_wab_data.csv')

#data['genre_and_niche_list'] = data['genre_and_niche_list'].fillna('').values.tolist()
#data['country_of_production_list'] = data['country_of_production_list'].fillna('').map(get_country_list)
#data['country_of_filming_list'] = data['country_of_filming_list'].fillna('').map(get_country_list)

categories = cols.loc[cols.category.notna() & cols.category.ne('school')]['category'].drop_duplicates()
for category in categories:
    newcols = cols.loc[cols.category==category]['newcol']

#make contact list
if 1==0:
    cur_data = pd.DataFrame()
    cur_cols = cols.loc[cols.person==1].copy()
    categories = cur_cols.loc[cur_cols.category.notna() & cur_cols.category.ne('school')]['category'].drop_duplicates()
    items = cur_cols['newcol'].drop_duplicates()
    for category in categories:
        oldcols = cur_cols.loc[cur_cols.category==category]['oldcol']
        newcols = cur_cols.loc[cur_cols.category==category]['newcol']
        df = data[list(oldcols)].copy()
        df.dropna(how='all', inplace=True)
        if len(df):
            df.rename(columns=dict(zip(oldcols, newcols)), inplace=True)
            df['category'] = re.sub('\d+', '', category)
            cur_data = cur_data.append(df, sort=False)
    cur_data.drop_duplicates(inplace=True)

    cur_data.to_csv('contacts.csv', index=False)
    cur_data.loc[cur_data.email.notna()][['f_name', 'l_name', 'email']].drop_duplicates().to_csv('contacts_cc.csv', index=False)

#make film list
if 1==0:
    cur_cols = cols.loc[cols.film==1].copy()
    cur_cols.loc[cur_cols.category.notna(), 'newcol'] = cur_cols.loc[cur_cols.category.notna()]['category'].str.replace('\d+', '')  + '_' + cur_cols.loc[cur_cols.category.notna()]['newcol']
    oldcols = cur_cols['oldcol']
    newcols = cur_cols['newcol']
    cur_data = data[list(oldcols)].copy()
    cur_data.dropna(how='all', inplace=True)
    cur_data.rename(columns=dict(zip(oldcols, newcols)), inplace=True)
    cur_data.columns = newcols
    cur_data.drop_duplicates().to_csv(out_dir / 'films.csv')
