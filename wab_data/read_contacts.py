from pathlib import Path
import pandas as pd
import re

data_dir = Path('data')

cols = pd.read_csv(data_dir / 'map_columns.csv')
cols = cols[cols['contact_info']==1]
categories = list(cols.loc[cols['category'].notna(), 'category'].drop_duplicates())

print(list(cols.loc[cols.contact_info.notna(), 'newcol'].drop_duplicates()))

#data = pd.DataFrame()
#for filename in data_dir.iterdir():
#    if re.match('\d{4}', filename.stem) and filename.suffix=='.csv':
#        cur_data = pd.read_csv(filename, usecols=list(cols.oldcol), low_memory=False)
#        data = data.append(cur_data, ignore_index=True, sort=False)

#for row in data.iterrows():
#    for item in zip(row[1].index, row[1].values):
#        print(item)
#    for item in row[1]:
#        print(item.index)
    
