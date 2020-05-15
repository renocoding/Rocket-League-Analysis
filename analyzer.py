import os
import sys
import pprint
import requests
import re
import pickle
from scipy.stats import pearsonr
import numpy as np

# Functions
def load_data(url):
    response = requests.get(url)
    return response

def usage(exit_code=0):
    progname = os.path.basename(sys.argv[0])
    print(f'''Usage: {progname} [-p PAGES]
    -p PAGES, how many pages of players to collect data from (100 per page)
    Default number of pages is 9''')
    sys.exit(exit_code)


def href_generator(urls):
    for url in urls:
        page = load_data(url)
        href_list = []
        for line in page.text.splitlines():
            if re.search(r'notooltip', line):
                href = re.search('href=\"(.*)\"', line)
                if(href):
                    yield href.group(1)

def get_tag_data(href_list):
    for href in href_list:
        player_stats = []
        new_url = "https://rocketleague.tracker.network" + href
        yield load_data(new_url)

def main():

    # initialize variables
    arguments = sys.argv[1:]
    num_pages = 9 #each page contains 100 players, with the 1st page containing the best
    page_counter = 1
    base_url = "https://rocketleague.tracker.network/ranked-leaderboards/all/12?page=" # format of the url for all leaderboard pages
    leaderboard_urls = []
    mvp_rate_list = []
    goal_rate_list = []
    save_rate_list = []
    assist_rate_list = []


    # loop through command line arguments and get necessary information
    while arguments:
        argument = arguments.pop(0)
        if argument == '-p':
            num_pages = int(arguments.pop(0))
        elif argument == '-h':
            usage(0)
        else:
            usage(1)

    # make a list of all leaderboard pages url's
    while page_counter <= num_pages:
        leaderboard_urls.append(base_url + str(page_counter))
        page_counter += 1

    # make generator that contains the html for each page
    href_list = href_generator(leaderboard_urls)

    # use html from each page to collect html data for every player in the top 900 players
    print("Beginning to enter stats...")
    counter = 0
    players_generator = get_tag_data(href_list)

    # iterate through each player's stat page
    for player_html in players_generator:
        player_stats = []
        save_i = 0
        for i, line in enumerate(player_html.text.splitlines()): #iterate through each line of response

            # use regex to find mvp/win ratio
            if re.search(r'MVP/Win', line):
                save_i = i
            if i - save_i == 3:
                for num in line.splitlines():
                    isNum = False
                    for char in num:
                        if char.isdigit():
                            isNum = True
                    if isNum:
                        player_stats.append(float(num)) # mvp/win

            # use regex to find goal-save-assist ratio, store the 3 numbers in a temporary list
            stats_no_group = re.search('y: ([0-9]+)', line)
            if(stats_no_group):
                for stat in stats_no_group.group(1).splitlines():
                    player_stats.append(float(stat))

        # if the 3 numbers are successfully found, add themm to their respective list
        if(len(player_stats) == 4):
            sumStats = sum(player_stats, 1)
            mvp_rate_list.append(player_stats[0])
            goal_rate_list.append(player_stats[1] / sumStats)
            save_rate_list.append(player_stats[2] / sumStats)
            assist_rate_list.append(player_stats[3] / sumStats)
            counter+=1
        print("Completed", str(counter), "of", str(100 * num_pages))
    print("Finished entering stats")

    # create arrays from the list
    mvp_rate = np.array(mvp_rate_list)
    goal_rate = np.array(goal_rate_list)
    save_rate = np.array(save_rate_list)
    assist_rate = np.array(assist_rate_list)

    # determine correlation using pearsonr
    goal_c, goal_p = pearsonr(goal_rate, mvp_rate)
    save_c, save_p = pearsonr(save_rate, mvp_rate)
    assist_c, assist_p = pearsonr(assist_rate, mvp_rate)

    print("Goal Rate to MVP Rate Correlation:", goal_c, goal_p)
    print("Save Rate to MVP Rate Correlation:", save_c, save_p)
    print("Assist Rate to MVP Rate Correlation:", assist_c, assist_p)






# Main Execution

if __name__ == '__main__':
    main()
