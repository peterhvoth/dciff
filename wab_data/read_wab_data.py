from pathlib import Path
import pandas as pd
import re

data_dir = Path('data')
raw_dir = data_dir / 'raw'
interim_dir = data_dir / 'interim'
out_dir = data_dir / 'out'

cols = pd.read_csv(interim_dir / 'map_columns.csv')
cols['newcol1'] = cols.apply(lambda x: x['newcol'] if pd.isna(x['category']) else x['category'] + '_' + x['newcol'], axis=1)

data = pd.DataFrame()
for filename in raw_dir.iterdir():
    if re.match('\d{4}', filename.stem) and filename.suffix=='.csv':
        df = pd.read_csv(filename, low_memory=False)
        data = data.append(df, ignore_index=True, sort=False)
data = data.apply(lambda x: x.str.strip(), axis=1)
data = data.dropna(how='all')
#data.rename(columns=dict(zip(cols.oldcol, cols.newcol1))).to_csv('wab_data.csv')

#make contact list
cur_data = pd.DataFrame()
cur_cols = cols.loc[cols.person==1].copy()
categories = cur_cols.loc[cur_cols.category.notna() & cur_cols.category.ne('school')]['category'].drop_duplicates()
items = cur_cols['newcol'].drop_duplicates()
for category in categories:
    oldcols = cur_cols.loc[cur_cols.category==category]['oldcol']
    newcols = cur_cols.loc[cur_cols.category==category]['newcol']
    df = data[list(oldcols)]
    df = df.dropna(how='all')
    if len(df):
        df = df.rename(columns=dict(zip(oldcols, newcols)))
        df['category'] = re.sub('\d+', '', category)
        cur_data = cur_data.append(df, sort=False)
cur_data.drop_duplicates().to_csv(out_dir / 'contacts.csv', index=False)
cur_data.loc[cur_data.email.notna()][['f_name', 'l_name', 'email']].drop_duplicates().to_csv(out_dir / 'contacts_cc.csv', index=False)
print('total:{}'.format(len(cur_data)))
print('email addresses:{}'.format(len(cur_data.loc[cur_data.email.notna()].drop_duplicates())))
for category in categories:
    print('{}: {}'.format(re.sub('\d+', '', category), len(cur_data.loc[cur_data.category==re.sub('\d+', '', category)].drop_duplicates())))

