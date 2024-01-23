import requests
import pandas as pd
import numpy as np


# # Calculating asset weighted average return by position

# getting total players
url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
r = requests.get(url)
json = r.json()
json['total_players']

# import player statistics (for id 5: Gabriel M)
pid = 5
url = f'https://fantasy.premierleague.com/api/element-summary/{pid}/'
r = requests.get(url)
json = r.json()


def get_player_history(pid):
    
    url = f'https://fantasy.premierleague.com/api/element-summary/{pid}/'
    r = requests.get(url)
    json = r.json()
    
    player_hist = pd.DataFrame()
    for fix in json['history']:
        mw = pd.Series(fix)
        player_hist = pd.concat([player_hist, mw], axis=1)
        
    player_hist = player_hist.T.reset_index(drop=True)
        
    return player_hist


# this is Gabriel's history
df_hist = get_player_history(5)
bool_played = df_hist['minutes'] >= 1
df_hist = df_hist.loc[bool_played, :]
df_hist


def calc_overachievement(pid, avg=4):
    """ calculates how often player scores better than average for a single game"""
    
    # get player history
    df_hist = get_player_history(pid)
    bool_played = df_hist['minutes'] >= 1
    df_hist = df_hist.loc[bool_played, :]
    
    # calculate overachievement percentage
    bool_overachieve = df_hist['total_points'] >= avg
    float_over = (bool_overachieve.astype(int).mean())
    
    return float_over

