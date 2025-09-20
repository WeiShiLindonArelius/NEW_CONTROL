import numpy as np
import pandas as pd
from Teams import Team, generate_lineups_six_to_four, Coach, choose_perks
from contests import round_robin, alter_lineup
from colorama import Fore, Style
from dump_pickle import dump_pkl
from load_pickle import season_wipe, load_pkl
import time
from random import choice, shuffle, uniform, randint
from leagues import league_season, user_draft, player_changes, grade_players, double_elim_12, caps
from Games import best_of, enablePrint
import concurrent.futures
from stat_functions import season_stats, best_of_stats, region_mvp, QUERY, initiate_databases, finalize_series_data
from statistics import mean, stdev
from collections import OrderedDict, defaultdict
import re
from openpyxl import load_workbook, Workbook
import sqlite3


#main begins on line 387, and the first season begins on line 468
#to change manual/auto team sorting, line 480 change manual=
#line 1200 contains variable to toggle rosters being written jj
#NO_SQL is in Players.py

#to give more time to choose perks or coaching decisions, go to the top of Team and change timeout= in timed_input

#GLOBAL VARIABLES
avg_stats_df = pd.DataFrame(columns=['Kills', 'Deaths', 'Damage', 'Effect', 'Overkill', 'Mitigated'])


def weighted_averages(team):  # takes in a team and calculates weighted average of each stat, returns a dataframe
    #despite being called weighted_averages, this produces a full dataframe for a team season

    final_dict = {'Team': team.name, 'Power': None, 'Attack Damage': None, 'Attack Speed': None, 'Critical %': None,
                  'Critical X': None, 'Health': None, 'Spawn Time': 0, 'Lineup Wins': team.wins,
                  'Lineup Losses': team.losses
        , 'Match Wins': team.match_wins, 'Match Losses': team.match_losses, 'Match Draws': team.match_draws}

    power_list = [player.power for player in team.players]
    total_power = (power_list[0] * 9) + (power_list[1] * 7) + (power_list[2] * 6) + (power_list[3] * 6) + (
                power_list[4] * 4) + (power_list[5] * 4)
    final_dict['Power'] = round((total_power / 36), 2)

    atk_dmg_list = [player.atk_dmg for player in team.players]
    total_atk_dmg = (atk_dmg_list[0] * 9) + (atk_dmg_list[1] * 7) + (atk_dmg_list[2] * 6) + (atk_dmg_list[3] * 6) + (
                atk_dmg_list[4] * 4) + (atk_dmg_list[5] * 4)
    final_dict['Attack Damage'] = round((total_atk_dmg / 36), 2)

    atk_spd_list = [player.atk_spd for player in team.players]
    total_atk_spd = (atk_spd_list[0] * 9) + (atk_spd_list[1] * 7) + (atk_spd_list[2] * 6) + (atk_spd_list[3] * 6) + (
                atk_spd_list[4] * 4) + (atk_spd_list[5] * 4)
    final_dict['Attack Speed'] = round((total_atk_spd / 36), 2)

    crit_pct_list = [player.crit_pct for player in team.players]
    total_crit_pct = (crit_pct_list[0] * 9) + (crit_pct_list[1] * 7) + (crit_pct_list[2] * 6) + (
                crit_pct_list[3] * 6) + (crit_pct_list[4] * 4) + (crit_pct_list[5] * 4)
    final_dict['Critical %'] = round((total_crit_pct / 36), 5)

    crit_x_list = [player.crit_x for player in team.players]
    total_crit_x = (crit_x_list[0] * 9) + (crit_x_list[1] * 7) + (crit_x_list[2] * 6) + (crit_x_list[3] * 6) + (
                crit_x_list[4] * 4) + (crit_x_list[5] * 4)
    final_dict['Critical X'] = round((total_crit_x / 36), 3)

    health_list = [player.max_health for player in team.players]
    total_health = (health_list[0] * 9) + (health_list[1] * 7) + (health_list[2] * 6) + (health_list[3] * 6) + (
                health_list[4] * 4) + (health_list[5] * 4)
    final_dict['Health'] = round((total_health / 36), 3)

    spawn_list = [player.spawn_time for player in team.players]
    total_spawn = (spawn_list[0] * 9) + (spawn_list[1] * 7) + (spawn_list[2] * 6) + (spawn_list[3] * 6) + (
                spawn_list[4] * 4) + (spawn_list[5] * 4)
    final_dict['Spawn Time'] = round((total_spawn / 36), 2)

    return pd.DataFrame([final_dict])

def team_season_dataframe(teams, season_no):
    #writes the average team player innate stats and their season record to a file
    #despite the name, this takes in a list of teams and writes them out after making a DF

    team_stats_df = pd.DataFrame(columns=['Team', 'Power', 'Attack Damage', 'Attack Speed', 'Critical %', 'Critical X',
                                              'Health', 'Spawn Time', 'Lineup Wins', 'Lineup Losses',
                                              'Match Wins', 'Match Losses', 'Match Draws'])
    for team in teams:
        team_stats_df = pd.concat([team_stats_df, weighted_averages(team)])

    path = "ControlAverageStats.xlsx"

    with pd.ExcelWriter(path, engine='openpyxl') as writer:
        team_stats_df.to_excel(writer, sheet_name='TeamWeightedAverages', index=False)


def sort_players_by_xWAR(team):
    team.players.sort(key=lambda pl: pl.xWAR, reverse=True)

def sort_all_players(leagues, manual):
    #teams have a boolean called mine
    def move_player(old, new, swap_team):
        swap_team.players[old], swap_team.players[new] = swap_team.players[new], swap_team.players[old]


    for league in leagues:
        for team in league:
            grade_players(team.players, is_team=True)
            if team.mine:
                enablePrint()
                if manual:
                    print(f"Here is the current order of your players ({team.name}):" + Fore.RESET)
                    i = 0
                    for player in team.players:
                        print(f"Slot {i}, {player}")
                        i += 1
                    while True:
                        user_choice = input(Fore.BLUE + "Would you like to move anything? If not, press N.\n"
                                                        "To move a player, press their Slot Number.")
                        if user_choice == 'N' or user_choice == 'n':
                            break
                        else:
                            user_choice = int(user_choice)
                        old_slot = user_choice
                        new_slot = int(input("What will their new slot be?"))
                        move_player(old_slot, new_slot, team)
                        print(Fore.RESET + "Here is the new order of your players:")
                        i = 0
                        for player in team.players:
                            print(f"Slot {i}, {player}")
                            i += 1
            team.lineups = generate_lineups_six_to_four(team.players, team.team_coach)



def write_to_file(filename=None, words=None, mode='w', error=False):
    if error:
        filename = 'error_output'
        mode = 'a'

    with open(filename, mode) as f:
        f.write(words + '\n')


def clean_file(file_path):
    with open(file_path, 'r+') as file:
        lines = file.readlines()
        file.seek(0)
        file.truncate()

        delete_next_line = False

        for line in lines:
            # Check if the line contains a colon
            if ':' in line:
                delete_next_line = True
                continue

            # Check if the line should be deleted based on the previous line
            if delete_next_line:
                delete_next_line = False
                continue

            # Check if the line is empty
            if line.strip() == '':
                continue

            # Write the line back to the file
            file.write(line)

def format_champion_line(line):
    # Define a regex pattern to match the line format
    if "Regional" in line:

        pattern = re.compile(r'^S(\d+)\s(.+?)\sRegional\sChampion:\s(.+)$')

        # Use the regex pattern to match and extract groups
        match = pattern.match(line)

        # If the line matches the pattern, format it as required
        if match:
            seed = match.group(1)
            region = match.group(2)
            champion = match.group(3)
            formatted_line = f"{champion} (S{seed} {region} Regional Champion)"
            return formatted_line
        else:
            # If the line doesn't match the expected format, return the original line
            return line.strip()
    else:
        # Define a regex pattern to match the required line format
        pattern = re.compile(r'^S(\d+)\s(.+?)\sChampion:\s(.+)$')

        # Use the regex pattern to match and extract groups
        match = pattern.match(line)

        # If the input string matches the format, format it as required
        if match:
            seed = match.group(1)
            champion = match.group(3)
            formatted_string = f"{champion} (S{seed} {champion} Champion)"
            return formatted_string
        else:
            # If the input string doesn't match the expected format, return the original string
            return line.strip()

def sort_champions_by_seed(file_path='champs'):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Create a list to store tuples (seed, champion_info)
    champions = []
    regional_seed_data = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0}
    uni_seed_data = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0,
                     9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0, 15: 0, 16: 0}


    index = 0
    for line in lines:

        if line.startswith('Entered playoffs as'):
            parts = line.split()
            seed = int(parts[-2])
            champion_info = lines[index-1].strip()
            champion_info = format_champion_line(champion_info)
            champions.append((seed, champion_info))

        index += 1

    # Sort the champions list in descending order based on seed
    champions.sort(reverse=True, key=lambda x: x[0])

    # Print the sorted champions
    clean_file(file_path)
    with open(file_path, 'a') as file:
        file.write('\n')
        x = y = 0
        for champion in champions:
            x += 1
            file.write(f"{champion[1]} Entered playoffs as {champion[0]} seed.\n")
            if "Regional" in champion[1]:
                regional_seed_data[champion[0]] += 1
            else:
                uni_seed_data[champion[0]] += 1
            if x == 10:
                file.write('\n')
                y = 1
                x = 0
            if y == 1 and x == 9:
                file.write('\n')
                x = 0
        file.write('\n\n')
        #for i in range(1,9):
        #    file.write(f"{i} Seed: {regional_seed_data[i]} Regional Champs ({round(100*regional_seed_data[i]/len(regional_seed_data),2)}%)"
        #               f" {uni_seed_data[i]} Universal Champs ({round(100*uni_seed_data[i]/len(uni_seed_data),2)}%)")
        #below_8_seed_champs = sum(uni_seed_data[key] for key in range(9, 17))
        #file.write(f"9-16 Seeds: {uni_seed_data[i]} Universal Champs ({round(100*below_8_seed_champs/len(uni_seed_data),2)}%)")



def remove_duplicates_ordered(upl_standings):
    seen_teams = OrderedDict()
    unique_standings = []

    for team in upl_standings:
        if team not in seen_teams:
            unique_standings.append(team)
            seen_teams[team] = None

    return unique_standings


def extract_high_seed(text):
    int_values = [int(match.group()) for match in re.finditer(r'\b\d+\b', text)][:2]
    high_seed = min(int_values)
    return high_seed

def get_upsets(upset_list, upset_count):
    #upset[0]: a string of the upset ex: "12(Universal_Draconians) def. 6(Web-of-Nations_Oni) by a score of 547-504 (R2L Universal Playoffs)"
    #upset[1]: integer, difference between seeds
    #upset[2]: integer, highest seed in the match (the seed which was upset)


    clear_file('upsets')
    seed_diff_list = []
    non_rel_upsets = []
    uni_upsets = []
    high_seed_dict = {}

    for upset in upset_list:
        high_seed_dict[upset] = extract_high_seed(upset[0])
        seed_diff_list.append(upset[1])
        if "Relegation" not in upset[0]:
            non_rel_upsets.append(upset)
            if "Universal Playoffs:" in upset[0]:
                uni_upsets.append(upset)
    seed_diff_avg = mean(seed_diff_list)

    with open('upsets', 'a') as u:
        u.write(f"So far, there have been {len(upset_list)} upsets, with an average seed differential of {seed_diff_avg:.3f}.\n\n")
        upset_list.sort(key=lambda l: (l[1], -(high_seed_dict[l])), reverse=True)
        non_rel_upsets.sort(key=lambda l: (l[1], -(high_seed_dict[l])), reverse=True)
        uni_upsets.sort(key=lambda l: (l[1], -(high_seed_dict[l])), reverse=True)

        if len(uni_upsets) >= 5:
            u.write("\n5 Largest Universal League Upsets\n")
            for i in range(5):
                u.write(f"{uni_upsets[i][0]}\n")
        else:
            u.write(f"\n{len(uni_upsets)} Largest Universal League Upsets\n")
            for i in range(len(uni_upsets)):
                u.write(f"{uni_upsets[i][0]}\n")

        if len(non_rel_upsets) >= 5:
            u.write("\n5 Largest Upsets (not incl. Universal Relegation)\n")
            for i in range(5):
                u.write(f"{non_rel_upsets[i][0]}\n")
        else:
            u.write(f"\n{len(non_rel_upsets)} Largest Upsets (not incl. Universal Relegation)\n")
            for i in range(len(non_rel_upsets)):
                u.write(f"{non_rel_upsets[i][0]}\n")
        if len(upset_list) >= 3:
            u.write("\n3 Largest Overall Upsets\n")
            for i in range(3):
                u.write(f"{upset_list[i][0]}\n")
        else:
            u.write(f"\n{len(upset_list)} Largest Overall Upsets\n")
            for i in range(len(upset_list)):
                u.write(f"{upset_list[i][0]}\n")

        u.write("\nAll Upsets:\n")
        for t in upset_list:
            u.write(f"{t[0]}\n")



GENERAL_OUTPUT = False


# try def __print__(): to get rid of colorama

def recreate_excel_file(filename):
    wb = Workbook()
    wb.save(filename)


def clear_file(filename, excel=False,sheets='all'):
    if not excel:
        if isinstance(filename,list):
            for file in filename:
                with open(file, 'w') as c:
                    c.write('')
        else:
            with open(filename, 'w') as c:
                c.write('')
    else:
        workbook = load_workbook(filename)

        # Loop through every sheet in the workbook
        for sheet in (workbook.sheetnames if sheets=='all' else [sheets] if isinstance(sheets, str) else sheets):
            worksheet = workbook[sheet]

            worksheet.delete_rows(1, worksheet.max_row)

        # Save the cleared workbook
        workbook.save(filename)

def create_teams(count,region='None',season_count=0):
    TEAMS = []
    for i in range(count):
        temp = Team(region,season_count=season_count)
        TEAMS.append(temp)
    user_draft(TEAMS, season_count, is_regional=True, draft_name=f"{region} Preliminary Draft - Round 1")
    user_draft(TEAMS, season_count, is_regional=True, draft_name=f"{region} Preliminary Draft - Round 2")
    user_draft(TEAMS, season_count, is_regional=True, draft_name=f"{region} Preliminary Draft - Round 3")
    return TEAMS

def ordinal_string(n: int) -> str:
    if 10 <= n % 100 < 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"

def main():
    jackson_playing = False

    import warnings
    warnings.simplefilter(action='ignore', category=FutureWarning)

    start = time.time()
    # file clearing:
    clear_file(['my_teams', 'region_mvp.txt','region_mvp.txt','champs', 'error_output', 'upsets', 'draft_list', 'draft_history',
                'player_trait_data', 'team_coach_data', 'execution_time', 'playerstats', 'off_season_report', 'my_team_playerstats',
                'my_team_results', 'std_devs', 'cumulative_avg_std_devs', 'comebacks', 'cap_fallback', 'xWAR_tests'])

    #try:
    #    clear_file('PlayerSeasons.xlsx', excel=True)
    #except KeyError:
    #    recreate_excel_file('PlayerSeasons.xlsx')
    #try:
    #    clear_file("ControlAverageStats.xlsx", excel=True)
    #except KeyError:
    #    recreate_excel_file("ControlAverageStats.xlsx")
    #try:
    #    clear_file("ControlPlayerStats.xlsx", excel=True)
    #except FileNotFoundError:
    #    recreate_excel_file("ControlPlayerStats.xlsx")
    #try:
    #    clear_file("ChampStats.xlsx", excel=True,sheets='Sheet1')
    #except KeyError:
    #    clear_file("ChampStats.xlsx",sheets='Sheet1')

    my_team_count = 5
    franchise_mode = False #f r a n c h i s e

    SEASONS = 50
    end_season_times = [float(0) for _ in range(SEASONS+1)]

    season_stats_list = {}
    champ_list = []


    all_teams = []
    #this is the only list which should contain every single season list, from every single season, period

    uni_stats_list = {}
    dw_stats_list = {}
    sc_stats_list = {}
    ds_stats_list = {}
    wof_stats_list = {}
    iw_stats_list = {}
    cl_stats_list = {}
    hc_stats_list = {}
    sh_stats_list = {}

    upset_list = []
    upset_count = 0

    for i in range(SEASONS+1):
        uni_stats_list[i] = list()
        dw_stats_list[i] = list()
        sc_stats_list[i] = list()
        ds_stats_list[i] = list()
        wof_stats_list[i] = list()
        iw_stats_list[i] = list()
        cl_stats_list[i] = list()
        hc_stats_list[i] = list()
        sh_stats_list[i] = list()
    s0_stats_list = list()

    use_saved = False
    #this should work as of 11/02/2024



    if use_saved:
        try:
            upl_standings, dw_teams, sc_teams, ds_teams, wof_teams, iw_teams, cl_teams, hc_teams, sh_teams, season_count = load_pkl()
            uni_teams = upl_standings
        except ValueError:
            use_saved = False
            print(Fore.RED + "Failed to save values, starting new iteration.")
    if not use_saved:
        season_count = 0
        uni_teams = create_teams(26, "Universal", season_count=season_count)

        for team in uni_teams:
            team.history[season_count] = ""
        upl_standings = league_season(uni_teams, use_saved=False, season_count=0,upset_list=upset_list,upset_count=upset_count, region="Universal",stats_list=s0_stats_list)
        dw_sc = choice([True, False])
        ds_wof = choice([True, False])
        iw_cl = choice([True, False])
        hc_sh = choice([True, False])


        dw_teams = create_teams((21 if dw_sc or jackson_playing else 22), "Darkwing", season_count=season_count)
        sc_teams = create_teams((21 if not dw_sc or jackson_playing else 22), "Shining-Core", season_count=season_count)
        ds_teams = create_teams((21 if ds_wof or jackson_playing else 22), "Diamond-Sea", season_count=season_count)
        wof_teams = create_teams((21 if not ds_wof or jackson_playing else 22), "Web-of-Nations", season_count=season_count)
        iw_teams = create_teams((21 if iw_cl or jackson_playing else 22), "Ice-Wall", season_count=season_count)
        cl_teams = create_teams((21 if not iw_cl or jackson_playing else 22), "Candyland", season_count=season_count)
        hc_teams = create_teams((21 if hc_sh or jackson_playing else 22), "Hell's-Circle", season_count=season_count)
        sh_teams = create_teams((21 if not hc_sh or jackson_playing else 22), "Steel-Heart", season_count=season_count)


        my_team1 = Team(("Darkwing" if dw_sc else "Shining-Core"), mine=True, season_count=season_count)
        jackson_team1 = Team(("Darkwing" if not dw_sc else "Shining-Core"), mine=True, season_count=season_count,jackson=True)

        my_team2 = Team(("Diamond-Sea" if ds_wof else "Web-of-Nations"), mine=True, season_count=season_count)
        jackson_team2 = Team(("Diamond-Sea" if not ds_wof else "Web-of-Nations"), mine=True, season_count=season_count,jackson=True)

        my_team3 = Team(("Ice-Wall" if iw_cl else "Candyland"), mine=True, season_count=season_count)
        jackson_team3 = Team(("Ice-Wall" if not iw_cl else "Candyland"), mine=True, season_count=season_count,
                             jackson=True)

        my_team4 = Team(("Hell's-Circle" if hc_sh else "Steel-Heart"), mine=True, season_count=season_count)
        jackson_team4 = Team(("Hell's-Circle" if not hc_sh else "Steel-Heart"), mine=True, season_count=season_count,
                             jackson=True)

        if not jackson_playing:
            if dw_sc:
                dw_teams.append(my_team1)
            else:
                sc_teams.append(my_team1)

            if ds_wof:
                ds_teams.append(my_team2)
            else:
                wof_teams.append(my_team2)

            if iw_cl:
                iw_teams.append(my_team3)
            else:
                cl_teams.append(my_team3)

            if hc_sh:
                hc_teams.append(my_team4)
            else:
                sh_teams.append(my_team4)
            jackson_teams = []
        else:
            if dw_sc:
                dw_teams.append(my_team1)
                sc_teams.append(jackson_team1)
            else:
                sc_teams.append(my_team1)
                dw_teams.append(jackson_team1)

            if ds_wof:
                ds_teams.append(my_team2)
                wof_teams.append(jackson_team2)
            else:
                wof_teams.append(my_team2)
                ds_teams.append(jackson_team2)

            if iw_cl:
                iw_teams.append(my_team3)
                cl_teams.append(jackson_team3)
            else:
                cl_teams.append(my_team3)
                iw_teams.append(jackson_team3)

            if hc_sh:
                hc_teams.append(my_team4)
                sh_teams.append(jackson_team4)
            else:
                sh_teams.append(my_team4)
                hc_teams.append(jackson_team4)
            jackson_teams = [jackson_team1,jackson_team2,jackson_team3,jackson_team4]

        my_teams = [my_team1,my_team2,my_team3,my_team4]


        for i in range((len(my_teams))):
            my_team = my_teams[i]
            my_team.make_mine(my_team.name)
            ch_slots_amped = choice([[0,5], [1,4],[0,4,5], [1,4,5], [1,3,5]])
            ch_att_amped = choice([["Critical Chance", round(uniform(0.021,0.033), 3)], ["Attack Damage", randint(3,6)]])
            ch_slot_effect = [ch_slots_amped]
            ch_slot_effect.extend(ch_att_amped)
            choward_coach = Coach(region=my_team.region, fixed_slot_effect=ch_slot_effect,fixed_name="Carter Howard")
            my_team.change_coach(choward_coach)
            print('\n' + Fore.BLUE + f"{my_team.name} is your team. Coach: {str(choward_coach)}, {str(my_team.captain)}")
            my_team.print_roster(first=True)
        if jackson_playing:
            for i in range(len(jackson_teams)):
                j_team = jackson_teams[i]
                jk_slots_amped = choice([[0], [1]])
                jk_att_amped = ["Power", round(uniform(0.839, 0.99), 2)]
                jk_slot_effect = [jk_slots_amped]
                jk_slot_effect.extend(jk_att_amped)
                jkeefe_coach = Coach(region=j_team.region, fixed_slot_effect=jk_slot_effect,fixed_name="Jackson Keefe")
                j_team.change_coach(jkeefe_coach)
                print('\n' + Fore.BLUE + f"{j_team.name} is your team. Coach: {str(jkeefe_coach)}, {str(j_team.captain)}")
                j_team.print_roster(first=True)



        print(Fore.RESET)

    def regional_leagues(dw_teams,sc_teams,ds_teams,wof_teams,iw_teams,cl_teams,hc_teams,sh_teams,season_count,champ_list,franchise_mode=False):
            pre_qualif_tournament = []
            last_stand_tournament = {'5 Seeds' : [], '6 Seeds' : [], '7 Seeds' : [], '8 Seeds' : []}

            print(Fore.GREEN + "DARKWING REGION, " + Fore.RESET, end='')
            dw_teams = league_season(dw_teams, False, season_count=season_count, final_reversed=False,
                                     region='Darkwing Regional', stats_list=dw_stats_list,upset_list=upset_list,upset_count=upset_count, champ_list=champ_list,franchise_mode=franchise_mode)
            dw_qualified = dw_teams[:8]


            print(Fore.GREEN + "SHINING CORE REGION, " + Fore.RESET, end='')
            sc_teams = league_season(sc_teams, False, season_count=season_count, final_reversed=False,
                                     region='Shining-Core Regional', stats_list=sc_stats_list,upset_list=upset_list,upset_count=upset_count, champ_list=champ_list,franchise_mode=franchise_mode)
            sc_qualified = sc_teams[:8]

            print(Fore.GREEN + "DIAMOND SEA REGION, " + Fore.RESET, end='')
            ds_teams = league_season(ds_teams, False, season_count=season_count, final_reversed=False,
                                     region='Diamond-Sea Regional', stats_list=ds_stats_list,upset_list=upset_list,upset_count=upset_count, champ_list=champ_list,franchise_mode=franchise_mode)
            ds_qualified = ds_teams[:8]

            print(Fore.GREEN + "WEB OF NATIONS, " + Fore.RESET, end='')
            wof_teams = league_season(wof_teams, False, season_count=season_count, final_reversed=False,
                                      region='Web-of-Nations Regional', stats_list=wof_stats_list,upset_list=upset_list,upset_count=upset_count, champ_list=champ_list,franchise_mode=franchise_mode)
            wof_qualified = wof_teams[:8]

            print(Fore.GREEN + "ICE WALL REGION, " + Fore.RESET, end='')
            iw_teams = league_season(iw_teams, False, season_count=season_count, final_reversed=False,
                                     region='Ice-Wall Regional', stats_list=iw_stats_list,upset_list=upset_list,upset_count=upset_count, champ_list=champ_list,franchise_mode=franchise_mode)
            iw_qualified = iw_teams[:8]

            print(Fore.GREEN + "CANDYLAND REGION, " + Fore.RESET, end='')
            cl_teams = league_season(cl_teams, False, season_count=season_count, final_reversed=False,
                                     region='Candyland Regional', stats_list=cl_stats_list,upset_list=upset_list,upset_count=upset_count, champ_list=champ_list,franchise_mode=franchise_mode)
            cl_qualified = cl_teams[:8]

            print(Fore.GREEN + "HELL'S CIRCLE, " + Fore.RESET, end='')
            hc_teams = league_season(hc_teams, False, season_count=season_count, final_reversed=False,
                                     region="Hell's-Circle Regional", stats_list=hc_stats_list,upset_list=upset_list,upset_count=upset_count, champ_list=champ_list,franchise_mode=franchise_mode)
            hc_qualified = hc_teams[:8]

            print(Fore.GREEN + "STEEL HEART REGION, " + Fore.RESET, end='')
            sh_teams = league_season(sh_teams, False, season_count=season_count, final_reversed=False,
                                     region="Steel-Heart Regional", stats_list=sh_stats_list,upset_list=upset_list,upset_count=upset_count, champ_list=champ_list,franchise_mode=franchise_mode)
            sh_qualified = sh_teams[:8]

            dw_champ = dw_qualified[0]
            regional_champs.append(dw_champ)
            sc_champ = sc_qualified[0]
            regional_champs.append(sc_champ)
            ds_champ = ds_qualified[0]
            regional_champs.append(ds_champ)
            wof_champ = wof_qualified[0]
            regional_champs.append(wof_champ)
            iw_champ = iw_qualified[0]
            regional_champs.append(iw_champ)
            cl_champ = cl_qualified[0]
            regional_champs.append(cl_champ)
            hc_champ = hc_qualified[0]
            regional_champs.append(hc_champ)
            sh_champ = sh_qualified[0]
            regional_champs.append(sh_champ)

            # trans_region = ['Darkwing', 'Shining-Core', 'Diamond-Sea', 'Web-of-Nations', 'Ice-Wall', 'Candyland', "Hell's-Circle", 'Steel-Heart']
            count = 0
            for region in [dw_qualified, sc_qualified, ds_qualified, wof_qualified, iw_qualified, cl_qualified,
                           hc_qualified, sh_qualified]:
                for number in [1, 2, 3]:
                    pre_qualif_tournament.append(region[number])

                last_stand_tournament['5 Seeds'].append(region[4])
                last_stand_tournament['6 Seeds'].append(region[5])
                last_stand_tournament['7 Seeds'].append(region[6])
                last_stand_tournament['8 Seeds'].append(region[7])
                count += 1

            for region in [dw_qualified, sc_qualified, ds_qualified, wof_qualified, iw_qualified, cl_qualified,
                            hc_qualified, sh_qualified]:
                season_wipe(region)

            if len(last_stand_tournament['8 Seeds']) < 8:
                enablePrint()
                print(Fore.RED + "NOT ENOUGH 8 SEEDS!" + Fore.RESET)
                write_to_file(error=True, words="NOT ENOUGH 8 SEEDS!")
                time.sleep(1)
            if len(last_stand_tournament['7 Seeds']) < 8:
                enablePrint()
                print(Fore.RED + "NOT ENOUGH 7 SEEDS!" + Fore.RESET)
                write_to_file(error=True, words="NOT ENOUGH 7 SEEDS!")
                time.sleep(1)
            if len(last_stand_tournament['6 Seeds']) < 8:
                enablePrint()
                print(Fore.RED + "NOT ENOUGH 6 SEEDS!" + Fore.RESET)
                write_to_file(error=True, words="NOT ENOUGH 6 SEEDS!")
                time.sleep(1)
            if len(last_stand_tournament['5 Seeds']) < 8:
                enablePrint()
                print(Fore.RED + "NOT ENOUGH 5 SEEDS!" + Fore.RESET)
                write_to_file(error=True, words="NOT ENOUGH 6 SEEDS!")
                time.sleep(1)
            return regional_champs, pre_qualif_tournament, last_stand_tournament
    another = 'y'
    relegated = {} # int keys, team object values
    promoted = {}

    for num in range(SEASONS):

        for team in my_teams:
            choose_perks(team)

        season_count += 1

        write_to_file('comebacks', words=f"SEASON {season_count}", mode='a')

        total_stats = {'Power': 0, 'Attack Damage': 0, 'Attack Speed': 0, 'Critical %': 0, 'Critical X': 0,
                       'Spawn Time': 0, 'Health': 0, 'Age': 0}
        all_players = []
        with open("rosters", 'a') as w:
            w.write(f"SEASON NO. {season_count}\n")
            trans_region = ['Universal', 'Darkwing', 'Shining-Core', 'Diamond-Sea', 'Web-of-Nations', 'Ice-Wall',
                            'Candyland', "Hell's-Circle", 'Steel-Heart']
            trans_i = -1
            for league in [uni_teams, dw_teams, sc_teams, ds_teams, wof_teams, iw_teams, cl_teams, hc_teams, sh_teams]:
                trans_i += 1
                for team in league:
                    team.region = trans_region[trans_i]
                    for player in team.players:
                        total_stats['Power'] += player.power
                        total_stats['Attack Damage'] += player.atk_dmg
                        total_stats['Attack Speed'] += player.atk_spd
                        total_stats['Critical %'] += player.crit_pct
                        total_stats['Critical X'] += player.crit_x
                        total_stats['Spawn Time'] += player.spawn_time
                        total_stats['Health'] += player.max_health
                        total_stats['Age'] += player.age

                        all_players.append(player)
            grade_players(all_players, is_team=True)
            stats = ["power", "dps", "crit_pct", "crit_x", "max_health", "spawn_time"]
            std_devs = {"power": 0, "dps": 0, "crit_pct": 0, "crit_dmg": 0, "max_health": 0, "spawn_time": 0}
            global_std_devs = {"power": 0, "dps": 0, "crit_pct": 0, "crit_dmg": 0, "max_health": 0, "spawn_time": 0}
        for stat in stats:
            values = [getattr(p, stat) for p in all_players]  # or p[stat] if using dicts
            std_devs[stat] = stdev(values)
        with open('std_devs', 'a') as file:
            file.write(f"SEASON {season_count}\n\n")
            for stat in stats:
                file.write(f"S{season_count} {stat} standard deviation: {std_devs[stat]}\n")

        stats_data = defaultdict(list)

        if season_count <= 10:

            pattern = re.compile(r'^S\d+ (\w+) standard deviation: ([\d.]+)')

            with open('std_devs', 'r') as file:
                for line in file:
                    match = pattern.match(line)
                    if match:
                        stat, value = match.groups()
                        stats_data[stat].append(float(value))
            with open('cumulative_avg_std_devs', 'w') as file:
                file.write("\nCumulative Average Standard Deviations (first 5 seasons only):\n")
                for stat, values in stats_data.items():
                    avg = sum(values) / len(values)
                    file.write(f"{stat}: {avg}\n")

        relegated[season_count] = []
        promoted[season_count] = []

        sort_all_players([uni_teams, dw_teams, sc_teams, ds_teams, wof_teams, iw_teams, cl_teams, hc_teams, sh_teams], manual=False)

        with open("my_rosters", 'w') as file:
            file.write(f"!!!!!!_SEASON 4_!!!!!!\n")
        for league in [dw_teams, sc_teams, ds_teams, wof_teams, iw_teams, cl_teams, hc_teams, sh_teams]:
            season_wipe(league)
            for team in league:
                team.fired_coach_this_season = False
                if franchise_mode and team.mine:
                    alter_lineup(team)
                team.history[season_count] = ""

                if team.mine or team.jackson:
                    team.print_roster(first=True)
        if season_count != 0:
            season_wipe(uni_teams)
            for team in uni_teams:
                team.history[season_count] = ""

        uni_qualif_g1 = []
        uni_qualif_g2 = []
        regional_champs = []
        last_stand = []
        regional_champs, pqt, last_stand = regional_leagues(dw_teams,sc_teams,ds_teams,wof_teams,iw_teams,cl_teams,hc_teams,sh_teams,season_count=season_count,champ_list=champ_list,franchise_mode=franchise_mode)

        last_stand_groups = {key: [] for key in range(8)}
        shuffle(last_stand['5 Seeds'])
        shuffle(last_stand['6 Seeds'])
        shuffle(last_stand['7 Seeds'])
        shuffle(last_stand['8 Seeds'])


        for i in range(8):
            temp7_processed = False
            temp8_processed = False
            temp5_processed = False

            other_region = ""
            temp_6 = last_stand['6 Seeds'][i]
            temp_6.accolades['Last-Stand'] += 1
            last_stand_groups[i].append(temp_6)

            for temp_7 in last_stand['7 Seeds']:
                if temp_7.played_region[season_count] != temp_6.played_region[season_count]:
                    other_region = temp_7.played_region[season_count]
                    temp_7.accolades['Last-Stand'] += 1
                    last_stand_groups[i].append(temp_7)
                    last_stand['7 Seeds'].remove(temp_7)
                    temp7_processed = True
                    break

            if not temp7_processed:
                write_to_file(error=True, words=f"temp7 failsafe triggered. Length {len(last_stand['7 Seeds'])}")
                temp_7 = choice(last_stand['7 Seeds'])
                other_region = temp_7.played_region[season_count]
                temp_7.accolades['Last-Stand'] += 1
                last_stand_groups[i].append(temp_7)
                last_stand['7 Seeds'].remove(temp_7)

            for temp_8 in last_stand['8 Seeds']:
                if temp_8.played_region[season_count] not in [temp_6.played_region[season_count], other_region]:
                    temp_8.accolades['Last-Stand'] += 1
                    last_stand_groups[i].append(temp_8)
                    last_stand['8 Seeds'].remove(temp_8)
                    temp8_processed = True
                    break

            if not temp8_processed:
                write_to_file(error=True, words=f"temp8 failsafe triggered. Length {len(last_stand['8 Seeds'])}")
                temp_8 = choice(last_stand['8 Seeds'])
                temp_8.accolades['Last-Stand'] += 1
                last_stand_groups[i].append(temp_8)
                last_stand['8 Seeds'].remove(temp_8)

            for temp_5 in last_stand['5 Seeds']:
                if temp_5.played_region[season_count] not in [temp_6.played_region[season_count], other_region]:
                    temp_5.accolades['Last-Stand'] += 1
                    last_stand_groups[i].append(temp_5)
                    last_stand['5 Seeds'].remove(temp_5)
                    temp5_processed = True
                    break

            if not temp5_processed:
                write_to_file(error=True, words=f"temp5 failsafe triggered. Length {len(last_stand['8 Seeds'])}")
                temp_5 = choice(last_stand['5 Seeds'])
                temp_5.accolades['Last-Stand'] += 1
                last_stand_groups[i].append(temp_5)
                last_stand['5 Seeds'].remove(temp_5)

        last_stand_start_time = time.time()
        index = 0
        ls_group_names = ["A", 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        for key in last_stand_groups.keys():
            print(Fore.GREEN + f"LAST STAND, GROUP {ls_group_names[index]}: " + Fore.RESET, end='')
            index+=1
            temp_standings = round_robin(last_stand_groups[key], 40, 4, print_region_seed=True,cyan_seeds=[0,1],
                                                       red_seeds=[2,3])

            temp_standings[0].history[season_count] += f" 1st in Last Stand Group {key} -> Pre-Qualifying Group."
            pqt.append(temp_standings[0])

            temp_standings[1].history[season_count] += f" 2nd in Last Stand Group {key} -> Pre-Qualifying Group."
            pqt.append(temp_standings[1])

            temp_standings[2].history[season_count] += f" Eliminated from Last Stand. (3rd in Group {key})"

            temp_standings[3].history[season_count] += f" Eliminated from Last Stand. (4th in Group {key})"

            season_wipe(temp_standings)
        last_stand_end_time = time.time()
        with open('execution_time', 'a') as file:
            file.write(f"Season {season_count} Last Stand Execution Time: {round((last_stand_end_time - last_stand_start_time) / 60)} minutes, {round(((last_stand_end_time - last_stand_start_time) % 60), 2)} seconds.\n")

        for team in pqt:
            team.accolades['Pre-Qualifying'] += 1

        def parse_region_seed(a_team):
            # Split the region_seed into letters and integer
            region, seed = a_team.region_seed.split('-')
            return region, int(seed)

        def create_pre_qualifying_groups(pq_teams):
            group_a, group_b, group_c, group_d, group_e, group_f, group_g, group_h = [], [], [], [], [], [], [], []

            team_by_seed = {
                2: [], 3: [], 4: [], "Last-Stand" : [],
            }

            for pq_team in pq_teams:
                region, seed = parse_region_seed(pq_team)
                if seed == 2:
                    team_by_seed[2].append(pq_team)

                elif seed == 3:
                    team_by_seed[3].append(pq_team)
                elif seed == 4:
                    team_by_seed[4].append(pq_team)
                elif seed in [5,6,7,8]:
                    team_by_seed["Last-Stand"].append(pq_team)

            if len(team_by_seed[2]) != 8:
                print(Fore.RED + f"2 Seed PQ Group Error: Length {len(team_by_seed[2])}" + Fore.RESET)
            if len(team_by_seed[3]) != 8:
                print(Fore.RED + f"3 Seed PQ Group Error: Length {len(team_by_seed[3])}" + Fore.RESET)
            if len(team_by_seed[4]) != 8:
                print(Fore.RED + f"4 Seed PQ Group Error: Length {len(team_by_seed[4])}" + Fore.RESET)
            if len(team_by_seed["Last-Stand"]) != 16:
                print(Fore.RED + f"Last Stand PQ Group Error: Length {len(team_by_seed[4])}" + Fore.RESET)



            groups = [group_a, group_b, group_c, group_d, group_e, group_f, group_g, group_h]
            two_seed, three_seed, four_seed, ls_team1, ls_team2 = None, None, None, None, None
            #two_region, three_region, four_region, ls1_region, ls2_region = None, None, None, None, None
            three_found, four_found, ls1_found, ls2_found = False, False, False, False
            for g_i in range(8):
                three_found, four_found, ls1_found, ls2_found = False, False, False, False

                two_seed = choice(team_by_seed[2])
                team_by_seed[2].remove(two_seed)
                two_region = parse_region_seed(two_seed)[0]

                for t in team_by_seed[3]:
                    if parse_region_seed(t)[0] != two_region:
                        three_seed = t
                        team_by_seed[3].remove(three_seed)
                        three_found = True
                        break
                if not three_found:
                    three_seed = choice(team_by_seed[3])
                    team_by_seed[3].remove(three_seed)
                three_region = parse_region_seed(three_seed)[0]

                for t in team_by_seed[4]:
                    if parse_region_seed(t)[0] not in [two_region,three_region]:
                        four_seed = t
                        team_by_seed[4].remove(four_seed)
                        four_found = True
                        break
                if not four_found:
                    four_seed = choice(team_by_seed[4])
                    team_by_seed[4].remove(four_seed)
                four_region = parse_region_seed(four_seed)[0]

                for t in team_by_seed["Last-Stand"]:
                    if parse_region_seed(t)[0] not in [two_region,three_region,four_region]:
                        ls_team1 = t
                        team_by_seed["Last-Stand"].remove(ls_team1)
                        ls1_found = True
                        break
                if not ls1_found:
                    ls_team1 = choice(team_by_seed["Last-Stand"])
                    team_by_seed["Last-Stand"].remove(ls_team1)

                ls1_region = parse_region_seed(ls_team1)[0]

                for t in team_by_seed["Last-Stand"]:
                    if parse_region_seed(t)[0] not in [two_region,three_region,four_region,ls1_region]:
                        ls_team2 = t
                        team_by_seed["Last-Stand"].remove(ls_team2)
                        ls2_found = True
                        break
                if not ls2_found:
                    ls_team2 = choice(team_by_seed["Last-Stand"])
                    team_by_seed["Last-Stand"].remove(ls_team2)


                groups[g_i].extend([two_seed, three_seed, four_seed, ls_team1, ls_team2])
            return group_a, group_b, group_c, group_d, group_e, group_f, group_g, group_h

        group_a, group_b, group_c, group_d, group_e, group_f, group_g, group_h = create_pre_qualifying_groups(pqt)


        print(Fore.GREEN + "PRE-QUALIFYING, GROUP A: " + Fore.RESET, end='')
        group_a_standings = round_robin(group_a, r=20, qualify_range=len(group_a), print_region_seed=True, cyan_seeds=[0,1,2], red_seeds=[3,4])
        group_a_champ, group_a_runner_up, group_a_third = group_a_standings[:3]
        print(Fore.GREEN + "PRE-QUALIFYING, GROUP B: " + Fore.RESET, end='')
        group_b_standings = round_robin(group_b, r=20, qualify_range=len(group_a), print_region_seed=True, cyan_seeds=[0,1,2], red_seeds=[3,4])
        group_b_champ, group_b_runner_up, group_b_third = group_b_standings[:3]
        print(Fore.GREEN + "PRE-QUALIFYING, GROUP C: " + Fore.RESET, end='')
        group_c_standings = round_robin(group_c, r=20, qualify_range=len(group_a), print_region_seed=True, cyan_seeds=[0,1,2], red_seeds=[3,4])
        group_c_champ, group_c_runner_up, group_c_third = group_c_standings[:3]
        print(Fore.GREEN + "PRE-QUALIFYING, GROUP D: " + Fore.RESET, end='')
        group_d_standings = round_robin(group_d, r=20, qualify_range=len(group_a), print_region_seed=True, cyan_seeds=[0,1,2], red_seeds=[3,4])
        group_d_champ, group_d_runner_up, group_d_third = group_d_standings[:3]
        print(Fore.GREEN + "PRE-QUALIFYING, GROUP E: " + Fore.RESET, end='')
        group_e_standings = round_robin(group_e, r=20, qualify_range=len(group_a), print_region_seed=True, cyan_seeds=[0,1,2], red_seeds=[3,4])
        group_e_champ, group_e_runner_up, group_e_third = group_e_standings[:3]
        print(Fore.GREEN + "PRE-QUALIFYING, GROUP F: " + Fore.RESET, end='')
        group_f_standings = round_robin(group_f, r=20, qualify_range=len(group_a), print_region_seed=True, cyan_seeds=[0,1,2], red_seeds=[3,4])
        group_f_champ, group_f_runner_up, group_f_third = group_f_standings[:3]
        print(Fore.GREEN + "PRE-QUALIFYING, GROUP G: " + Fore.RESET, end='')
        group_g_standings = round_robin(group_g, r=20, qualify_range=len(group_a), print_region_seed=True, cyan_seeds=[0,1,2], red_seeds=[3,4])
        group_g_champ, group_g_runner_up, group_g_third = group_g_standings[:3]
        print(Fore.GREEN + "PRE-QUALIFYING, GROUP H: " + Fore.RESET, end='')
        group_h_standings = round_robin(group_h, r=20, qualify_range=len(group_a), print_region_seed=True, cyan_seeds=[0,1,2], red_seeds=[3,4])
        group_h_champ, group_h_runner_up, group_h_third = group_h_standings[:3]

        i = 0
        for champ1 in [group_a_champ, group_b_champ, group_c_champ, group_d_champ]:
            index = ["A", "B", "C", "D"]
            uni_qualif_g1.append(champ1)
            champ1.history[season_count] += f" Won PQ Group {index[i]} -> UNI Qualifying."
            i+=1
        i = 0
        for champ2 in [group_e_champ, group_f_champ, group_g_champ, group_h_champ]:
            index = ["E", "F", "G", "H"]
            uni_qualif_g2.append(champ2)
            champ2.history[season_count] += f" Won PQ Group {index[i]} -> UNI Qualifying."
            i += 1
        i = 0
        for runner_up1 in [group_e_runner_up, group_f_runner_up, group_g_runner_up, group_h_runner_up]:
            index = ["E", "F", "G", "H"]
            uni_qualif_g1.append(runner_up1)
            runner_up1.history[season_count] += f" 2nd in PQ Group {index[i]} -> UNI Qualifying."
        i = 0
        for runner_up2 in [group_a_runner_up, group_b_runner_up, group_c_runner_up, group_d_runner_up]:
            index = ["A", "B", "C", "D"]
            uni_qualif_g2.append(runner_up2)
            runner_up2.history[season_count] += f" 2nd in PQ Group {index[i]} -> UNI Qualifying."

        i = 0
        for third1 in [group_e_third, group_b_third, group_g_third, group_d_third]:
            index = ["E", "B", "G", "D"]
            uni_qualif_g1.append(third1)
            third1.history[season_count] += f" 3rd in PQ Group {index[i]} -> UNI Qualifying."
        i = 0
        for third2 in [group_a_third, group_f_third, group_c_third, group_h_third]:
            index = ["A", "F", "C", "H"]
            uni_qualif_g2.append(third2)
            third2.history[season_count] += f" 3rd in PQ Group {index[i]} -> UNI Qualifying."

        for i in [3,4]:
            group_a_standings[i].history[season_count] += f" Eliminated from PQ ({ordinal_string(i+1)} in Group A)"
            group_b_standings[i].history[season_count] += f" Eliminated from PQ ({ordinal_string(i+1)} in Group B)"
            group_c_standings[i].history[season_count] += f" Eliminated from PQ ({ordinal_string(i+1)} in Group C)"
            group_d_standings[i].history[season_count] += f" Eliminated from PQ ({ordinal_string(i+1)} in Group D)"
            group_e_standings[i].history[season_count] += f" Eliminated from PQ ({ordinal_string(i+1)} in Group E)"
            group_f_standings[i].history[season_count] += f" Eliminated from PQ ({ordinal_string(i+1)} in Group F)"
            group_g_standings[i].history[season_count] += f" Eliminated from PQ ({ordinal_string(i + 1)} in Group G)"
            group_h_standings[i].history[season_count] += f" Eliminated from PQ ({ordinal_string(i + 1)} in Group H)"



        if len(upl_standings) < 30:
            drop_range1 = [0, 2, 5]
            drop_range2 = [1, 3, 4]
        else:
            drop_range1 = [0, 2, 5, 6, 9, 11, 12,14]
            drop_range2 = [1, 3, 4, 7, 8, 10, 13,15]

        for i in drop_range1:
            uni_qualif_g1.append(upl_standings[i])
            uni_teams.remove(upl_standings[i])
            relegated[season_count].append(upl_standings[i])

        for i in drop_range2:
            uni_qualif_g2.append(upl_standings[i])
            uni_teams.remove(upl_standings[i])
            relegated[season_count].append(upl_standings[i])

        for team in uni_qualif_g1:
            team.accolades['Universal-Qualifying'] += 1
        for team in uni_qualif_g2:
            team.accolades['Universal-Qualifying'] += 1

        uni_qualif_start_time = time.time()

        for i in range(8):
            if i % 2 == 0:
                uni_qualif_g1.append(regional_champs[i])
            elif i % 2 == 1:
                uni_qualif_g2.append(regional_champs[i])
        for group in [uni_qualif_g1, uni_qualif_g2]:
            season_wipe(group)

        print(Fore.GREEN + "GROUP 1 QUALIFYING ROUND, " + Fore.RESET, end='')
        g1_pre_advance = round_robin(uni_qualif_g1, 8, len(uni_qualif_g1), franchise_mode=True, cyan_seeds=[0,1,2,3,4,5], yellow_seeds=[6,7,8,9,10,11], red_seeds=[r for r in range(12,len(uni_qualif_g1))])
        print(Fore.GREEN + "GROUP 2 QUALIFYING ROUND, " + Fore.RESET, end='')
        g2_pre_advance = round_robin(uni_qualif_g2, 8, len(uni_qualif_g2), franchise_mode=True, cyan_seeds=[0,1,2,3,4,5], yellow_seeds=[6,7,8,9,10,11], red_seeds=[r for r in range(12,len(uni_qualif_g2))])
        uni_teams.reverse()
        g1_advance = [None for _ in range(24)]
        g2_advance = [None for _ in range(24)]

        void_draft = []

        for i in range(6): #seeds 1 through 6 who clinch universal league
            g1_advance[i] = g1_pre_advance[i]
            uni_teams.append(g1_advance[i])
            g1_pre_advance[i].history[season_count] += f" {ordinal_string(i+1)} in Group 1 Qualifying. -> UNI League."

            g2_advance[i] = g2_pre_advance[i]
            uni_teams.append(g2_advance[i])
            g2_pre_advance[i].history[season_count] += f" {ordinal_string(i+1)} in Group 2 Qualifying. -> UNI League."
        for i in [6,7,8,9]: #7, 8, 9, 10, seeds going to play-in
            g1_advance[i] = g1_pre_advance[i]
            g1_pre_advance[i].qualifying_group = 1
            g1_pre_advance[i].history[season_count] += f" {ordinal_string(i + 1)} in Group 1 Qualifying. -> Universal Play-In. "

            g2_advance[i] = g2_pre_advance[i]
            g2_pre_advance[i].qualifying_group = 2
            g2_pre_advance[i].history[season_count] += f" {ordinal_string(i + 1)} in Group 2 Qualifying. -> Universal Play-In. "
        for i in range(10,len(g1_pre_advance)): #11 seed and below eliminated
            void_draft.append(g1_pre_advance[i])
            void_draft.append(g2_pre_advance[i])

            g1_pre_advance[i].history[season_count] += f" {ordinal_string(i+1)} in Group 1 Qualifying. Failed to qualify."
            g2_pre_advance[i].history[season_count] += f" {ordinal_string(i+1)} in Group 2 Qualifying. Failed to qualify."

            g1_pre_advance[i].second_pick = 3 #1 in 3 chance for second round pick
            g2_pre_advance[i].second_pick = 3


        for i in range(6):
            if g1_advance[i] in relegated[season_count]:
                relegated[season_count].remove(g1_advance[i])
            else:
                promoted[season_count].append(g1_advance[i])
            if g2_advance[i] in relegated[season_count]:
                relegated[season_count].remove(g2_advance[i])
            else:
                promoted[season_count].append(g2_advance[i])

        uni_qualif_end_time = time.time()

        with open('execution_time', 'a') as file:
            file.write(f"Season {season_count} Universal Qualifying Group Stage Execution Time: {round((uni_qualif_end_time - uni_qualif_start_time) / 60)} minutes, {round(((uni_qualif_end_time - uni_qualif_start_time) % 60), 2)} seconds.\n")

        uni_play_in_start_time = time.time()

        #UNIVERSAL PLAY IN
        advanced_play_in = []
        elim_play_in = []

        print(Fore.BLUE + "(Game 1) Group 1 no. 7 vs Group 2 no. 10, winner advances, loser eliminated")
        upi_g1W, upi_g1L = best_of(g1_advance[6], g2_advance[9],
                                   thresh=180, win_by=25,
                                   both_return=True, upset_list=upset_list, upset_count=upset_count,
                                   context=f"S{season_count} Universal Play-In Game 1",advantage=6)
        advanced_play_in.append(upi_g1W)
        elim_play_in.append(upi_g1L)
        print(Fore.GREEN + f"{upi_g1W.name} advance\n{upi_g1L.name} eliminated" + Fore.RESET)

        print(Fore.BLUE + "(Game 2) Group 2 no. 7 vs Group 1 no. 10, winner advances, loser eliminated")
        upi_g2W, upi_g2L = best_of(g2_advance[6], g1_advance[9],
                                   thresh=180, win_by=25,
                                   both_return=True, upset_list=upset_list, upset_count=upset_count,
                                   context=f"S{season_count} Universal Play-In Game 1",advantage=6)
        advanced_play_in.append(upi_g2W)
        elim_play_in.append(upi_g2L)
        print(Fore.GREEN + f"{upi_g2W.name} advance\n{upi_g2L.name} eliminated" + Fore.RESET)

        print(Fore.BLUE + "(Game 3) Group 1 no. 8 vs Group 2 no. 9, winner advances, loser eliminated")
        upi_g3W, upi_g3L = best_of(g1_advance[7], g2_advance[8],
                                   thresh=180, win_by=25,
                                   both_return=True, upset_list=upset_list, upset_count=upset_count,
                                   context=f"S{season_count} Universal Play-In Game 1",advantage=3)
        advanced_play_in.append(upi_g3W)
        elim_play_in.append(upi_g3L)
        print(Fore.GREEN + f"{upi_g3W.name} advance\n{upi_g3L.name} eliminated" + Fore.RESET)

        print(Fore.BLUE + "(Game 4) Group 2 no. 8 vs Group 1 no. 9, winner advances, loser eliminated")
        upi_g4W, upi_g4L = best_of(g2_advance[7], g1_advance[8],
                                   thresh=180, win_by=25,
                                   both_return=True, upset_list=upset_list, upset_count=upset_count,
                                   context=f"S{season_count} Universal Play-In Game 1",advantage=3)
        advanced_play_in.append(upi_g4W)
        elim_play_in.append(upi_g4L)
        print(Fore.GREEN + f"{upi_g4W.name} advance\n{upi_g4L.name} eliminated" + Fore.RESET)

        print(Fore.RED + "***END OF UNIVERSAL QUALIFYING***" + Fore.RESET)



        uni_play_in_end_time = time.time()
        with open('execution_time', 'a') as file:
            file.write(f"Season {season_count} Universal Play-In Execution Time: {round((uni_play_in_end_time - uni_play_in_start_time) / 60)} minutes, {round(((uni_play_in_end_time - uni_play_in_start_time) % 60), 2)} seconds.\n")


        advanced_play_in = list(set(advanced_play_in))

        time.sleep(3)


        for team in advanced_play_in:
            uni_teams.append(team)
            if team in relegated[season_count]:
                relegated[season_count].remove(team)
            else:
                promoted[season_count].append(team)
            team.history[season_count] += "Advanced from Universal Play-In -> UNI League. "
        for team in elim_play_in:
            team.history[season_count] += "Failed to advance from Universal Play-In. "
            void_draft.append(team)
            team.second_pick = 2 #2 in 3 chance for second round pick

        season_wipe(uni_teams)
        uni_teams = list(set(uni_teams))
        upl_standings = league_season(uni_teams, use_saved=False, season_count=season_count, stats_list=uni_stats_list,upset_list=upset_list,upset_count=upset_count, region="Universal",franchise_mode=franchise_mode)

        for team in promoted[season_count]:
            print(f"{team.name} PROMOTED.")
            team.history[season_count] += "\n\tPROMOTED to Universal League."
        for team in relegated[season_count]:
            print(f"{team.name} RELEGATED.")
            team.history[season_count] += "\n\tRELEGATED to "

        clear_file('history')
        clear_file('my_teams')
        clear_file('best_stats')

        reverse_upl_standings = list(reversed(upl_standings))



        #to make MVP specific to regional regular season stats, DO NOT run the season_stats function on each region
        #instead, the stats will be generated in the league_season function following the regular season,
        #and the MVP can be determined by running those stats through the region_mvp function


        get_upsets(upset_list, upset_count)

        second_draft_g1 = []
        second_draft_g2 = []
        second_draft_g3 = []

        third_draft_full = []

        #todo currently, pre-qualifying teams are being given second round picks in a way other than being added to g3
        #every srg3 team is getting an extra second round draft pick, meaning it's being granted to them after failing
        #to qualify for the universal qualifying round
        for league in [dw_teams, sc_teams, ds_teams, wof_teams, iw_teams, cl_teams, hc_teams, sh_teams]:
            for team in league:
                if team not in uni_teams:
                    all_teams.append(team)
                if team.second_pick == 1:
                    second_draft_g1.append(team)
                elif team.second_pick == 2:
                    coin = choice([True, True, False])
                    if coin:
                        team.history[season_count] += "\n\t2 in 3 chance for Second Round pick: SUCCESS"
                        second_draft_g2.append(team)
                    else:
                        team.history[season_count] += "\n\t2 in 3 chance for Second Round pick: FAILURE"
                elif team.second_pick == 3:
                    coin = choice([True, False, False])
                    if coin:
                        team.history[season_count] += "\n\t1 in 3 chance for Second Round pick: SUCCESS"
                        second_draft_g3.append(team)
                    else:
                        team.history[season_count] += "\n\t1 in 3 chance for Second Round pick: FAILURE"
                team.second_pick = 0
                if team.third_pick == 1:
                    third_draft_full.append(team)
                    team.third_pick = 0

        for team in uni_teams:
            all_teams.append(team)
            if team.second_pick == 1 and team not in second_draft_g1:
                second_draft_g1.append(team)
            elif team.second_pick == 2 and team not in second_draft_g2:
                coin = choice([True, True, False])
                if coin:
                    team.history[season_count] += "\n\t2 in 3 chance for Second Round pick: SUCCESS"
                    second_draft_g2.append(team)
                else:
                    team.history[season_count] += "\n\t2 in 3 chance for Second Round pick: FAILURE"
            elif team.second_pick == 3 and team not in second_draft_g3:
                coin = choice([True, False, False])
                if coin:
                    team.history[season_count] += "\n\t1 in 3 chance for Second Round pick: SUCCESS"
                    second_draft_g3.append(team)
                else:
                    team.history[season_count] += "\n\t1 in 3 chance for Second Round pick: FAILURE"
            if team.third_pick == 1 and team not in third_draft_full:
                third_draft_full.append(team)
                team.third_pick = 0


        shuffle(second_draft_g1)
        shuffle(second_draft_g2)
        shuffle(second_draft_g3)
        second_draft_full = second_draft_g1 + second_draft_g2 + second_draft_g3

        #season_stats_list[season_count] = season_stats(all_teams, season_count, season_stats_list)
        #print(Fore.CYAN + f"season_stats_list[season_count] contains {len(season_stats_list[season_count])} season objects.")
        #best_of_stats(season_stats_list[season_count], season_count)
        sort_champions_by_seed()

        #REMINDER: season_stats_list is a DICTIONARY with integer keys for the season number, and the values are a LIST OF PLAYER SEASONS


        if True:
            all_players = []

            labyrinth_mine = 1 #I've set it equal to 1 so that I only get one Labyrinth team now
            for league in [dw_teams, sc_teams, ds_teams, wof_teams, iw_teams, cl_teams, hc_teams, sh_teams]:
                league.reverse()
            for team in uni_teams:
                if team in dw_teams:
                    dw_teams.remove(team)
                    if relegated[season_count]:
                        add = choice(relegated[season_count])
                        relegated[season_count].remove(add)
                        dw_teams.append(add)
                        add.history[season_count] += "Darkwing Regional."
                    else:
                        add = Team('Labyrinth',season_count=season_count)
                        add.history[season_count] = "Introduced into the Darkwing Regional."
                        dw_teams.insert(0, add)
                        if labyrinth_mine <= 1:
                            add.make_mine(add.name)
                            labyrinth_mine += 1
                elif team in sc_teams:
                    sc_teams.remove(team)
                    if relegated[season_count]:
                        add = choice(relegated[season_count])
                        relegated[season_count].remove(add)
                        sc_teams.append(add)
                        add.history[season_count] += "Shining-Core Regional."
                    else:
                        add = Team('Labyrinth',season_count=season_count)
                        add.history[season_count] = "Introduced into the Shining-Core Regional."
                        sc_teams.insert(0, add)
                        if labyrinth_mine <= 1:
                            add.make_mine(add.name)
                            labyrinth_mine += 1
                elif team in ds_teams:
                    ds_teams.remove(team)
                    if relegated[season_count]:
                        add = choice(relegated[season_count])
                        relegated[season_count].remove(add)
                        ds_teams.append(add)
                        add.history[season_count] += "Diamond-Sea Regional."
                    else:
                        add = Team('Labyrinth',season_count=season_count)
                        add.history[season_count] = "Introduced into the Diamond-Sea Regional."
                        ds_teams.insert(0, add)
                        if labyrinth_mine <= 1:
                            add.make_mine(add.name)
                            labyrinth_mine += 1
                elif team in wof_teams:
                    wof_teams.remove(team)
                    if relegated[season_count]:
                        add = choice(relegated[season_count])
                        relegated[season_count].remove(add)
                        wof_teams.append(add)
                        add.history[season_count] += "Web-of-Nations Regional."
                    else:
                        add = Team('Labyrinth',season_count=season_count)
                        add.history[season_count] = "Introduced into the Web-of-Nations Regional."
                        wof_teams.insert(0, add)
                        if labyrinth_mine <= 1:
                            add.make_mine(add.name)
                            labyrinth_mine += 1
                elif team in iw_teams:
                    iw_teams.remove(team)
                    if relegated[season_count]:
                        add = choice(relegated[season_count])
                        relegated[season_count].remove(add)
                        iw_teams.append(add)
                        add.history[season_count] += "Ice-Wall Regional."
                    else:
                        add = Team('Labyrinth',season_count=season_count)
                        add.history[season_count] = "Introduced into the Ice-Wall Regional."
                        iw_teams.insert(0, add)
                        if labyrinth_mine <= 1:
                            add.make_mine(add.name)
                            labyrinth_mine += 1
                elif team in cl_teams:
                    cl_teams.remove(team)
                    if relegated[season_count]:
                        add = choice(relegated[season_count])
                        relegated[season_count].remove(add)
                        cl_teams.append(add)
                        add.history[season_count] += "Candyland Regional."
                    else:
                        add = Team('Labyrinth',season_count=season_count)
                        add.history[season_count] = "Introduced into the Candyland Regional."
                        cl_teams.insert(0, add)
                        if labyrinth_mine <= 1:
                            add.make_mine(add.name)
                            labyrinth_mine += 1
                elif team in hc_teams:
                    hc_teams.remove(team)
                    if relegated[season_count]:
                        add = choice(relegated[season_count])
                        relegated[season_count].remove(add)
                        hc_teams.append(add)
                        add.history[season_count] += "Hell's-Circle Regional."
                    else:
                        add = Team('Labyrinth',season_count=season_count)
                        add.history[season_count] = "Introduced into the Hell's-Circle Regional."
                        hc_teams.insert(0, add)
                        if labyrinth_mine <= 1:
                            add.make_mine(add.name)
                            labyrinth_mine += 1
                elif team in sh_teams:
                    sh_teams.remove(team)
                    if relegated[season_count]:
                        add = choice(relegated[season_count])
                        relegated[season_count].remove(add)
                        sh_teams.append(add)
                        add.history[season_count] += "Steel-Heart Regional."
                    else:
                        add = Team('Labyrinth',season_count=season_count)
                        add.history[season_count] = "Introduced into the Steel-Heart Regional."
                        sh_teams.insert(0, add)
                        if labyrinth_mine <= 1:
                            add.make_mine(add.name)
                            labyrinth_mine += 1


            with open("rosters", 'w') as l:
                l.write('')

            write_rosters = True

            total_stats = {'Power' : 0, 'Attack Damage' : 0, 'Attack Speed' : 0, 'Critical %' : 0, 'Critical X' : 0, 'Spawn Time' : 0, 'Health' : 0, 'Age' : 0}
            if write_rosters:
                with open("rosters", 'a') as w:
                    w.write(f"SEASON NO. {season_count}\n")
                    trans_region = ['Universal', 'Darkwing', 'Shining-Core', 'Diamond-Sea', 'Web-of-Nations', 'Ice-Wall', 'Candyland', "Hell's-Circle", 'Steel-Heart']
                    trans_i = -1
                    for league in [uni_teams, dw_teams, sc_teams, ds_teams, wof_teams, iw_teams, cl_teams, hc_teams, sh_teams]:
                        trans_i +=1
                        for team in league:
                            team.region = trans_region[trans_i]
                            for player in team.players:
                                total_stats['Power'] += player.power
                                total_stats['Attack Damage'] += player.atk_dmg
                                total_stats['Attack Speed'] += player.atk_spd
                                total_stats['Critical %'] += player.crit_pct
                                total_stats['Critical X'] += player.crit_x
                                total_stats['Spawn Time'] += player.spawn_time
                                total_stats['Health'] += player.max_health
                                total_stats['Age'] += player.age

                                all_players.append(player)
                    grade_players(all_players,is_team=True)




                    for key in total_stats.keys():
                        w.write(f"Average {key}: {total_stats[key]/len(all_players):.4f}\n")
                    w.write('\n')
                    for player in all_players:
                        w.write(f"{str(player)}\n")

            #note: reverse_upl_standings is the correct order from 1st to 36th

            other_all_teams = []
            for league in [uni_teams, dw_teams, sc_teams, ds_teams, wof_teams, iw_teams, cl_teams, hc_teams, sh_teams]:
                other_all_teams.extend(league)

            player_changes(other_all_teams, season_count=season_count)

            for team in reverse_upl_standings[20:]:
                void_draft.append(team)
                third_draft_full.append(team)

            void_draft.reverse()

            dw_draft = [team for team in dw_teams if team not in void_draft]
            sc_draft = [team for team in sc_teams if team not in void_draft]
            ds_draft = [team for team in ds_teams if team not in void_draft]
            wof_draft = [team for team in wof_teams if team not in void_draft]
            iw_draft = [team for team in iw_teams if team not in void_draft]
            cl_draft = [team for team in cl_teams if team not in void_draft]
            hc_draft = [team for team in hc_teams if team not in void_draft]
            sh_draft = [team for team in sh_teams if team not in void_draft]


            user_draft(dw_draft, season_count, is_regional=True, draft_name="Darkwing Regional draft", league_season_stats=dw_stats_list)
            user_draft(sc_draft, season_count, is_regional=True, draft_name="Shining-Core Regional draft", league_season_stats=sc_stats_list)
            user_draft(ds_draft, season_count, is_regional=True, draft_name="Diamond-Sea Regional draft", league_season_stats=ds_stats_list)
            user_draft(wof_draft, season_count, is_regional=True, draft_name="Web-of-Nations Regional draft", league_season_stats=wof_stats_list)
            user_draft(iw_draft, season_count,  is_regional=True, draft_name="Ice-Wall Regional draft", league_season_stats=iw_stats_list)
            user_draft(cl_draft, season_count, is_regional=True, draft_name="Candyland Regional draft", league_season_stats=cl_stats_list)
            user_draft(hc_draft, season_count,  is_regional=True, draft_name="Hell's-Circle Regional draft", league_season_stats=hc_stats_list)
            user_draft(sh_draft, season_count, is_regional=True, draft_name="Steel-Heart Regional draft", league_season_stats=sh_stats_list)

            user_draft(second_draft_full, season_count, second=True, draft_name="Secondary draft") #1 in 3 for eliminated in Universal Qualifying Group Stage
                                                                                                   #2 in 3 for eliminated Universal play-in
                                                                                                   #approx. 1 in 2 chance for regional missed playoffs
            shuffle(third_draft_full)
            user_draft(third_draft_full, season_count, third=True, draft_name="Tertiary draft") #Universal teams relegated to qualifying + 1/10 chance for regional missed playoffs

            upl_draft = reverse_upl_standings[0:20]
            upl_draft.reverse()
            #This takes the top 20 from the UPL (those NOT on the chopping block) and reverses them


            #This takes the 16 teams which were eliminated and puts the draft in order from worst to best by reversing
            #void draft includes all teams which failed to qualify from universal qualifying, as well as all teams on the universal chopping block
            upl_draft = remove_duplicates_ordered(upl_draft)


            user_draft(upl_draft, season_count, draft_name='Universal-Draft', league_season_stats=season_stats_list,write_draft=True)
            user_draft(void_draft, season_count, void=True, draft_name='Void-Draft')

            slasher_count = undead_count = reflector_count = clutch_count = inc_count = pp_count = total_player_count = exploder_count = splitter_count = vampire_count = toxic_count = healer_count = flasher_count =  normal_player_count = 0
            coach_lineup_mod_count = {'NC' : 0, '1C' : 0, '2C' : 0, '3C' : 0, '4C' : 0, '5C' : 0, 'Error' : 0}
            coach_slots_amped_count = {
                (0,) : 0, (1,) : 0, (2,) : 0, (3,) : 0, (4,) : 0, (5,) : 0,
                (0, 5) : 0, (1, 4) : 0, (2, 3) : 0, (3, 5) : 0, (3, 4) : 0, (0, 4) : 0, (1, 3) : 0, (2, 5) : 0,
                (0, 4, 5) : 0, (1, 4, 5) : 0, (1, 3, 5) : 0, (2, 3, 4) : 0, (2, 3, 5) : 0, (3, 4, 5) : 0, (2,4,5) : 0
            }
            coach_attribute_amped_count = {"Power" : [0,0], "Attack Damage" : [0,0], "Critical Chance" : [0,0]} #list values: [count of coaches whom affect this trait, total multiplier value]
            coach_trait_amped_count = {'Pp' : [0,0], 'R#' : [0,0], 'C%' : [0,0], 'I*' : [0,0], 'U-' : [0,0], 'X+' : [0,0], 'Hn' : [0,0], 'Tx' : [0,0]}
            total_team_count = 0
            slasher_list = []
            undead_list = []
            reflector_list = []
            clutch_list = []
            inc_list = []
            pp_list = []
            exploder_list = []
            splitter_list = []
            vampire_list = []
            toxic_list = []
            healer_list = []
            flasher_list = []
            all_teams_lists = [uni_teams, dw_teams, sc_teams, ds_teams, wof_teams, iw_teams, cl_teams, hc_teams, sh_teams]

            def percent_within_thresholds(numbers, lim, std_dev):
                thresholds = [100, 250, 500, 1000, std_dev, round(lim/2)]
                total = len(numbers)

                results = {
                    thresh: round((100 * sum((lim - x <= thresh and lim-x > 0) for x in list(numbers)) / total),2)
                    for thresh in thresholds
                }

                return results

            xwar_array = np.array([team.get_team_xWAR() for team_list in all_teams_lists for team in team_list])
            xwar_std = xwar_array.std()
            xwar_mean = xwar_array.mean()
            cap = caps[season_count]
            above_cap = xwar_array[xwar_array > cap]
            below_cap = xwar_array[xwar_array <= cap]
            avg_diff_below_cap = below_cap.mean() - cap
            avg_diff_above_cap = above_cap.mean() - cap
            with open('history', 'w') as history:
                history.write(f"Average Team xWAR: {xwar_array.mean()}, xWAR Cap: {cap}\n")
            cap_mode = 'a' if season_count > 1 else 'w'
            with open('salary-cap-calculator', cap_mode) as cap_file:
                cap_file.write(f"S{season_count} Average Team xWAR: {xwar_mean} (Per Player: {xwar_mean/6})\nxWAR Cap: {cap}\nStd Dev: {xwar_std}\nAverage Diff Below Cap: {avg_diff_below_cap}\nAverage Diff Above Cap: {avg_diff_above_cap}\n")
                pct_thresh = percent_within_thresholds(xwar_array, cap, xwar_std)
                cap_file.write(f"% of teams OVER the cap: {round((100 * sum(x > cap for x in list(xwar_array)) / len(xwar_array)), 2)}\n")
                cap_file.write(f"% of teams UNDER the cap: {round((100 * sum(cap > x for x in list(xwar_array)) / len(xwar_array)), 2)}\n")
                for thresh in pct_thresh.keys():
                    if thresh%50==0:
                        cap_file.write(f"% of teams within {thresh} xWAR of cap: {pct_thresh[thresh]}\n")
                    elif thresh == round(cap/2):
                        cap_file.write(f"% of teams over 1/2 cap value: {pct_thresh[thresh]}\n\n")
                    else:
                        cap_file.write(f"% of teams within one standard deviation of cap: {pct_thresh[thresh]}\n")

            for league in [uni_teams, dw_teams, sc_teams, ds_teams, wof_teams, iw_teams, cl_teams, hc_teams,
                           sh_teams]:
                for team in league:
                    total_team_count += 1
                    coach_slots_amped_count[tuple(team.team_coach.slot_effect[0])] += 1
                    coach_attribute_amped_count[team.team_coach.slot_effect[1]][0] += 1
                    coach_attribute_amped_count[team.team_coach.slot_effect[1]][1] += team.team_coach.slot_effect[2]
                    coach_trait_amped_count[team.team_coach.trait_effect[0]][0] += 1
                    coach_trait_amped_count[team.team_coach.trait_effect[0]][1] += team.team_coach.trait_effect[1]

                    if team.team_coach.lineup_modifier in ['NC', '1C', '2C', '3C', '4C', '5C']:
                        coach_lineup_mod_count[team.team_coach.lineup_modifier] += 1
                    else:
                        coach_lineup_mod_count['Error'] += 1
                    for idk in team.players:
                        total_player_count += 1
                        if idk.trait_tag == '$l':
                            slasher_count += 1
                            slasher_list.append(idk)
                        elif idk.trait_tag == 'U-':
                            undead_count += 1
                            undead_list.append(idk)
                        elif idk.trait_tag == 'R#':
                            reflector_count += 1
                            reflector_list.append(idk)
                        elif idk.trait_tag == 'C%':
                            clutch_count += 1
                            clutch_list.append(idk)
                        elif idk.trait_tag == 'I*':
                            inc_count += 1
                            inc_list.append(idk)
                        elif idk.trait_tag == 'Pp':
                            pp_count += 1
                            pp_list.append(idk)
                        elif idk.trait_tag == 'X+':
                            exploder_count += 1
                            exploder_list.append(idk)
                        elif idk.trait_tag == 'Sp':
                            splitter_count += 1
                            splitter_list.append(idk)
                        elif idk.trait_tag == 'V.':
                            vampire_count += 1
                            vampire_list.append(idk)
                        elif idk.trait_tag == 'Tx':
                            toxic_count += 1
                            toxic_list.append(idk)
                        elif idk.trait_tag == 'Hn':
                            healer_count += 1
                            healer_list.append(idk)
                        elif idk.trait_tag == 'Fl':
                            flasher_count += 1
                            flasher_list.append(idk)
                        normal_player_count += 1 if idk.trait_tag == 'None' else 0

                    team.print_team_name(season_count)
                    team.print_accolades()
                    team.print_history(season_count)
                    if team.mine:
                        print("\n" + Fore.RED + f"{team.name}\n" + Fore.BLUE + team.history[season_count] + Fore.RESET)

            with open('team_coach_data', 'a') as file:
                file.write(f"--Lineup Modifiers--\n")
                file.write(
                    f"NC: {coach_lineup_mod_count['NC']} ({round((100 * coach_lineup_mod_count['NC'] / total_team_count), 2)}%)\n")
                file.write(
                    f"1C: {coach_lineup_mod_count['1C']} ({round((100 * coach_lineup_mod_count['1C'] / total_team_count), 2)}%)\n")
                file.write(
                    f"2C: {coach_lineup_mod_count['2C']} ({round((100 * coach_lineup_mod_count['2C'] / total_team_count), 2)}%)\n")
                file.write(
                    f"3C: {coach_lineup_mod_count['3C']} ({round((100 * coach_lineup_mod_count['3C'] / total_team_count), 2)}%)\n")
                file.write(
                    f"4C: {coach_lineup_mod_count['4C']} ({round((100 * coach_lineup_mod_count['4C'] / total_team_count), 2)}%)\n")
                file.write(
                    f"5C: {coach_lineup_mod_count['5C']} ({round((100 * coach_lineup_mod_count['5C'] / total_team_count), 2)}%)\n"
                    f"--Slots Amplified--\n")

                for amped_slots in [(0,), (1,), (2,), (3,), (4,), (5,),
                (0, 5), (1, 4), (2, 3), (3, 5), (3, 4), (0, 4), (1, 3), (2, 5),
                (0, 4, 5), (1, 4, 5), (1, 3, 5), (2, 3, 4), (2, 3, 5), (3, 4, 5), (2,4,5)]:
                    file.write(f"{list(amped_slots)}: {coach_slots_amped_count[amped_slots]} "
                               f"({round((100 * coach_slots_amped_count[amped_slots] / total_team_count), 2)}%)\n")
                file.write(f"--Attributes Affected--\n"
                           f"""Power: {coach_attribute_amped_count["Power"][0]} """
                           f"""({round((100 * coach_attribute_amped_count["Power"][0] / total_team_count), 2)}%)\n"""
                           f"""\tAverage Amp: {round((coach_attribute_amped_count["Power"][1] / coach_attribute_amped_count["Power"][0]), 2)}\n"""
                           f"""Attack Damage: {coach_attribute_amped_count["Attack Damage"][0]} """
                           f"""({round((100 * coach_attribute_amped_count["Attack Damage"][0] / total_team_count), 2)}%)\n"""
                           f"""\tAverage Amp: {round((coach_attribute_amped_count["Attack Damage"][1] / coach_attribute_amped_count["Attack Damage"][0]), 2)}\n"""
                           f"""Critical Chance: {coach_attribute_amped_count["Critical Chance"][0]} """
                           f"""({round((100 * coach_attribute_amped_count["Critical Chance"][0] / total_team_count), 2)}%)\n"""
                           f"""\tAverage Amp: {round((coach_attribute_amped_count["Critical Chance"][1] / coach_attribute_amped_count["Critical Chance"][0]), 2)}\n""")
                file.write("--Traits Affected--\n")
                for trait in ['Pp', 'R#', 'C%', 'I*', 'U-', 'X+']:
                    file.write(f"""{trait}: {coach_trait_amped_count[trait][0]} """
                               f"""({round((100 * coach_trait_amped_count[trait][0] / total_team_count), 2)}%)\n"""
                               f"""\tAverage Amp: ({round((coach_trait_amped_count[trait][1] / total_team_count), 2)})\n""")





            with open('player_trait_data','a') as file:
                file.write(f"Season No. {season_count}, Total Players: {total_player_count}\n")

                if len(slasher_list) > 0:
                    file.write(f"Slashers: {slasher_count} ({round((100*slasher_count/total_player_count),2)}%)\n")
                    file.write(f"\tAverage Instant Kill %: {round(mean([100*player.insta_kill_pct for player in slasher_list]),3)}\n")

                if len(undead_list) > 0:
                    file.write(f"Undead: {undead_count} ({round((100*undead_count/total_player_count),2)}%)\n")
                    file.write(f"\tAverage Revive Chance: {round(mean([100*player.trait_multiplier for player in undead_list]),3)}%\n")
                    file.write(f"\tAverage Health on Revive: {round(mean([200 * player.trait_multiplier for player in undead_list]), 3)}%\n")

                if len(reflector_list) > 0:
                    file.write(f"Reflectors: {reflector_count} ({round((100*reflector_count/total_player_count),2)}%)\n")
                    file.write(f"\tAverage Reflect Chance: {round(mean([100*player.trait_multiplier for player in reflector_list]), 3)}%\n")

                if len(clutch_list) > 0:
                    file.write(f"Clutch Players: {clutch_count} ({round((100*clutch_count/total_player_count),2)}%)\n")
                    file.write(f"\tAverage Clutch Multiplier: {round(mean([player.trait_multiplier for player in clutch_list]), 3)}x Attack Damage and Power in Clutch-Time\n")

                if len(inc_list) > 0:
                    file.write(f"Inconsistent Players: {inc_count} ({round((100*inc_count/total_player_count),2)}%)\n")
                    file.write(f"\tAverage Inconsistent Multiplier: {round(mean([200*player.trait_multiplier for player in inc_list]), 2)}% chance for abnormal stats\n")

                if len(pp_list) > 0:
                    file.write(f"Playoff Performers: {pp_count} ({round((100*pp_count/total_player_count),2)}%)\n")
                    file.write(f"\tAverage Playoff Performer Multiplier: {round(mean([100*player.trait_multiplier for player in pp_list]), 2)}% chance to add extra +4 Power in Playoff games.\n")

                if len(exploder_list) > 0:
                    file.write(f"Exploders: {exploder_count} ({round((100*exploder_count / total_player_count), 2)}%)\n")
                    file.write(f"\tAverage Explosion Damage: {round(mean([player.trait_multiplier[0]*player.atk_dmg for player in exploder_list]), 2)} to ALL enemies upon death.\n")

                if len(splitter_list) > 0:
                    file.write(f"Splitters: {splitter_count} ({round((100 * splitter_count / total_player_count), 2)}%)\n")
                    file.write(
                        f"\tAverage Splitter Multiplier: {round(mean([100 * player.trait_multiplier for player in splitter_list]), 2)}% chance to attack a second time.\n")

                if len(vampire_list) > 0:
                    file.write(f"Vampires: {vampire_count} ({round((100 * vampire_count / total_player_count), 2)}%)\n")
                    file.write(
                        f"\tAverage Vampire Multiplier: {round(mean([100 * player.trait_multiplier for player in vampire_list]), 2)}% chance to self-heal for between 1/2 and 4/5 of dealt attack damage.\n")

                if len(toxic_list) > 0:
                    file.write(f"Toxic Players: {toxic_count} ({round((100 * toxic_count / total_player_count), 2)}%)\n")
                    file.write(
                        f"\tAverage Toxic Multiplier: {round(mean([100 * player.trait_multiplier[0] for player in toxic_list]), 2)}% chance to inflict {round(mean([player.trait_multiplier[1][1] for player in toxic_list]), 1)} toxin damage for {round(mean([player.trait_multiplier[1][0] for player in toxic_list]), 1)} ticks.\n")

                if len(flasher_list) > 0:
                    file.write(f"Flashers: {flasher_count} ({round((100 * flasher_count / total_player_count), 2)}%)\n")
                    file.write(
                        f"\tAverage Flasher Multiplier: {round(mean([100 * player.trait_multiplier[0] for player in flasher_list]), 2)}% chance to inflict stun for {round(mean([player.trait_multiplier[1] for player in flasher_list]), 1)} ticks.\n")

                if len(healer_list) > 0:
                    file.write(f"Healers: {healer_count} ({round((100 * healer_count / total_player_count), 2)}%)\n")
                    file.write(
                        f"\tAverage Healer Multiplier: Heal for {round(mean([player.trait_multiplier[1] for player in healer_list]), 2)} every {round(mean([player.trait_multiplier[0] for player in healer_list]), 2)} ticks.\n")

                file.write(f"Normal Players (no traits): {normal_player_count} ({round((100*normal_player_count / total_player_count), 2)}%)\n\n")
            finalize_series_data()
            system = [upl_standings,dw_teams,sc_teams,ds_teams,wof_teams,iw_teams,cl_teams,hc_teams,sh_teams,season_count]
            dump_pkl(system)

            end_season_times[season_count] = time.time()
            if season_count == 1:
                print(Fore.CYAN + f"Season {season_count} Execution Time: {round((end_season_times[season_count]-start)/60)} minutes, {round(((end_season_times[season_count]-start)%60),2)} seconds." + Fore.RESET)
                with open('execution_time', 'a') as e_file:
                    e_file.write(f"Season {season_count} Total Execution Time: {round((end_season_times[season_count]-start)/60)} minutes, {round(((end_season_times[season_count]-start)%60),2)} seconds.\n\n")
            else:
                print(Fore.CYAN + f"Season {season_count} Execution Time: "
                                  f"{round((end_season_times[season_count] - end_season_times[season_count-1]) / 60)} minutes, {round(((end_season_times[season_count] - end_season_times[season_count-1]) % 60), 2)} seconds." + Fore.RESET)
                with open('execution_time', 'a') as e_file:
                    e_file.write(f"Season {season_count} Total Execution Time: "
                                  f"{round((end_season_times[season_count] - end_season_times[season_count-1]) / 60)} minutes, {round(((end_season_times[season_count] - end_season_times[season_count-1]) % 60), 2)} seconds.\n\n")

    # uni_champions.sort(key=lambda x : (x.wins / x.losses), reverse=True)
    end = time.time()
    print(f"\nTotal Execution Time: {round((end-start)/60)} minutes, {round(((end-start)%60),2)} seconds.")

def test_main():
    import numpy as np



    def generate_list(target_total, min_value, max_value, round_to=0):
        final_list = []

        coefficients = np.array([9, 7, 6, 6, 4, 4])

        num_lists = 1

        valid_list_found = False

        while not valid_list_found:

            if round_to == 0:
                initial_values = np.random.randint(min_value, max_value + 1, size=5)
            else:
                initial_values = np.round(np.random.uniform(min_value, max_value, size=5), round_to)

            partial_sum = np.dot(coefficients[:-1], initial_values)
            remaining_value = (target_total - partial_sum) / coefficients[-1]

            if min_value <= remaining_value <= max_value:
                valid_list_found = True

                final_list = np.append(initial_values, remaining_value)


        return final_list


    model_teams = create_teams(32, 'Test')
    model_teams[0].name = "Test_CLONES"
    for pxyr in model_teams[0].players:
        pxyr.power  = 60
        pxyr.atk_dmg = 45
        pxyr.atk_spd = 9
        pxyr.crit_pct = 0.045
        pxyr.crit_x = 10.7
        pxyr.max_health = 540
        pxyr.spawn_time = 11

    total_power_target = 2160 #round to 0
    total_atk_dmg_target = 1620 #round to 0
    total_atk_spd_target = 324 #round to 0
    total_crit_pct_target = 1.62 #round to 4
    total_crit_x_target = 386 #round to 2
    total_health_target = 19440 #round to 2
    total_spawn_target = 396 #round to 0


    for i in range(1,32): #create model teams 1 through 31
        idx = 0
        gen_power_list = generate_list(total_power_target, 49, 60, 0)
        gen_atk_dmg_list = generate_list(total_atk_dmg_target, 40, 65, 0)
        gen_atk_spd_list = generate_list(total_atk_spd_target, 5, 10, 0)
        gen_crit_pct_list = generate_list(total_crit_pct_target, 0.045, 0.11, 4)
        gen_crit_x_list = generate_list(total_crit_x_target, 8, 14, 2)
        gen_health_list = generate_list(total_health_target, 170, 260, 2)
        gen_spawn_list = generate_list(total_spawn_target, 6, 12, 0)
        for plxr in model_teams[i].players:
            plxr.power = gen_power_list[idx]
            plxr.atk_dmg = gen_atk_dmg_list[idx]
            plxr.atk_spd = gen_atk_spd_list[idx]
            plxr.crit_pct = gen_crit_pct_list[idx]
            plxr.crit_x = gen_crit_x_list[idx]
            plxr.max_health = gen_health_list[idx]
            plxr.spawn_time = gen_spawn_list[idx]
            idx += 1



    all_teams = []

    shuffle(model_teams)

    # Split the list into 6 equal parts
    model_groups = [model_teams[i:i + 5] for i in range(0, len(model_teams), 5)]

    dw_teams = create_teams(100, "Darkwing")
    dw_teams = dw_teams + model_groups[0]
    round_robin(dw_teams, 3, len(dw_teams), is_test=True)

    sc_teams = create_teams(100, "Shining-Core")
    sc_teams = sc_teams + model_groups[1]
    round_robin(sc_teams, 3, len(sc_teams), is_test=True)

    ds_teams = create_teams(100, "Diamond-Sea")
    ds_teams = ds_teams + model_groups[2]
    round_robin(ds_teams, 3, len(ds_teams), is_test=True)

    wof_teams = create_teams(100, "Web-of-Nations")
    wof_teams = wof_teams + model_groups[3]
    round_robin(wof_teams, 3, len(wof_teams), is_test=True)

    iw_teams = create_teams(100, "Ice-Wall")
    iw_teams = iw_teams + model_groups[4]
    round_robin(iw_teams, 3, len(iw_teams), is_test=True)

    cl_teams = create_teams(100, "Candyland")
    cl_teams = cl_teams + model_groups[5]
    round_robin(cl_teams, 3, len(cl_teams), is_test=True)

    for group in [dw_teams, sc_teams, ds_teams, wof_teams, iw_teams, cl_teams]:
        for team in group:
            all_teams.append(team)

    team_season_dataframe(all_teams, 0)



    upset_list = []
    champ_list = []
    clear_file('error_output')
    season_count = 0
    season_stats_list = {}

    #league_season(test_teams, season_count=1, region="Test", upset_count=0, upset_list=upset_list, champ_list=champ_list)
    #season_stats_list[season_count] = season_stats(test_teams, season_count, season_stats_list)
    #region_mvp(season_stats_list, season_count=season_count, region='Test')
    #best_of_stats(season_stats_list, season_count=season_count)

def another_test():

    teams = create_teams(22,region='Darkwing')
    league_season(teams,region='Darkwing')



def flush_database(db='C:/Users/carte/ControlDataBase.db'):
    with sqlite3.connect(db):
        pass

def coach_testing():
    clear_file('coach_test_stats')
    clear_file('team_coach_data')
    def write_coach_standings(coach_list,round_no=-1,write_all=False):
        coach_list.sort(key=lambda x: (x.coach_record["Game Wins"], x.coach_record["Match Wins"]), reverse=True)
        with open("coach_test_stats", 'a') as file:
            if write_all:
                file.write(f"FINAL STANDINGS\n")
                for c in coach_list:
                    file.write(f"""{str(c)}: {c.coach_record["Game Wins"]}-{c.coach_record["Game Losses"]}\n""")
            else:
                file.write(f"--Round {round_no + 1} of {len(coach_list)-1}--\n")
                for c in coach_list[:7]:
                    file.write(f"""{str(c)}: {c.coach_record["Game Wins"]}-{c.coach_record["Game Losses"]}\n""")
                file.write("...\n")
                for c in coach_list[-7:]:
                    file.write(f"""{str(c)}: {c.coach_record["Game Wins"]}-{c.coach_record["Game Losses"]}\n""")
                file.write("\n")


    from random import uniform, randint
    from Teams import Coach
    from itertools import cycle

    lineup_modifiers = cycle(["NC", "1C", "2C", "3C", "4C", "5C"])
    slots_amped_possibilities = [ [0], [1], [2], [3], [4], [5],
            [0,5], [1,4], [2,3], [3,5], [3,4], [0,1], [0,4], [1,3], [2,5],
            [0,1,2], [0,2,4], [1,3,5], [2,4,5]
        ]


    coaches = []
    num_coaches = len(slots_amped_possibilities)*6


    for slot_list in slots_amped_possibilities:

        for i in range(6):
            if len(slot_list) == 3:
                slot_amp_possibilities = [
                    ["Power", round(uniform(0.549, 0.929), 2)],
                    ["Attack Damage", randint(2, 5)],
                    ["Critical Chance", round(uniform(0.02, 0.04), 2)]
                ]
            elif len(slot_list) == 2:
                slot_amp_possibilities = [
                    ["Power", round(uniform(0.59, 0.95), 2)],
                    ["Attack Damage", randint(3, 6)],
                    ["Critical Chance", round(uniform(0.0225, 0.0433), 2)]
                ]
            else:
                slot_amp_possibilities = [
                    ["Power", round(uniform(0.69, 0.99), 2)],  # % chance to add power
                    ["Attack Damage", randint(5, 9)],  # raw increment
                    ["Critical Chance", round(uniform(0.025, 0.05), 2)],  # raw increment
                ]
            trait_effects = [
                ["Pp", 1], ['R#', round(uniform(1.25, 1.5), 2)],
                ['C%', round(uniform(1.1, 1.25), 2)], ['I*', round(uniform(0.025, 0.5), 2)],
                ['U-', round(uniform(1.05, 1.1), 2)], ['X+', randint(2, 8)]
            ]


            fixed_slot_effect = [slot_list] + slot_amp_possibilities[i%3]
            fixed_trait_effect = trait_effects[i]

            coach = Coach("Delirium", fixed_lineup_modifier=next(lineup_modifiers), fixed_slot_effect=fixed_slot_effect, fixed_trait_effect=fixed_trait_effect)
            coaches.append(coach)

    teams = [Team("") for _ in range(num_coaches)]
    sorted_teams = sorted(teams, key=lambda t: t.name)
    sorted_coaches = sorted(coaches,key=lambda c: c.name)
    index = 0

    for team in sorted_teams:
        team.change_coach(sorted_coaches[index])
        sorted_coaches[index].teams_coached.append(team.name)
        index+=1

    coach_lineup_mod_count = {'NC': 0, '1C': 0, '2C': 0, '3C': 0, '4C': 0, '5C': 0, 'Error': 0}
    coach_slots_amped_count = {
        (0,): 0, (1,): 0, (2,): 0, (3,): 0, (4,): 0, (5,): 0,
        (0, 5): 0, (1, 4): 0, (2, 3): 0, (3, 5): 0, (3, 4): 0, (0, 1): 0, (0,4) : 0, (1,3) : 0, (2,5) : 0,
        (0, 1, 2): 0, (0, 2, 4): 0, (1, 3, 5): 0, (2, 4, 5): 0
    }
    coach_attribute_amped_count = {"Power": [0, 0], "Attack Damage": [0, 0], "Critical Chance": [0,0]}  # list values: [count of coaches whom affect this trait, total multiplier value]
    coach_trait_amped_count = {'Pp': [0, 0], 'R#': [0, 0], 'C%': [0, 0], 'I*': [0, 0], 'U-': [0, 0], 'X+': [0, 0]}
    total_team_count = 0
    for team in teams:
        total_team_count += 1
        coach_lineup_mod_count[team.team_coach.lineup_modifier] += 1
        coach_slots_amped_count[tuple(team.team_coach.slot_effect[0])] += 1
        coach_attribute_amped_count[team.team_coach.slot_effect[1]][0] += 1
        coach_attribute_amped_count[team.team_coach.slot_effect[1]][1] += team.team_coach.slot_effect[2]
        coach_trait_amped_count[team.team_coach.trait_effect[0]][0] += 1
        coach_trait_amped_count[team.team_coach.trait_effect[0]][1] += team.team_coach.trait_effect[1]

    with open('team_coach_data', 'a') as file:
        file.write(f"--Lineup Modifiers--\n")
        file.write(
            f"NC: {coach_lineup_mod_count['NC']} ({round((100 * coach_lineup_mod_count['NC'] / total_team_count), 2)}%)\n")
        file.write(
            f"1C: {coach_lineup_mod_count['1C']} ({round((100 * coach_lineup_mod_count['1C'] / total_team_count), 2)}%)\n")
        file.write(
            f"2C: {coach_lineup_mod_count['2C']} ({round((100 * coach_lineup_mod_count['2C'] / total_team_count), 2)}%)\n")
        file.write(
            f"3C: {coach_lineup_mod_count['3C']} ({round((100 * coach_lineup_mod_count['3C'] / total_team_count), 2)}%)\n")
        file.write(
            f"4C: {coach_lineup_mod_count['4C']} ({round((100 * coach_lineup_mod_count['4C'] / total_team_count), 2)}%)\n")
        file.write(
            f"5C: {coach_lineup_mod_count['5C']} ({round((100 * coach_lineup_mod_count['5C'] / total_team_count), 2)}%)\n"
            f"--Slots Amplified--\n")

        for amped_slots in [(0,), (1,), (2,), (3,), (4,), (5,),
        (0, 5), (1, 4), (2, 3), (3, 5), (3, 4), (0, 1), (0,4), (1,3), (2,5),
        (0, 1, 2), (0, 2, 4), (1, 3, 5), (2, 4, 5)]:
            file.write(f"{list(amped_slots)}: {coach_slots_amped_count[amped_slots]} "
                       f"({round((100 * coach_slots_amped_count[amped_slots] / total_team_count), 2)}%)\n")
        file.write(f"--Attributes Affected--\n"
                   f"""Power: {coach_attribute_amped_count["Power"][0]} """
                   f"""({round((100 * coach_attribute_amped_count["Power"][0] / total_team_count), 2)}%)\n"""
                   f"""\tAverage Amp: {round((coach_attribute_amped_count["Power"][1] / coach_attribute_amped_count["Power"][0]), 2)}\n"""
                   f"""Attack Damage: {coach_attribute_amped_count["Attack Damage"][0]} """
                   f"""({round((100 * coach_attribute_amped_count["Attack Damage"][0] / total_team_count), 2)}%)\n"""
                   f"""\tAverage Amp: {round((coach_attribute_amped_count["Attack Damage"][1] / coach_attribute_amped_count["Attack Damage"][0]), 2)}\n"""
                   f"""Critical Chance: {coach_attribute_amped_count["Critical Chance"][0]} """
                   f"""({round((100 * coach_attribute_amped_count["Critical Chance"][0] / total_team_count), 2)}%)\n"""
                   f"""\tAverage Amp: {round((coach_attribute_amped_count["Critical Chance"][1] / coach_attribute_amped_count["Critical Chance"][0]), 2)}\n""")
        file.write("--Traits Affected--\n")
        for trait in ['Pp', 'R#', 'C%', 'I*', 'U-', 'X+']:
            file.write(f"""{trait}: {coach_trait_amped_count[trait][0]} """
                       f"""({round((100 * coach_trait_amped_count[trait][0] / total_team_count), 2)}%)\n"""
                       f"""\tAverage Amp: {round((coach_trait_amped_count[trait][1] / coach_trait_amped_count[trait][0]), 2)}\n""")



    for round_count in range(num_coaches-1):
        round_robin(teams,1,0,is_test=True)
        write_coach_standings(coaches,round_no=round_count)
        index = round_count+1
        if round_count != (num_coaches-2):
            if round_count % 10 == 9:
                with open('coach_test_stats', 'a') as file:
                    ex_coach1 = choice(coaches)
                    ex_coach2 = choice(coaches)
                    dupl1 = "NO Duplicates" if len(ex_coach1.teams_coached) == len(set(ex_coach1.teams_coached)) else "DUPLICATES PRESENT"
                    dupl2 = "NO Duplicates" if len(ex_coach2.teams_coached) == len(set(ex_coach2.teams_coached)) else "DUPLICATES PRESENT"
                    file.write(f"{ex_coach1.name} has coached {len(ex_coach1.teams_coached)} teams with {dupl1}: {ex_coach1.teams_coached}\n")
                    file.write(f"{ex_coach2.name} has coached {len(ex_coach2.teams_coached)} teams with {dupl2}: {ex_coach2.teams_coached}\n\n")
            for team in sorted_teams:
                if index <= (num_coaches-1):
                    team.change_coach(sorted_coaches[index])
                    sorted_coaches[index].teams_coached.append(team.name)
                else:
                    team.change_coach(sorted_coaches[(index-num_coaches)])
                    sorted_coaches[index-num_coaches].teams_coached.append(team.name)
                index+=1
    write_coach_standings(coaches,write_all=True)
    for ex_coach in sorted_coaches:
        dupl = "NO Duplicates" if len(ex_coach.teams_coached) == len(set(ex_coach.teams_coached)) else "DUPLICATES PRESENT"
        with open('coach_test_stats','a') as file:
            file.write(f"{ex_coach.name} has coached {len(ex_coach.teams_coached)} teams with {dupl}: {ex_coach.teams_coached}\n")



from stat_functions import clear_all_databases

def test():

    teams = create_teams(26, region='Universal',season_count=1)
    for i in range(1,13):
        teams[i-1].seed = i
    league_season(teams,season_count=1,upset_count=0,upset_list=[],stats_list={}, )




#clear_all_databases()
#initiate_databases()
main()
#another_test()
