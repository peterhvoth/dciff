#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import requests
from lxml import html
import re

def extract_imdb_id(url):
    from urllib import parse
    path = parse.urlparse(url).path
    path = path.split('/')
    return path[2] or False

def unidecodeTrim(str):
    from unidecode import unidecode
    if str:
        str = unidecode(str)
        str = re.sub('^[\r\n\s]+', '', str)
        str = re.sub('[\r\n\s]+$', '', str)
    else:
        str = ''
    return str

def getNameInfo(name_id):
    result = []
    url = base_url + '/name/' + name_id + '/'
    req = requests.get(url)
    content = html.fromstring(req.text.encode('utf-8'))
    root = content.findall(".//div[@id='filmography']//div[@class='filmo-row odd']")
    for item in root:
        result.append(item.attrib['id'].split('-'))
    root = content.findall(".//div[@id='filmography']//div[@class='filmo-row even']")
    for item in root:
        result.append(item.attrib['id'].split('-'))
    return result

conn = sqlite3.connect(':memory:')
conn.row_factory = sqlite3.Row
db = conn.cursor()
sql = 'CREATE TABLE titles (title_id text, title text, year text, country text, language text)'
db.execute(sql)
sql = 'CREATE TABLE names (name_id text, name text)'
db.execute(sql)
sql = 'CREATE TABLE credits (title_id text, name_id text, credit text)'
db.execute(sql)

itemprop = ['name', 
            'duration', 
            'genre', 
            'datePublished', 
            'image', 
            'description', 
            'director', 
            'name', 
            'creator', 
            'actors', 
            'actor', 
            'duration']

itemtype = ['http://schema.org/Movie', 
            'http://schema.org/Organization', 
            'http://schema.org/Person']

base_url = 'http://www.imdb.com'
pages = ['tt7653826', 
#'tt6950864', 
#'tt7981652', 
#'tt5605076', 
# 'tt8133096', 
# 'tt6233550', 
# 'tt7755698', 
# 'tt6063648', 
# 'tt7385812', 
# 'tt7482172', 
# 'tt6966866', 
# 'tt6985634', 
# 'tt6264018', 
# 'tt7343512', 
# 'tt7901352', 
# 'tt7013822', 
# 'tt6203324', 
# 'tt6090976', 
# 'tt7852230', 
# 'tt7883452', 
# 'tt6951518', 
# 'tt6433232', 
# 'tt7090150', 
# 'tt6477328', 
# 'tt6235850', 
# 'tt6963348', 
# 'tt7087722', 
# 'tt6774924', 
# 'tt7753208', 
# 'tt5948090', 
# 'tt7281094', 
# 'tt7901362', 
# 'tt6723676', 
# 'tt7312266', 
# 'tt5145366', 
# 'tt6722104', 
# 'tt5037684', 
# 'tt6221504', 
# 'tt7827550', 
# 'tt2095768', 
# 'tt7516368', 
# 'tt6992278', 
# 'tt7136714', 
# 'tt7374040', 
# 'tt6300238', 
'tt7520674']
#page_info = [{'type' : 'title', 'id' : 'tt1677720'}]

for page in pages:
    url = base_url + '/title/' + page + '/'
    
    quicklinks = {'fullcredits' : url + 'fullcredits', #Full Cast and Crew
                  #'releaseinfo' : url + 'releaseinfo', #Release Dates
                  #'officialsites' : url + 'officialsites', #Official Sites
                  #'companycredits' : url + 'companycredits', #Company Credits
                  #'locations' : url + 'locations', #Filming &amp; Production
                  'technical' : url + 'technical', #Technical Specs
                  #'taglines' : url + 'taglines', #Taglines
                  'plotsummary' : url + 'plotsummary', #Plot Summary
                  'synopsis' : url + 'synopsis', #Synopsis
                  'keywords' : url + 'keywords', #Plot Keywords
                  #'parentalguide' : url + 'parentalguide', #Parents Guide
                  #'news' : url + 'news', #News
                  #'externalsites' : url + 'externalsites', #External Sites
                  'awards' : url + 'awards', #Awards
                  #'faq' : url + 'faq', #FAQ
                  #'reviews' : url + 'reviews', #User Reviews
                  #'ratings' : url + 'ratings', #User Ratings
                  #'externalreviews' : url + 'externalreviews', #External Reviews
                  #'criticreviews' : url + 'criticreviews', #Metacritic Reviews
                  #'mediaindex' : url + 'mediaindex', #Photo Gallery
                  #'videogallery' : url + 'videogallery', #Trailers and Videos
                  #'trivia' : url + 'trivia', #Trivia
                  #'goofs' : url + 'goofs', #Goofs
                  #'crazycredits' : url + 'crazycredits', #Crazy Credits
                  #'quotes' : url + 'quotes', #Quotes
                  #'alternateversions' : url + 'alternateversions', #Alternate Versions
                  #'movieconnections' : url + 'movieconnections', #Connections\
                  'soundtrack' : url + 'soundtrack'} #Soundtracks  
    
    req = requests.get(url)
    content = html.fromstring(req.text.encode('utf-8'))
    
    root = content.find(".//*[@class='title_wrapper']")
    titleDetails = {}
    titleDetails['id'] = page
    titleDetails['title'] = unidecodeTrim(root.findtext("./*[@itemprop='name']"))
    titleDetails['year'] = unidecodeTrim(root.findtext(".//*[@id='titleYear']/a"))
    titleDetails['country'] = ''
    titleDetails['language'] = ''

    details = content.findall(".//div[@id='titleDetails']/div[@class='txt-block']")
    for item in details:
        heading = item.findtext("h4")
        if heading:
            heading = heading.lower()
            heading = unidecodeTrim(re.sub('\:', '', heading))
            value = item.findtext("a")
            if not value:
                for i in item.xpath("text()"):
                    if re.sub('[\n\r\s]+', '', i):
                        value = unidecodeTrim(i)
            else:
                value = unidecodeTrim(value)
            titleDetails[heading] = value
    db.execute('INSERT INTO titles (title_id, title, year, country, language) VALUES (?, ?, ?, ?, ?)', 
               (titleDetails['id'], titleDetails['title'], titleDetails['year'], titleDetails['country'], titleDetails['language']))

    req = requests.get(quicklinks['fullcredits'])
    content = html.fromstring(req.text)
    
    root = content.find(".//div[@id='fullcredits_content']")
    categories = [i.text for i in root.findall("./h4")]
    personnel = [i for i in root.findall("./table")]

    for idx, category in enumerate(categories):
        category = unidecodeTrim(category)
        category = re.sub('\sby$', '', category)
        rows = personnel[idx].findall(".//tr")
        for row in rows:
            elements = row.findall(".//a")
            for elem in elements:
                try:
                    print(elem.tag, elem.attrib, elem.text.strip())
                except:
                    continue
                name_id = extract_imdb_id(elem.attrib['href'])
                db.execute('INSERT INTO credits (title_id, name_id, credit) VALUES (?, ?, ?)', (page, name_id, category))
                filmography = getNameInfo(name_id)
                print(name_id)
                print(len(filmography))
                for film in filmography:
                    db.execute('INSERT INTO credits (title_id, name_id, credit) VALUES (?, ?, ?)', (film[0], name_id, film[1]))
                print()

if 1==0:
    sql = 'SELECT * FROM titles t INNER JOIN credits c ON t.title_id=c.title_id GROUP BY t.title_id, c.name_id'
    db.execute(sql)
    for row in db.fetchall():
        print(dict(row))

if 1==0:
    sql = 'SELECT * FROM credits WHERE credit="Directed"'
    db.execute(sql)
    for row in db.fetchall():
        print(getNameInfo(row['name_id']))

if 1==0:
    sql = 'SELECT * FROM titles'
    db.execute(sql)
    for row in db.fetchall():
        print(dict(row))
    
if 1==0:
    sql = 'SELECT * FROM names'
    db.execute(sql)
    for row in db.fetchall():
        print(dict(row))
    
if 1==0:
    sql = 'SELECT * FROM credits'
    db.execute(sql)
    for row in db.fetchall():
        print(dict(row))
    
    
