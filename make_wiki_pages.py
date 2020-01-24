from pathlib import Path
import pandas as pd
from datetime import datetime
import re

header = '<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.10/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.mediawiki.org/xml/export-0.10/ http://www.mediawiki.org/xml/export-0.10.xsd" version="0.10" xml:lang="en">'

data_dir = Path('/home/peterhvoth/Documents/DCIFF')
df = pd.read_csv(Path(data_dir / 'filmfreeway-useful.csv'))
f = open(Path(data_dir / 'mediawiki_import.xml'), 'w')
f.write(header)

for idx, row in df.iterrows():
    year = 2020
    completion_date = '' if pd.isna(row['Completion Date']) else datetime.strptime(row['Completion Date'], '%Y-%m-%d').year
    row.fillna('', inplace=True)
    row['Alumni'] = 'Yes' if row['Alumni'] else 'No'
    row = row.apply(lambda x: re.sub('\&', '&amp;', x))
    f.write('<page>\n')
    f.write('<title>{}</title>\n'.format(row['Project Title']))
    f.write('<ns>0</ns>\n')
    f.write('<revision>\n')
    f.write('\t<model>wikitext</model>\n')
    f.write('\t<format>text/x-wiki</format>\n')
    f.write('\t<text xml:space="preserve" bytes="6">{{Infobox film_pressinfo\n')
    f.write('\t|year = {}\n'.format(year))
    f.write('\t|category = {}\n'.format(row['Category']))
    f.write('\t|premiere = \n')
    f.write('\t|genre = {}\n'.format(row['Genres']))
    f.write('\t|country = {}\n'.format(row['Country']))
    f.write('\t|language = {}\n'.format(row['Language']))
    f.write('\t|runtime = {}\n'.format(row['Duration']))
    f.write('\t|completion_date = {}\n'.format(completion_date))
    f.write('\t|synopsis = \n')
    f.write('\t|trailer = {}\n'.format(row['Trailer URL']))
    f.write('\t|director = {}\n'.format(row['Directors']))
    f.write('\t|writer = {}\n'.format(row['Writers']))
    f.write('\t|producer = {}\n'.format(row['Producers']))
    f.write('\t|cast = {}\n'.format(row['Key Cast']))
    f.write('\t|website = {}\n'.format(row['Project Website']))
    f.write('\t|twitter = {}\n'.format(row['Twitter']))
    f.write('\t|facebook = {}\n'.format(row['Facebook']))
    f.write('\t|instagram = \n')
    f.write('\t|dc = {}\n'.format(row['DC Metro']))
    f.write('\t|alum = {}\n'.format(row['Alumni']))
    f.write('\t}}\n')
    if row['Synopsis']:
        f.write('==Film Synopsis==\n')
        f.write('{}\n'.format(row['Synopsis']))
    if row['Submitter Statement']:
        f.write('==Director Statement==\n')
        f.write('{}\n'.format(row['Submitter Statement']))
    if row['Submitter Biography']:
        f.write('==Director Biography==\n')
        f.write('{}\n'.format(row['Submitter Biography']))
    f.write('==News &amp; Reviews==\n')
    f.write('==Notes==\n')
    f.write('[[Category:{0} Selection]] [[Category:{1}]] [[Category:{0} {1}]] [[Category:{2}]]'.format(year, row['Category'], row['Country'] ))
    f.write('\t</text>\n')
    f.write('</revision>\n')
    f.write('</page>\n')
    
f.write('</mediawiki>')