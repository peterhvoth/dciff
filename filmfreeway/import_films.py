from pathlib import Path
import pandas as pd
import re

def get_category(s):
    feature = True if re.search('\(over 40 mins\)', s, re.IGNORECASE) else False
    doc = True if re.search('documentary', s, re.IGNORECASE) else False
    animation = True if re.search('animation', s, re.IGNORECASE) else False
    hs = True if re.search('high school', s, re.IGNORECASE) else False
    
    if hs:
        result = 'High School'
    elif animation:
        result = 'Animation'
    elif doc and feature:
        result = 'Documentary Feature'
    elif doc and not feature:
        result = 'Documentary Short'
    elif feature:
        result = 'Narrative Feature'
    else:
        result = 'Narrative Short'
    return result

def get_multi(s, n=0):
    result = '' 
    if pd.isna(s):
        return ''
    else:
        result = s.split(',')
    if n==1:
        return result[0]
    elif n>1:
        return result[:n]
    else:
        return result

data_dir = Path('~/Documents/DCIFF')

google_drive_cols = ['Category', 'Title', 'Contact Name', 'Contact Email', 'Contact Phone', 'Run Time', 'Country', 
                     'Completion Date', 'Director 1', 'Producer 1', 'Cast 1', 'Cast 2', 'Cast 3', 'Premiere', 'Synopsis']
colmap = {'Project Title' : 'Title', 'Category' : 'Category', 'Duration' : 'Run Time', 
          'Completion Date' : 'Completion Date', 'DC Metro' : 'DC Metro', 'Email' : 'Contact Email', 
          'Phone' : 'Contact Phone', 'Country of Origin' : 'Country', 'Synopsis' : 'Synopsis'}

columns = pd.read_csv(Path(data_dir / 'cols_in.csv'))
columns = columns.loc[columns.iloc[:,2]==1].iloc[:,1]

ff_data = pd.read_csv(Path(data_dir / 'filmfreeway-submissions.csv')).loc[:,columns]
ff_data = ff_data.rename(columns={'Submission Custom Answer 3':'DC Metro'})
ff_data['Category'] = ff_data.loc[:,'Submission Categories'].apply(get_category)
ff_data = ff_data.drop(columns='Submission Categories')
ff_data['Alumni'] = ff_data.loc[:,'Flag'].apply(lambda x: True if x=='Alumni' else False)
ff_data = ff_data.drop(columns='Flag')

df = pd.DataFrame()
df[list(colmap.values())] = ff_data[list(colmap.keys())]
df[['Cast 1', 'Cast 2', 'Cast 3']] = ff_data.loc[:,'Key Cast'].apply(lambda x: pd.Series(get_multi(x, 3)))
df['Contact Name'] = ff_data.apply(lambda x: x['First Name'] + ' ' + x['Last Name'], axis=1)
df['Director 1'] = ff_data.loc[:,'Directors'].apply(get_multi, n=1)
df['Producer 1'] = ff_data.loc[:,'Producers'].apply(get_multi, n=1)
df['Premiere'] = ''

ff_data.to_csv(Path(data_dir / 'filmfreeway-useful.csv'), index=False)
df.to_csv(Path(data_dir / 'filmfreeway-google_drive.csv'), columns=google_drive_cols, index=False)
