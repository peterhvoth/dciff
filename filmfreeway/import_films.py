from pathlib import Path
import pandas as pd
import re

def get_category(s):
    series = True if re.search('Series', s, re.IGNORECASE) else False
    feature = True if re.search('\(over 40 mins\)', s, re.IGNORECASE) else False
    doc = True if re.search('documentary', s, re.IGNORECASE) else False
    animation = True if re.search('animation', s, re.IGNORECASE) else False
    hs = True if re.search('high school', s, re.IGNORECASE) else False
    
    if hs:
        result = 'High School'
    elif series:
        result = 'Series Episode'
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

drop_cols = ['Tracking Number', 'Lyrics', 'Project Type', 'Student Project', 'Production Budget', 'Shooting Format', 'Aspect Ratio', 'Film Color', 
             'Camera', 'Lens', 'Focal Length', 'Shutter Speed', 'Aperture', 'ISO / Film', 'Other Credits', 'Rating', 'Submission Date', 
             'Submission Status', 'Judging Status', 'Submission Deadlines', 'Submission Fee', 'Discount Code', 'Assigned Judges', 
             'Screenings / Awards', 'Distributor Information', 'Submission ID', 'Submission Notes', 'Submission Custom Field 1', 
             'Submission Custom Answer 1', 'Submission Custom Field 2', 'Submission Custom Answer 2', 'Submission Custom Field 3']

cols = {'main' : ['First Name', 'Last Name', 'Birthdate', 'Gender', 'Email', 'Phone', 'Address', 'Address 2', 'City', 'State', 'Postal Code', 'Country', 
                 'Project Title', 'Project Title (Original Language)', 'Synopsis', 'Synopsis (Original Language)', 'Duration', 'Country of Origin', 
                 'Language', 'Trailer URL', 'Country of Filming', 'Project Website', 'Twitter', 'Facebook', 'Genres', 'Completion Date', 
                 'First-time Filmmaker', 'Directors', 'Writers', 'Producers', 'Key Cast', 'Submitter Statement', 'Submitter Biography', 'Flag', 
                 'Submission Categories', 'Submission Link', 'Submission Password', 'Submission Custom Answer 3'], 
        'cheat_sheet' : ['Category', 'Title', 'Contact Name', 'Contact Email', 'Contact Phone', 'Run Time', 'Completion Date', 'Synopsis', 'Director 1', 
                         'Producer 1', 'Cast 1', 'Cast 2', 'Cast 3', 'Premiere', 'DC Metro', 'Female', 'Screener', 'Screener Password']}

colmap = {'Project Title' : 'Title', 'Category' : 'Category', 'Duration' : 'Run Time', 'Completion Date' : 'Completion Date', 
          'Email' : 'Contact Email', 'Phone' : 'Contact Phone', 'Synopsis' : 'Synopsis'}

df = pd.read_csv(Path(data_dir / 'filmfreeway-submissions.csv'))
df = df[df['Judging Status']=='Selected'].drop(drop_cols, axis=1)

df_main = df.loc[:,cols['main']]
df_main['Project Title'] = df_main['Project Title'].apply(lambda x: re.sub('"(.*)"', '\g<1>', x)) 
df_main['DC Metro'] = df['Submission Custom Answer 3']
df_main['Category'] = df.loc[:,'Submission Categories'].apply(get_category)
df_main['Alumni'] = df.loc[:,'Flag'].apply(lambda x: True if x=='Alumni' else False)
df_main['Country'] = df['Country of Origin'].apply(lambda x: x.split(',')[0])

countries = df_main['Country'].drop_duplicates().sort_values()

df = pd.DataFrame()
df[list(colmap.values())] = df_main[list(colmap.keys())]
df[['Cast 1', 'Cast 2', 'Cast 3']] = df_main.loc[:,'Key Cast'].apply(lambda x: pd.Series(get_multi(x, 3)))
df['Contact Name'] = df_main.apply(lambda x: x['First Name'] + ' ' + x['Last Name'], axis=1)
df['Director 1'] = df_main.loc[:,'Directors'].apply(get_multi, n=1)
df['Producer 1'] = df_main.loc[:,'Producers'].apply(get_multi, n=1)
df['Premiere'] = ''
df['Female'] = df_main['Gender'].apply(lambda x: 1 if x=='Female' else '')
df['DC Metro'] = df_main['DC Metro'].apply(lambda x: 1 if x=='Yes' else '')
df[['Screener', 'Screener Password']] = df_main.apply(lambda x: pd.Series({'Screener' : x['Submission Link'], 'Screener Password' : x['Submission Password']}) if not re.search('filmfreeway\.com', x['Submission Link']) else pd.Series({'Screener' : '', 'Screener Password' : ''}), axis=1)

for ctry in countries:
    df[ctry] = df_main['Country of Origin'].apply(lambda x: 1 if x==ctry else '')

df_main.to_csv(Path(data_dir / 'filmfreeway-useful.csv'), index=False)
df.reindex(columns=list(df.columns).extend(countries)).to_csv(Path(data_dir / 'filmfreeway-google_drive.csv'), index=False)
