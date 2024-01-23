#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
import json
from collections import defaultdict
from datetime import datetime
import requests
import schedule
import time


# In[ ]:


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


# In[ ]:


ls_pid = [5, 6, 12, 13, 14, 19, 20, 29, 31, 113, 540, 36, 42, 43, 47, 48, 49, 50, 60, 584, 599, 63, 65, 70, 85, 86, 89, 595, 643, 90, 96, 101, 104, 105, 106, 108, 110, 112, 119, 122, 129, 131, 132, 133, 134, 135, 143, 148, 151, 153, 157, 160, 161, 165, 168, 173, 178, 475, 594, 596, 605, 126, 145, 197, 199, 202, 203, 211, 216, 217, 611, 220, 221, 223, 225, 228, 229, 230, 231, 234, 240, 242, 245, 249, 250, 254, 259, 260, 261, 262, 263, 265, 267, 270, 275, 280, 281, 282, 283, 288, 558, 591, 688, 290, 291, 303, 304, 305, 308, 309, 313, 52, 321, 326, 328, 575, 582, 586, 602, 614, 631, 342, 343, 344, 350, 352, 353, 355, 356, 365, 369, 616, 373, 376, 377, 379, 386, 396, 597, 617, 402, 406, 407, 412, 415, 416, 421, 424, 427, 430, 28, 378, 436, 439, 447, 453, 604, 713, 33, 476, 482, 488, 576, 638, 663, 693, 493, 501, 504, 506, 509, 511, 513, 516, 519, 520, 639, 522, 523, 524, 526, 528, 539, 542, 544, 642, 664, 545, 551, 557, 559, 563, 565, 567, 569, 572, 590]


# In[ ]:


# Schedule the job with the argument
schedule.every().week.do(create_json_dict, ls_pid)

while True:
    schedule.run_pending()
    # Sleep for an hour (3600 seconds)
    time.sleep(3600)

