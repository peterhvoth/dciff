import os
import pandas as pd
import re

write_columns = False
data = pd.DataFrame()
for filename in os.listdir('./'):
    if re.match('\d{4}\.csv', filename):
        cur_data = pd.read_csv(filename, low_memory=False)
        data = data.append(cur_data, ignore_index=True, sort=False)
data = data.dropna(axis=1, how='all')
print(data.columns)
if write_columns:
    with open('wab_columns.txt', 'w') as f:
        for col in data.columns:
            f.write(col + '\n')
data.to_csv('wab_data_original.csv')
