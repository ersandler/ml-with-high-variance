#!/usr/bin/env python
# coding: utf-8

# In this notebook, I'll be modifying my previous functions to get player histories, calculate overachievement, and build a valid FPL team to be able to take in additional parameters to allow for more customizable metrics. 

# In[3]:


import requests
import pandas as pd
import numpy as np
from collections import defaultdict
from datetime import datetime
from tqdm import tqdm


# In[ ]:





# ## get_player_history

# In[21]:


def construct_fixture_dict(mw_start, mw_end):
    """ constructs a map of fixture ids to the matchweek where the fixture takes place
    
    Inputs:
        mw_start(int): mw where dictionary will start collecting fixture ids
        mw_end(int): mw where dictionary will stop collecting fixture ids, inclusive
        
    Returns:
        fixtures_dict(dict): keys are PL fixture IDs, values are the matchweek where fixture has/will take place \
                                note: value=None if fixture is currently unscheduled
    """
    
    # initialize dictionary
    fixtures_dict = dict()
    
    # api call
    url = "https://fantasy.premierleague.com/api/fixtures/"
    r = requests.get(url)
    json = r.json()

    for fix in json:
        
        # check if fixture is unscheduled
        if fix['event'] != None:
            
            if fix['event'] >= mw_start:
                
                # checking if we're past the last matchweek we want to check
                if fix['event'] > mw_end:
                    return fixtures_dict
                else: 
                    # add fixture to map
                    fixtures_dict[fix['id']] = fix['event']
        
    return fixtures_dict


# In[18]:


def get_player_history(pid, mw_start, mw_end, fix_dict=None):
    """ gets dataframe containing history of player's games for current season
    
    Inputs: 
        pid(int): player id
        mw_start(int): matchweek where dataframe will start collecting game history
        mw_end(int): matchweek where dataframe will stop collecting game history, inclusive
        fix_dict(dict): map of PL fixture IDs to matchweeks where fixture occured/will occur
    """
    # checking to see if user has provided a fix_dict (stops us from having to make a new one)
    if fix_dict == None:
        fix_dict = construct_fixture_dict(mw_start, mw_end)
    
    # api call
    url = f'https://fantasy.premierleague.com/api/element-summary/{pid}/'
    r = requests.get(url)
    json = r.json()
    
    # convert json to df
    player_hist = pd.DataFrame(json['history'])
    
    # create column 'mw' that holds matchweek each fixture took place
    player_hist['mw'] = player_hist['fixture'].replace(fix_dict)
    
    # selected only matchweeks in range
    filtered_player_hist = player_hist[player_hist['mw'].isin(range(mw_start, mw_end + 1))]

    return filtered_player_hist


# In[23]:


# it works!
get_player_history(5, 3, 5)


# ## Calculating weighted average score by position

# In[5]:


def get_positional_averages():
    """ creates a dict of average fpl game score for each position. asset's scores are weighted by ownership; 
        more owned assets are weighted higher. 
    
    Returns:
        averages_dict(dict): map of element_type (1, 2, 3, or 4) to average score(float)
    """
    
    
    # import player statistics
    url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
    r = requests.get(url)
    json = r.json()
    df_elements = pd.DataFrame(json['elements'])
    
    # get columns we care about
    df_data = df_elements.loc[:, ('web_name', 'id', 'element_type', 'points_per_game', 'selected_by_percent',                     'minutes', 'chance_of_playing_this_round')]

    # making all possible data floats (default is string)
    for col in df_data.columns:
        try:
            df_data[col] = df_data[col].astype(float)
        except(ValueError):
            pass

    # slice out players who haven't played
    bool_points = df_data['points_per_game'] > 0
    df_data = df_data.loc[bool_points, :]

    # calculating average for each position
    averages_dict = dict()
    for pos in df_data['element_type'].unique():

        pos_average = 0

        # get only one position
        bool_pos = df_data['element_type'] == pos
        df_pos = df_data.loc[bool_pos, :]

        # iterate through each player, calculate their weighted average score
        for idx in df_pos.index:
            pos_average += ((df_pos.loc[idx, 'selected_by_percent'] / 100) * df_pos.loc[idx, 'points_per_game'])

        # adjusting for amount of assets owned in each position
        if pos == 1:
            pos_average = pos_average / 2
        elif pos == 4:
            pos_average = pos_average / 3
        else:
            pos_average = pos_average / 5

        # add to dictionary
        averages_dict[pos] = pos_average
        
    return averages_dict


# ## Putting it all together with calc_overachievement

# In[6]:


def calc_overachievement(pid, element_type, avg_dict, mw_start=1, mw_end=38):
    """ calculates how often player scores better than average for a single game
    
    Inputs:
        pid(int): player id
        element_type(int): represents positions; 1 for GK, 2 for DEF, 3 for MID, 4 for ATT
        avg_dict(dict): dict containing average for each position
        
        
    Returns:
        float_over(float): decimal representing % of time a player got over avg points in this season
    """
    
    # get player history
    df_hist = get_player_history(pid, mw_start, mw_end)
    bool_played = df_hist['minutes'] > 0
    df_hist = df_hist.loc[bool_played, :]
    
    # calculate overachievement percentage
    bool_overachieve = df_hist['total_points'] >= avg_dict[element_type]
    float_over = (bool_overachieve.astype(int).mean())
    
    return float_over


# # function to check whether a lineup is legal

# In[16]:


def check_lineup(gks, defs, mids, fwds):
    """ put counts of each position """
    if (gks + defs + mids + fwds) != 11:
        return False
    if gks != 1 or defs < 3 or fwds < 1:
        return False
    if defs > 5 or mids > 5 or fwds > 5:
        return False
    return True


# ## get_team_score

# In[26]:


def get_team_score(df_team, mw, col_id='id', col_start='start'):
    """ gets the score of an fpl team from a dataframe 
    
    Inputs:
        df_team(df): dataframe that holds information about team
        mw(int): matchweek to judge team for
        col_id(any): name of column where player id values are stored, default is 'id'
        col_start(any): name of column where data for whether player started or not is stored, default is 'start'
        
    """
    
    # make sure our columns are in the df
    assert col_id in df_team.columns, f'col_id={col_id} is not a feature of df_team'
    assert col_start in df_team.columns, f'col_start={col_start} is not a feature of df_team'
    

    df_on = df_team[df_team['start'] == 1].copy()
    df_bench = df_team[df_team['start'] != 1].copy()
    
    # get rid of bench players who didnt play
    for idx in df_bench.index:
        pid = int(df_bench.loc[idx, col_id])
        if get_player_history(pid, mw, mw)['minutes'].sum() == 0:
            df_bench.drop(idx, inplace=True)

    # for each player, check if they played. if not, remove them from df
    for idx in df_on.index:
        pid = int(df_on.loc[idx, col_id])
        if get_player_history(pid, mw, mw)['minutes'].sum() == 0:
            if len(df_bench) == 0:
                # we're out of bench players to try
                pass
            else:
                # iterate through bench to find first player that makes team legal
                pass_next = False
                
                for sub in df_bench.index:
                    if not pass_next:

                        df_prospect = df_on.drop(idx).copy()

                            
                        df_prospect.loc[sub, :] = list(df_bench.loc[sub, :])
                        
                        counts = df_prospect['element_type'].value_counts()
                        if check_lineup(counts[1], counts[2], counts[3], counts[4]):
                            df_on = df_prospect.copy()
                            df_bench.drop(sub, inplace=True)
                            pass_next = True
                    
    total_score = 0
    # iterate through each player in the team
    for idx in df_on.index:
        # get their score for the given matchweek, add to total
        pid = int(df_on.loc[idx, col_id])
        player_hist = get_player_history(pid, mw, mw)
        total_score += player_hist['total_points'].sum() * (1 + df_on.loc[idx, 'captain'])
    
    return total_score


# ## get_num_fixtures
# given a pid and mw, return the number of fixtures a player can play in that mw

# In[8]:


def get_num_fixtures(pid, mw, fix_dict=None):
    """ returns  number of fixtures player will play in a given matchweek
    
    Inputs:
        pid(int): player id
        mw(int): matchweek queried
        fix_dict(dict): map of PL fixture IDs to matchweeks where fixture occured/will occur
        
    Returns:
        num_fix(int): number of fixtures a player will play in queried matchweek
    
    """
    # check if user has provided a fix_dict
    if fix_dict == None:
        fix_dict = construct_fixture_dict(mw, mw)
    
    # api call
    url = f'https://fantasy.premierleague.com/api/element-summary/{pid}/'
    r = requests.get(url)
    json = r.json()
    
    # get fixtures
    player_fix = pd.DataFrame(json['fixtures'])
    
    # create column with matchweek when fixture will be played
    player_fix['mw'] = player_fix['id'].replace(fix_dict)
    
    # get only matchweek in question
    filtered_player_fix = player_fix[player_fix['mw'] == mw]
    
    num_fix = len(filtered_player_fix)
    
    return num_fix


# In[9]:


get_num_fixtures(5, 10)


# # create json dict
# This dictionary will mean we don't have to query the API every time we want a player's json. 

# In[26]:


import os
import json
def create_json_dict(player_ids):
    """ player_ids must be iterable/listlike """
    # this dictionary will collect player json objects so we don't have to keep re-querying the API
    player_jsons = defaultdict(lambda: None)

    # Define the directory path
    directory = "FPLjsons/"
    # Create the directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)

    for pid in player_ids:
        print(pid, end=' | ')
        url = f'https://fantasy.premierleague.com/api/element-summary/{pid}/'
        r = requests.get(url)
        j = r.json()
        
        player_jsons[pid] = j
        
    # save the dictionary to the specified file path
    current_date = datetime.today()
    formatted_date = current_date.strftime('%m-%d-%Y')
    
    file_path = f"FPLjsons/jsons-{formatted_date}"
    with open(file_path, 'w') as file:
        json.dump(dict(player_jsons), file)


# In[11]:


ls_pid = [5, 6, 12, 13, 14, 19, 20, 29, 31, 113, 540, 36, 42, 43, 47, 48, 49, 50, 60, 584, 599, 63, 65, 70, 85, 86, 89, 595, 643, 90, 96, 101, 104, 105, 106, 108, 110, 112, 119, 122, 129, 131, 132, 133, 134, 135, 143, 148, 151, 153, 157, 160, 161, 165, 168, 173, 178, 475, 594, 596, 605, 126, 145, 197, 199, 202, 203, 211, 216, 217, 611, 220, 221, 223, 225, 228, 229, 230, 231, 234, 240, 242, 245, 249, 250, 254, 259, 260, 261, 262, 263, 265, 267, 270, 275, 280, 281, 282, 283, 288, 558, 591, 688, 290, 291, 303, 304, 305, 308, 309, 313, 52, 321, 326, 328, 575, 582, 586, 602, 614, 631, 342, 343, 344, 350, 352, 353, 355, 356, 365, 369, 616, 373, 376, 377, 379, 386, 396, 597, 617, 402, 406, 407, 412, 415, 416, 421, 424, 427, 430, 28, 378, 436, 439, 447, 453, 604, 713, 33, 476, 482, 488, 576, 638, 663, 693, 493, 501, 504, 506, 509, 511, 513, 516, 519, 520, 639, 522, 523, 524, 526, 528, 539, 542, 544, 642, 664, 545, 551, 557, 559, 563, 565, 567, 569, 572, 590]


# In[28]:


create_json_dict(ls_pid)

