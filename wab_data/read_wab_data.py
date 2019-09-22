from pathlib import Path
import pandas as pd
import re

data_dir = Path('data')

cols = pd.read_csv(data_dir / 'map_columns.csv')
cols['newcol1'] = cols.apply(lambda x: x['newcol'] if pd.isna(x['category']) else x['category'] + '_' + x['newcol'], axis=1)

data = pd.DataFrame()
for filename in data_dir.iterdir():
    if re.match('\d{4}', filename.stem) and filename.suffix=='.csv':
        df = pd.read_csv(filename, low_memory=False)
        data = data.append(df, ignore_index=True, sort=False)
data = data.apply(lambda x: x.str.strip(), axis=1)
data = data.dropna(how='all')
#data.rename(columns=dict(zip(cols.oldcol, cols.newcol1))).to_csv('wab_data.csv')

#make contact list
if 1==0:
    contacts = pd.DataFrame()
    contact_cols = cols.loc[cols.person==1]
    categories = contact_cols.loc[contact_cols.category.notna() & contact_cols.category.ne('school')]['category'].drop_duplicates()
    items = contact_cols['newcol'].drop_duplicates()
    for category in categories:
        oldcols = contact_cols.loc[contact_cols.category==category]['oldcol']
        newcols = contact_cols.loc[contact_cols.category==category]['newcol']
        df = data[list(oldcols)]
        df = df.dropna(how='all')
        if len(df):
            df = df.rename(columns=dict(zip(oldcols, newcols)))
            df['category'] = re.sub('\d+', '', category)
            contacts = contacts.append(df, sort=False)
    contacts.drop_duplicates().to_csv('contacts.csv', index=False)
    contacts.loc[contacts.email.notna()][['f_name', 'l_name', 'email']].drop_duplicates().to_csv('contacts_cc.csv', index=False)
    print('total:{}'.format(len(contacts)))
    print('email addresses:{}'.format(len(contacts.loc[contacts.email.notna()].drop_duplicates())))
    for category in categories:
        print('{}: {}'.format(re.sub('\d+', '', category), len(contacts.loc[contacts.category==re.sub('\d+', '', category)].drop_duplicates())))

#make film list
if 1==1:
    films = pd.DataFrame
    film_cols = cols.loc[cols.film==1]


#data.rename(columns=dict(zip(cols.oldcol, cols.newcol1))).to_csv(data_dir / 'wab_data.csv', index=False)

#print(data[film_cols.oldcol].columns)