from pathlib import Path
import numpy as np
from collections import Counter
import pandas as pd
import csv
import matplotlib.pyplot as plt
from scipy.stats import describe


def make_dist():
    cat_ary = np.array([[16, 14, 9, 24],
                        [14, 9, 9, 17],
                        [24, 14, 14, 20],
                        [17, 13, 11, 21],
                        [17, 16, 10, 24]])
    
    origin_ary = np.array([[20, 27, 0],
                        [16, 19, 0],
                        [24, 24, 0],
                        [21, 24, 0],
                        [23, 27, 0]])
    metro_dc = .3
    for row in origin_ary:
        row[2] = row[1]*metro_dc
        row[1] = row[1]*(1-metro_dc)
    
    return {'category' : {'pct' : np.true_divide(cat_ary, cat_ary.sum(axis=1, keepdims=True)).mean(axis=0), 
                          'avg' : cat_ary.sum(axis=1).mean(), 
                          'std' : cat_ary.std(axis=1).mean()}, 
            'origin' : {'pct' : np.true_divide(origin_ary, origin_ary.sum(axis=1, keepdims=True)).mean(axis=0), 
                        'avg' : origin_ary.sum(axis=1).mean(), 
                        'std' : origin_ary.std(axis=1).mean()}}
    
def make_festival(dist):
    films = int(np.random.normal(dist['category']['avg'], dist['category']['std'], 1))
    categories = np.random.choice(['Animation', 'Documentary', 'Narrative Feature', 'Narrative Short'], 
                                  films,
                                  p=dist['category']['pct'])
    origin = np.random.choice(['International', 'USA', 'DC'], 
                                  films,
                                  p=dist['origin']['pct'])
    attendance = np.random.choice(range(10, 150), films)
    votes = [Counter(np.random.choice(['Fair', 'Good', 'Great'], screening, p=np.random.dirichlet(np.random.rand(3), 1)[0])) for screening in attendance]
    df = {'Category' : categories, 
                 'Origin' : origin, 
                 'Attendance' : attendance, 
                 'Fair' : [v['Fair'] for v in votes], 
                 'Good' : [v['Good'] for v in votes], 
                 'Great' : [v['Great'] for v in votes]}
    return pd.DataFrame(df, columns=df.keys())

def make_festival_actual(year):
    df = pd.read_csv(data_raw / '{} DCIFF Balloting.csv'.format(year), usecols=['Name', 'Category', 'Great', 'Good', 'Fair', 'Origin'])
    df = df.fillna(0)
    df['Attendance'] = df['Fair'] + df['Good'] + df['Great']
    return df

def finish_festival(df, year):
    total_attendance = sum(df['Attendance'])
    q = df['Attendance'].quantile([.25, .5, .75])
    df['AttendanceQuartile'] = 4 - (df['Attendance'].between(0, q[.25])*1 + df['Attendance'].between(0, q[.5])*1 + df['Attendance'].between(0, q[.75])*1)

    votes = df[['Fair', 'Good', 'Great']]
    df['year'] = year

    #df['stdevRaw'] = [sd(max(screening), sum(screening)) for index, screening in votes.iterrows()]
    df['stdev+1'] = [sd(max(screening), sum(screening)+1) for index, screening in votes.iterrows()]
    #df['stdevA'] = [sd(max(screening), total_attendance) for index, screening in votes.iterrows()]
    
    #df['ScoreRaw'] = [score_film_v2(screening) for index, screening in votes.iterrows()]
    df['Score+1'] = [score_film_v2(screening, N_plus=1) for index, screening in votes.iterrows()]
    #df['ScoreA'] = [score_film_v2(screening, N=total_attendance) for index, screening in votes.iterrows()]

    #df['RankRaw'] = df['ScoreRaw'].rank(ascending=False, method='min')
    #df['catRankRaw'] = df.groupby('Category')['ScoreRaw'].rank(ascending=False, method='min')
    #df['originRankRaw'] = df.groupby('Origin')['ScoreRaw'].rank(ascending=False, method='min')
    df['Rank+1'] = df['Score+1'].rank(ascending=False, method='min')
    df['catRank+1'] = df.groupby('Category')['Score+1'].rank(ascending=False, method='min')
    df['originRank+1'] = df.groupby('Origin')['Score+1'].rank(ascending=False, method='min')
    #df['RankA'] = df['ScoreA'].rank(ascending=False, method='min')
    #df['catRankA'] = df.groupby('Category')['ScoreA'].rank(ascending=False, method='min')
    #df['originRankA'] = df.groupby('Origin')['ScoreA'].rank(ascending=False, method='min')

    df['stdev'] = df['stdev+1']
    df['Score'] = df['Score+1']
    df['Rank'] = df['Rank+1']
    df['catRank'] = df['catRank+1']
    df['originRank'] = df['originRank+1']
    print(df[['Name', 'Score', 'Rank']])

    df = winners(df)
    #df = df.sort_values('Rank')
    return df

def score_film(votes, N=None, N_plus=0):
    values = {'Fair' : 0, 'Good' : 0, 'Great' : 0}
    votes = votes.to_dict()
    max_val = max(votes.values())
    if N is None:
        N = sum(votes.values()) + N_plus
    m = sd(max_val, N)
    for k, v in votes.items():
        values[k] = (v/N)*m
    return (values['Great']*3) + (values['Good']*2) + values['Fair']

def score_film_v2(votes, N=None, N_plus=0):
    values = {'Fair' : 0, 'Good' : 0, 'Great' : 0}
    votes = votes.to_dict()
    if N is None:
        N = sum(votes.values()) + N_plus
    for k, v in votes.items():
        if v==0:
            values[k] = 0
        else:
            m = sd(v, N)
            print(k, v, N, m)
            values[k] = (v/N)*m
    print(values['Great']*3, values['Good']*2, values['Fair'])
    return (values['Great']*3) + (values['Good']*2) + values['Fair']

def tests(df, describe=None, award=None, score=None, all=None):
    if award or all:
        print('correlation - Attendance:Award', round(np.corrcoef(df['Attendance'], df['Award'].notna())[1,0], 2))
        print('correlation - AttendanceQuartile:Award', round(np.corrcoef(df['AttendanceQuartile'], df['Award'].notna())[1,0], 2))
    if score or all:
        print('correlation - Attendance:Rank', round(np.corrcoef(df['Attendance'], df['Rank'])[1,0], 2))
        print('correlation - Attendance:Score', round(np.corrcoef(df['Attendance'], df['Score'])[1,0], 2))
    if all:
        print('correlation - Attendance:RankRaw', round(np.corrcoef(df['Attendance'], df['RankRaw'])[1,0], 2))
        print('correlation - Attendance:ScoreRaw', round(np.corrcoef(df['Attendance'], df['ScoreRaw'])[1,0], 2))
        print('correlation - Attendance:Rank+1', round(np.corrcoef(df['Attendance'], df['Rank+1'])[1,0], 2))
        print('correlation - Attendance:Score+1', round(np.corrcoef(df['Attendance'], df['Score+1'])[1,0], 2))
        print('correlation - Attendance:RankA', round(np.corrcoef(df['Attendance'], df['RankA'])[1,0], 2))
        print('correlation - Attendance:ScoreA', round(np.corrcoef(df['Attendance'], df['ScoreA'])[1,0], 2))
    if score or all:
        print('correlation - stdev:Rank', round(np.corrcoef(df['stdev'], df['Rank'])[1,0], 2))
    if all:
        print('correlation - stdev:RankRaw', round(np.corrcoef(df['stdevRaw'], df['RankRaw'])[1,0], 2))
        print('correlation - stdev+1:Rank+1', round(np.corrcoef(df['stdev+1'], df['Rank+1'])[1,0], 2))
        print('correlation - stdevA:RankA', round(np.corrcoef(df['stdevA'], df['RankA'])[1,0], 2))
    if score or all:
        print('correlation - Attendance:stdev', round(np.corrcoef(df['Attendance'], df['stdev'])[1,0], 2))
    if all:
        print('correlation - Attendance:stdevRaw', round(np.corrcoef(df['Attendance'], df['stdevRaw'])[1,0], 2))
        print('correlation - Attendance:stdev+1', round(np.corrcoef(df['Attendance'], df['stdev+1'])[1,0], 2))
        print('correlation - Attendance:stdevA', round(np.corrcoef(df['Attendance'], df['stdevA'])[1,0], 2))
    if describe or all:
        print('score - mean', round(np.mean(df['Score']), 2))
        print('score - median', round(np.median(df['Score']), 2))
        print('score - stdev', round(np.std(df['Score']), 2))

def winners(df):
    df.loc[df.Rank==1, 'Award'] = 'Best of Fest'

    for category in df['Category'].drop_duplicates():
        min_rank = min(df.loc[df.Award.isna() & (df.Category==category)]['catRank'])
        idx = df.loc[(df.catRank==min_rank) & (df.Category==category)].index[0]
        df.loc[df.index==idx, 'Award'] = 'Best {}'.format(category)

#    for origin in df.loc[df.Origin!='USA']['Origin'].drop_duplicates():
#        min_rank = min(df.loc[df.Award.isna() & (df.Origin==origin)]['originRank'])
#        idx = df.loc[(df.originRank==min_rank) & (df.Origin==origin)].index[0]
#        df.loc[df.index==idx, 'Award'] = 'Best {} Film'.format(origin)

    return df

data_dir = Path('data')
data_raw = data_dir / 'raw'
data_out = data_dir / 'out'

columns = ['Name', 'Category', 'Great', 'Good', 'Fair', 'Origin', 'Score', 'Attendance', 'year', 'stdev', 'Rank', 'catRank', 'originRank', 'Award']

sd = lambda n, N: 1-((1.96/2)*np.sqrt(((n/N)*(1-(n/N)))/n))

actual = None
for year in [2019]:
    festival = make_festival_actual(year)
    festival = finish_festival(festival, year)
    festival.to_csv(data_out / 'sim_{}.csv'.format(year), columns=columns)
    try:
        actual = actual.append(festival)
    except:
        actual = festival

#dist = make_dist()
#data = None
#for n in range(0,50):
#    festival = make_festival(dist)
#    festival = finish_festival(festival, n)
#    try:
#        data = data.append(festival)
#    except:
#        data = festival
#data.to_csv(data_out / 'sim.csv', columns=columns[1:])

#print('Simulation')
#tests(data, award=1, score=1)
#print()
#print('Actual')
#tests(actual, award=1, score=1)
#for year in [2017, 2018, 2019]:
#    print()
#    print('Actual {}'.format(year))
#    tests(actual[actual.year==year], award=1, score=1)
    
#df = pd.read_csv(data_raw / '2017 DCIFF Balloting.csv')
#df['Fair'] = df['Fair'].fillna(0)
#df['Good'] = df['Good'].fillna(0)
#df['Great'] = df['Great'].fillna(0)
#df['Attendance'] = df['Fair'] + df['Good'] + df['Great']
#df = finish_festival(df, 2017)
#df.drop(columns='Award')
#df['Award'] = df['Actual Award']
#print()
#print('Actual Actual 2017')
#tests(df, award=1, score=1)
#df.to_csv(data_out / 'sim_2017a.csv'.format(year), columns=columns)


