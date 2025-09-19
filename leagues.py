from Games import best_of, enablePrint, blockPrint
from contests import round_robin, chain
from Player_Creator import s_tier, a_tier, b_tier, c_tier, slasher
from random import choice, randint, uniform, choices, seed
from seed import generate_seed
from colorama import Fore, Back
# from dump_pickle import dump_pkl
from load_pickle import load_pkl, season_wipe
from numpy import mean
from Players import calculate_standard_deviation, PlayerSeason, grade_seasons, Player
from stat_functions import region_mvp, write_to_file
from time import sleep, time
import pandas as pd
import math
from Teams import Coach
from datetime import datetime
from statistics import stdev
import re

def timed_input(prompt): #False = do nothing with coach decisions, True = manual coach decisions
    make_coach_decisions = False

    if make_coach_decisions:
        user_input = input(prompt)
        return user_input
    else:
        print(prompt)
        return "O"


caps = [2500, 2500, 2850, 3125, 3250, 3300] + ([3330] * 50)

def closest_multiple_of_6(n):
    lower_multiple = (n // 6) * 6
    upper_multiple = lower_multiple + 6

    if abs(n - lower_multiple) <= abs(n - upper_multiple):
        return lower_multiple
    else:
        return upper_multiple


def player_stats_as_df(player: "PlayerSeason", dt, season_count, averages = None, deviations = None):
    avg_stats = {
        'Power': 55,
        'DPS': 55.5 / 7.5,  # Attack Damage / Attack Speed = Damage Per Tick
        'Critical %': 0.065,
        'Critical X': 7.5,
        'Mitigated %' : 0.58,
        'Defense %' : 0.04,
        'Defense Absolute' : 4,
        'Health': 210,
        'Spawn Time': 6.9
    } if not averages else averages

    std_devs = {
        'Power': 2.8310736964118535,
        'DPS': 1.2849939496934677,
        'Critical %': 0.016486753255019818,
        'Critical X': 2.267179294196781,
        'Mitigated %' : 0.0238, #estimated, need to test real std dev
        'Defense %' : 0.01155,
        'Defense Absolute' : 1.155,
        'Health': 28.43499326921077,
        'Spawn Time': 0.8484030789402577

    } if not deviations else deviations


    stats_dict = {'Name' : player.player.name, 'Team' : f"S{season_count}_{player.player.team}",
                  'Power' : (player.power - avg_stats["Power"]) / std_devs["Power"],
                  'DPS' : (player.dps - avg_stats["DPS"]) / std_devs["DPS"],
                  'Health' : (player.max_health-avg_stats["Health"]) / std_devs["Health"],
                  'Critical %' : ((player.crit_pct if player.trait_tag != '$l' else player.insta_kill_pct) - avg_stats["Critical %"]) / std_devs["Critical %"],
                  'Critical X' : (player.crit_x - avg_stats["Critical X"]) / std_devs["Critical X"],
                  'Mitigated %' : (player.mit_pct - avg_stats['Mitigated %']) / std_devs['Mitigated %'],
                  'Defense %' : (player.defense_pct - avg_stats["Defense %"]) / std_devs["Defense %"],
                  'Defense Absolute': (player.defense_abs - avg_stats["Defense Absolute"]) / std_devs["Defense Absolute"],
                  'Spawn Time' : (avg_stats["Spawn Time"] - player.spawn_time) / std_devs["Spawn Time"],
                  'Trait' : player.trait_tag, 'xWAR' : player.player.get_xWAR(averages=averages,deviations=deviations),
                  'Game Wins' : player.game_wins, 'Game Losses' : player.game_losses, 'Game Winrate' : 100*round((player.game_wins / (player.game_wins+player.game_losses)),4),
                  'Effect' : player.effect, 'Kills' : player.kills, 'Deaths' : player.deaths, 'Slot' : player.player.slot,
                  'Team Winrate' : 100*round((player.player.team_wins / (player.player.team_wins + player.player.team_losses)),4), "Time" : dt}

    for word in std_devs.keys():
        stats_dict[word] = round(stats_dict[word], 3)

    return pd.DataFrame([stats_dict])



def player_season_excel(player_seasons,season_count=-1,averages=None,deviations=None):

    OFF = False

    if OFF:
        return 0
    else:
        player_stats_df = pd.DataFrame(columns=['Power', 'DPS', 'Health', 'Critical %', 'Critical X', 'Mitigated %', 'Defense %', 'Defense Absolute', 'Spawn Time', 'Game Wins', 'Game Losses', 'Effect', 'Kills', 'Deaths'])
        path = "ControlPlayerStats.xlsx"
        player_date_time = datetime.now().strftime("%m-%d_%H:%M")

        try:
            current_seasons = pd.read_excel(path, engine='openpyxl')
        except FileNotFoundError:
            return None
        for season in player_seasons:
            player_stats_df = pd.concat([player_stats_df, player_stats_as_df(season,player_date_time,season_count,averages,deviations)])

        all_seasons = pd.concat([current_seasons, player_stats_df])

        with pd.ExcelWriter(path, engine='openpyxl') as writer:
            all_seasons.to_excel(writer, index=False)
            return None


def weighted_averages(team, team_date_time, season_no=-1,appending=False):  # takes in a team and calculates weighted average of each stat, returns a dataframe
    #despite being called weighted_averages, this produces a full dataframe for a team season

    if not appending:
        final_dict = {'Team': team.name, 'Season' : season_no, 'Power': None, 'DPS' : None, 'Critical %': None,
                  'Critical X': None, 'Health': None, 'Spawn Time': 0, 'Lineup Wins': team.wins,
                  'Lineup Losses': team.losses, 'Match Wins': team.match_wins, 'Match Losses': team.match_losses,
                  'Match Draws': team.match_draws, "Time" : team_date_time}
    else:
        final_dict = {'Power': None, 'DPS' : None, 'Critical %': None,
                  'Critical X': None, 'Health': None, 'Spawn Time': 0, 'Lineup Wins': team.wins,
                  'Lineup Losses': team.losses, 'Match Wins': team.match_wins, 'Match Losses': team.match_losses,
                  'Match Draws': team.match_draws, "Time" : team_date_time}

    power_list = [player.power for player in team.players]
    total_power = (power_list[0] * 9) + (power_list[1] * 7) + (power_list[2] * 6) + (power_list[3] * 6) + (
                power_list[4] * 4) + (power_list[5] * 4)
    final_dict['Power'] = round((total_power / 36), 2)

    atk_dmg_list = [player.atk_dmg for player in team.players]
    total_atk_dmg = (atk_dmg_list[0] * 9) + (atk_dmg_list[1] * 7) + (atk_dmg_list[2] * 6) + (atk_dmg_list[3] * 6) + (
                atk_dmg_list[4] * 4) + (atk_dmg_list[5] * 4)
    avg_atk_dmg = round((total_atk_dmg / 36), 2)

    atk_spd_list = [player.atk_spd for player in team.players]
    total_atk_spd = (atk_spd_list[0] * 9) + (atk_spd_list[1] * 7) + (atk_spd_list[2] * 6) + (atk_spd_list[3] * 6) + (
                atk_spd_list[4] * 4) + (atk_spd_list[5] * 4)
    avg_atk_spd = round((total_atk_spd / 36), 2)

    final_dict['DPS'] = round((avg_atk_dmg / avg_atk_spd), 2)

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

    team_date_time = datetime.now().strftime("%m-%d_%H:%M")
    for team in teams:
        team_stats_df = pd.concat([team_stats_df, weighted_averages(team,team_date_time)])

    path = "ControlAverageStats.xlsx"

    with pd.ExcelWriter(path, engine='openpyxl') as writer:
        team_stats_df.to_excel(writer, sheet_name='TeamWeightedAverages', index=False)



#this will allow me to manually draft players for each team

def write_champ(champ, season_count, region, league=None):
    # the champ list from main is a dictionary with keys for seasons, and values as a nested dictionary with each region's name as a key and the champ as a value
    # this function will be run with only a single season's dictionary of champions, with the season_count imported separately
    run_function = True #toggle function
    if not run_function:
        pass
    else:
        champ_dict_a = {"Season" : season_count, "Region" : region, "Team" : champ.name, "Seed" : champ.seed, "xWAR" : champ.get_team_xWAR()}
        champ_df = pd.DataFrame([champ_dict_a])
        full_champ_df = pd.concat([champ_df.reset_index(drop=True), weighted_averages(team=champ,team_date_time=datetime.now().strftime("%m-%d_%H:%M"),season_no=season_count,appending=True).reset_index(drop=True)],axis=1)

        valid_regions = ['Darkwing Regional', 'Shining-Core Regional', 'Diamond-Sea Regional',
                         'Web-of-Nations Regional', 'Ice-Wall Regional', 'Candyland Regional', "Hell's-Circle Regional",
                         'Steel-Heart Regional']
        with open("champs", 'a') as c:
            if region in valid_regions:
                c.write(f"S{season_count} {region} Champion: {champ.name}\n"
                        f"Entered playoffs as the {champ.seed} seed.\n\n")
            else:
                c.write(f"S{season_count} Universal Champion: {champ.name}\n"
                        f"Entered playoffs as the {champ.seed} seed.\n\n")

        with pd.ExcelWriter("ChampStats.xlsx", engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            workbook = writer.book
            sheet = workbook['Sheet1']

            # Count only truly non-empty rows
            non_empty_rows = 0
            for row in sheet.iter_rows():
                if any(cell.value is not None for cell in row):
                    non_empty_rows += 1

            header = non_empty_rows == 0
            start_row = non_empty_rows

            avgs_df = pd.DataFrame([get_league_averages(league,season_count,region)])

            total_df = pd.concat([avgs_df, full_champ_df], ignore_index=True)

            total_df.to_excel(writer, index=False, startrow=start_row, header=header)


def get_league_averages(teams,season_count,region="None",for_xWAR=False,for_players=False):
    #returns dictionary with the weighted average value for each stat in a given league
    dummy = slasher()
    #get_xWAR is a part of class Player, so I need to apply it to a player even when it uses the avg stats


    if for_players:
        players = teams
        return {"Power": mean([p.power for p in players]),
                "DPS": mean([p.dps for p in players]),
                "Critical %": mean([p.crit_pct for p in players]),
                "Critical X": mean([p.crit_x for p in players]),
                "Mitigated %": mean([p.mit_pct for p in players]),
                "Defense %" : mean([p.defense_pct for p in players]),
                "Defense Absolute" : mean([p.defense_abs for p in players]),
                "Health": mean([p.max_health for p in players]),
                "Spawn Time": mean([p.spawn_time for p in players])}
    else:
        if not for_xWAR:
            avg_stats_dict = {"Power" :  mean([team.get_weighted_stat("Power") for team in teams]),
                "DPS" : mean([team.get_weighted_stat("DPS") for team in teams]),
                "Critical %" :  mean([team.get_weighted_stat("Critical %") for team in teams]),
                "Critical X" : mean([team.get_weighted_stat("Critical X") for team in teams]),
                "Mitigated %": mean([team.get_weighted_stat("Mitigated %") for team in teams]),
                "Defense %" : mean([team.get_weighted_stat("Defense %") for team in teams]),
                "Defense Absolute": mean([team.get_weighted_stat("Defense Absolute") for team in teams]),
                "Health" : mean([team.get_weighted_stat("Health") for team in teams]),
                "Spawn Time" : mean([team.get_weighted_stat("Spawn Time") for team in teams])}

            other_dict = {
                "Season" : season_count,
                "Region": region,
                "Team": "REGIONAL AVERAGES",
                "Seed" : "N/A",
                "xWAR" : dummy.get_xWAR(set_stats=avg_stats_dict),

            }

            return other_dict | avg_stats_dict
        else:
            return {"Power" :  mean([team.get_weighted_stat("Power") for team in teams]),
                "DPS" : mean([team.get_weighted_stat("DPS") for team in teams]),
                "Critical %" :  mean([team.get_weighted_stat("Critical %") for team in teams]),
                "Critical X" : mean([team.get_weighted_stat("Critical X") for team in teams]),
                "Mitigated %": mean([team.get_weighted_stat("Mitigated %") for team in teams]),
                "Defense %": mean([team.get_weighted_stat("Defense %") for team in teams]),
                "Defense Absolute": mean([team.get_weighted_stat("Defense Absolute") for team in teams]),
                "Health" : mean([team.get_weighted_stat("Health") for team in teams]),
                "Spawn Time" : mean([team.get_weighted_stat("Spawn Time") for team in teams])}



def ordinal_string(n: int) -> str:
    if 10 <= n % 100 < 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"

def half_to_one(num):
    if num == 1:
        return 1
    else:
        x = (abs(num - 1)) / 2
        return (num + x) if num < 1 else (num - x)

def x_over_one(num, times):
    if num <= 1:
        return 1
    else:
        over_one = num-1
        return 1 + (times*over_one)


def grade_players(players, is_team=None, averages=None, deviations=None):
    for player in players:
        player.get_xWAR(averages=averages, deviations=deviations)

    players.sort(key=lambda pl: pl.xWAR, reverse=True)
    rank_index = 0
    for player in players:
        player.grade_dict['Rank'] = 1 + rank_index
        rank_index += 1



def user_draft(teams, season_count, is_regional=False, void=False, second = False,
               draft_name='Default', league_season_stats= None, auto_mine = True, third = False,write_draft = False):

    #league_season_stats will import the season stats from the league in which the draft is being held,
    #so that I can import it into grade_player_seasons to grade the seasons of my players in relation to
    #the rest of the league they are in
    #this functionality ONLY matters if I am drafting my own players, which I don't care about doing
    #this is disabled as of 11/02/2024
    seed(generate_seed())
    number = -1
    with open('draft_history', 'w') as bruh:
        bruh.write('')
    draft_class = {}
    if not is_regional and not void: #universal draft
        for i in [0,1]:
            add = s_tier(round(uniform(-2,3.99),2), pre_reflect=(uniform(0,0.125)))
            add.team = i
            draft_class[i] = add
        for i in [2,3,4,5,6,7,8,24]:
            add = a_tier(round(uniform(-3,4.99),2))
            add.team = i
            draft_class[i] = add
        for i in [9,28,29]:
            add = a_tier((round(uniform(0.49,2.99),2)))
            add.team = i
            draft_class[i] = add
        for i in [10,11,12,13,14,15,16]:
            add = b_tier(round(uniform(-2.99,4.89),2))
            add.team = i
            draft_class[i] = add
        for i in [17,30]:
            add = b_tier(round(uniform(2.99,3.99),2))
            add.team = i
            draft_class[i] = add
        for i in [18,19,20,21,22,23]:
            add = c_tier(round(uniform(-1.99,3.01),2), fixed=choice(['C%','Pp']))
            add.team = i
            draft_class[i] = add
        for i in [25, 26, 27]:
            add = slasher(round(uniform(-0.25,3.25), 2))
            add.team = i
            draft_class[i] = add
    elif is_regional and not void: #regional draft
        for i in [27,28,29]:
            add = s_tier(round(uniform(1,5),1))
            add.team = i
            draft_class[i] = add
        for i in [0,1,2,3,4,5,6,24]:
            add = a_tier(round(uniform(1,6),2))
            add.team = i
            draft_class[i] = add
        for i in [7,8,9,10,11,12,13,14,15,25]:
            add = b_tier(round(uniform(1,6),2))
            add.team = i
            draft_class[i] = add
        for i in [16,17,18,19,20,26,36]:
            add = c_tier(round(uniform(1, 7.5), 2))
            add.team = i
            draft_class[i] = add
        for i in [21,22,23]:
            add = slasher(round(uniform(1, 2.5), 2))
            add.team = i
            draft_class[i] = add
        for i in [31, 32, 33, 34, 35, 30]:
            trait = choice(['R#', 'C%', 'I*', 'U-', 'X+'])
            add = choice([s_tier(round(uniform(0, 2)), fixed=trait), a_tier(round(uniform(0, 2)), fixed=trait),
                          b_tier(round(uniform(0, 2.5)), fixed=trait), c_tier(round(uniform(0, 3)), fixed=trait)])
            add.team = i
            draft_class[i] = add
    elif void: #void draft
        for i in range(len(teams)):
            if i%3 == 0:
                add = b_tier(round(randint(-10000,60000)/10000, 2), pre_reflect=(uniform(0,0.15)))
            elif i%3 == 1:
                add = a_tier(round(randint(-10000,60000)/10000, 2), pre_reflect=(uniform(0,0.125)))
            else:
                add = c_tier(round(uniform(-2.25, 7.75), 2), pre_reflect=(uniform(0.25,0.95)))
                add.team = i
                draft_class[i] = add
            add.team = i
            draft_class[i] = add
        for i in range(6):
            add = s_tier(round(randint(-10000,60000)/10000, 2), pre_reflect=(uniform(0.01,0.05)))
            add.team = i+len(teams)
            draft_class[(i+len(teams))] = add
        for i in range(6,10):
            trait = choice(['R#', 'C%', 'I*', 'U-', 'X+'])
            add = choice([s_tier(round(uniform(-0.5, 2.5)), fixed=trait), a_tier(round(uniform(-0.5, 3)), fixed=trait),
                          b_tier(round(uniform(-0.5, 3.5)), fixed=trait), c_tier(round(uniform(-0.5, 4)), fixed=trait)])
            add.team = i+len(teams)
            draft_class[(i+len(teams))] = add

    if second: #second round
        #104 teams miss regional playoffs (second_pick == 1)
        # up to 64 teams (but never close to 64) could be second_pick == 2
        # so draft_class should be 104 good players and 64 decent players
        # secondary draft will also run grade_players on all team rosters and the draft class
        # so that teams can see if there is a player remaining in the draft that is better than their worst player
        #if there is no option for upgrade, they pass the pick

        second_all_players = []
        base = len(teams)

        for i in range((base-10)):
            if i%3 == 0:
                add = s_tier(round(uniform(-2.0,4.5), 2))
            elif i%3 == 1:
                add = a_tier(round(uniform(-2.5, 4.0), 2))
            else:
                add = b_tier(round(uniform(-1.5, 5.0), 2))
            add.team = i
            draft_class[i] = add
        for i in range((base-10), (base+25)):
            if i%3 == 0:
                add = a_tier(round(uniform(-1.0,5.0), 2))
            elif i%3 == 1:
                add = b_tier(round(uniform(-0.5, 5.5), 2))
            else:
                add = c_tier(round(uniform(-2.0, 6.5), 2))
            add.team = i
            draft_class[i] = add
        for i in [(base+26), (base+27), (base+28)]:
            add = a_tier(7)
            add.team = i
            draft_class[i] = add
        for i in [(base+29), (base+30), (base+31), (base+32), (base+33)]:
            add = slasher(round(uniform(1.25,3), 2))
            add.team = i
            draft_class[i] = add
        for i in [(base+34), (base+35), (base+36), (base+37), (base+38)]:
            trait = choice(['R#', 'C%', 'I*', 'U-', 'X+'])
            add = choice([s_tier(round(uniform(0, 2.5)), fixed=trait), a_tier(round(uniform(0, 3)), fixed=trait),
                          b_tier(round(uniform(0, 3.5)), fixed=trait), c_tier(round(uniform(0, 4)), fixed=trait)])
            add.team = i
            draft_class[i] = add

        for team in teams:
            team.second_pick = 0
            for player in team.players:
                second_all_players.append(player)
    elif third: #third round
        third_all_players = []

        for team in teams:
            team.third_pick = 0
            for player in team.players:
                third_all_players.append(player)

        base = closest_multiple_of_6(len(teams) + 12)
        for i in range(base):
            if i%6 == 0:
                coin = choice([True, False])
                if coin:
                    add = s_tier(round(uniform(3.0,6.0), 2))
                else:
                    add = c_tier(round(uniform(2.0,7.0), 2))
            elif i%6 == 1:
                coin = choice([True, False, False])
                if coin:
                    add = s_tier(round(uniform(3.0, 6.0), 2))
                else:
                    add = b_tier(round(uniform(1.5, 5.5), 2))
            elif i%6 == 2:
                coin = choice([True, False, False, False])
                if coin:
                    add = s_tier(round(uniform(3.0, 6.0), 2))
                else:
                    add = a_tier(round(uniform(2.0, 5.0), 2))
            elif i%6 == 3:
                coin = choice([True, False, False, False, False])
                if coin:
                    add = s_tier(round(uniform(3.5, 6.5), 2))
                else:
                    add = s_tier(round(uniform(1.0, 5.0), 2))
            elif i%6 == 4:
                add = choice([slasher(round(uniform(0,2.5), 2)), a_tier(round(uniform(3.0, 3.99), 2))])
            elif i%6 == 5:
                trait = choice(['R#', 'C%', 'I*', 'U-', 'X+'])
                add = choice([s_tier(round(uniform(0, 2.5)), fixed=trait), a_tier(round(uniform(0, 3)), fixed=trait),
                              b_tier(round(uniform(0, 3.5)), fixed=trait), c_tier(round(uniform(0, 4)), fixed=trait)])
            else:
                #should never happen, just wanted to get rid of error message
                add = a_tier(round(uniform(0,2)))
            #ignore error
            add.team = i
            draft_class[i] = add


    p = draft_class.copy()
    #not sure why this is an if/else block, but I don't want to mess with it
    #players in the draft class are graded here and given a grade_dict['Rank']
    averages = get_league_averages(p.values(), season_count, for_xWAR=True,for_players=True)
    stats = ["power", "dps", "crit_pct", "crit_x", "mit_pct", "max_health", "spawn_time"]
    deviations = {"Power": 0, "DPS": 0, "Critical %": 0, "Critical X": 0, "Mitigated %" : 0, "Health": 0, "Spawn Time": 0}
    translated_stats = {'power': 'Power', 'dps': 'DPS', 'crit_pct': 'Critical %', 'crit_x': 'Critical X', 'mit_pct' : 'Mitigated %',
                        'max_health': 'Health',
                        'spawn_time': 'Spawn Time'}
    for stat in stats:
        values = [getattr(v, stat) for v in p.values()]  # or p[stat] if using dicts
        deviations[translated_stats[stat]] = stdev(values)
    if second:
        #ignore
        temp_players = list(p.values()) + second_all_players
        grade_players(list(temp_players),averages=averages)
    elif third:
        #ignore
        temp_players = list(p.values()) + third_all_players
        grade_players(list(temp_players),averages=averages)
    else:
        grade_players(list(p.values()),averages=averages)

    #if it is a second round, grade_players will assign player.grade_dict['Rank'] to all players
    #they are ranked in a list which contains all players from all teams with a Second Round draft pick, and
    #all the players in the Second Round draft class
    #teams will select another player only if there is a player on the draft list with a better rank than
    #their lowest ranked player. and, of course, they will pick the highest ranked player in the draft class


    p = dict(sorted(p.items(), key=lambda plyr: plyr[1].xWAR, reverse=True))

    def get_player_rank(plyr, plyr_list):
        sorted_players = sorted(plyr_list, key=lambda px: px.xWAR, reverse=True)
        for ix, px in enumerate(sorted_players, start=1):
            if px == plyr:
                return ix
        return None

    def find_best_upgrade(team, draft_pool):
        team_lineup = team.players
        current_value = team.get_team_xWAR()
        cap = caps[season_count]
        used_fallback = False

        best_upgrade = draft_pool[-1]
        best_old_player = team_lineup[0].name
        new_player_rank = len(draft_pool)
        best_value = -1000000


        for old_player in team_lineup:
            old_xWAR = old_player.get_xWAR()
            for new_player in draft_pool:
                new_xWAR = new_player.get_xWAR()
                new_value = current_value + new_xWAR - old_xWAR

                if cap >= new_value > best_value:
                    best_value = new_value
                    best_upgrade = new_player
                    best_old_player = old_player.name
                    new_player_rank = get_player_rank(new_player, draft_pool)

        if best_upgrade == draft_pool[-1] and best_old_player == team_lineup[0].name and new_player_rank == len(draft_pool):
            # fallback: no legal upgrade found
            with open("cap_fallback", "a") as fallback:
                fallback.write(f"{team.name}, season {season_count} {draft_name}\n")
            used_fallback = True


        return best_upgrade, best_old_player, new_player_rank, used_fallback

    for i in range(len(teams)):

        if write_draft and i == 0:
            with open('draft_list', 'w', buffering=10) as f:
                f.write(f"{draft_name}")
            with open('draft_list', 'a', buffering=10) as f:

                f.write(f" {len(p.values())} of {len(draft_class)} players remaining.\n")
                for player in p.values():
                    f.write('\n')
                    f.write('\n')
                    f.write(str(player))
                    f.write('\n')

        if teams[i].mine and not auto_mine: # make sure to keep auto_mine on because this has not been updated to work
            enablePrint()
            x=0
            my_players_seasons = []
            if league_season_stats:
                full_season_list = []
                for val in league_season_stats.values():
                    for season in val:
                        full_season_list.append(season)


                for player in teams[i].players:
                    temp = PlayerSeason(player, season_count)
                    my_players_seasons.append(temp)
                grade_seasons(my_players_seasons, True, import_averages=full_season_list)
                my_players_seasons.sort(key=lambda szn : szn.season_grade_data, reverse=True)
                for thing in my_players_seasons:
                    thing.print_player_season(filename='my_teams')
                    print(f"({x})")
                    thing.print_player_season()
                    x+=1
            else:
                for player in teams[i].players:
                    temp = PlayerSeason(player, season_count)
                    temp.print_player_season(filename='my_teams')
                    print(f"({x})")
                    temp.print_player_season()
                    x += 1
            print(f"{teams[i].name} to select.")
            try:
                terminate = int(input("Choose player index to terminate."))
            except IndexError:
                terminate = int(input("Choose 0, 1, 2, or 3."))
            index = int(input("Choose player index to draft."))
            try:
                draft(p[index], teams[i], index=i, season_count=season_count, repl=terminate, draft_name=draft_name)
            except KeyError:
                print("Index unavailable. Options are:",end=' ')
                for key in p.keys():
                    print(key,end=', ')
                print('')
                index = int(input("Choose player index to draft."))
                draft(p[index], teams[i], index=i, season_count=season_count, repl=terminate, draft_name=draft_name)
            del p[index]
        else:
            players_in_class = list(p.values())

            #create filler player to start
            top_player = s_tier()
            top_player.grade_dict['Rank'] = 1000

            for player in players_in_class:
                #find player with best rank value and set them to top player which will be drafted
                if player.grade_dict['Rank'] < top_player.grade_dict['Rank']:
                    top_player = player

            index = top_player.team

            teams[i].players = sorted(teams[i].players, key=lambda pl: pl.xWAR, reverse=True)

            pass_word = "Secondary" if second else "Tertiary" if third else "Draft"

            team_choice = find_best_upgrade(teams[i], sorted(list(p.values()), key= lambda py : py.xWAR, reverse=True))

            if team_choice[3]:
                teams[i].history[season_count] += f"\tPassed {pass_word} pick.\n"
            else:
                draft(player=team_choice[0], repl=team_choice[1], team=teams[i], index=i, season_count=season_count,
                      draft_name=draft_name,
                      averages=averages, deviations=deviations,new_pl_rank=team_choice[2])
                for key, value in list(p.items()):
                    if value == team_choice[0]:
                        del p[key]
                        break


def draft(player, team, index, season_count, repl="Name", draft_name="None", averages=None, deviations=None,new_pl_rank=None):
    # team.print_roster()

    cap = caps[season_count]
    slot = -1

    old_xWAR = team.get_team_xWAR()

    old = next(p for p in team.players if p.name == repl)
    team.players.sort(key=lambda p: p.xWAR, reverse=True)
    for i, plyr in enumerate(team.players):
        if plyr.name == repl:
            slot = i
    team.players[slot] = player
    player.team = team.name

    new_xWAR = old_xWAR - old.xWAR + player.xWAR

    if draft_name == "Secondary draft":
        player.drafted = f"Drafted {ordinal_string(index + 1)} in the S{season_count} Second Round draft"
        team.history[season_count] += f"\n\tWith the {ordinal_string(index + 1)} pick in the Second Round draft, selected {player.name} ({ordinal_string(new_pl_rank)} best remaining in class)" \
                                      f" [Terminated Slot {slot}, {repl}] xWAR: {old_xWAR} -> {new_xWAR} ({new_xWAR-cap} to cap)"
        team.second_pick = 0
    elif draft_name == "Tertiary draft":
        player.drafted = f"Drafted {ordinal_string(index + 1)} in the S{season_count} Third Round draft"
        team.history[
            season_count] += f"\n\tWith the {ordinal_string(index + 1)} pick in the Third Round draft, selected {player.name} ({ordinal_string(new_pl_rank)} best remaining in class)" \
                             f" [Terminated Slot {slot},  {old.name}] xWAR: {old_xWAR} -> {new_xWAR} ({new_xWAR-cap} to cap)"
        team.third_pick = 0
    elif draft_name != "None":
        player.drafted = f"Drafted {ordinal_string(index+1)} in the S{season_count} {draft_name}"
        team.history[season_count] += f"\n\tWith the {ordinal_string(index+1)} pick in the {draft_name}, selected {player.name} ({ordinal_string(new_pl_rank)} best remaining in class)" \
                                      f" [Terminated Slot {slot},  {old.name}] xWAR: {old_xWAR} -> {new_xWAR} ({new_xWAR-cap} to cap)"
    else:
        print("Catastrophic draft error.")
        write_to_file(error=True, words=f"Draft error, S{season_count}: no draft name given.")

    #with open('draft_history', 'a') as x:
    #    x.write(f"{player.name} has been drafted to {team.name}\n{old.name} terminated.\n")

def player_changes(teams, season_count=-1):

        better_count = {'Player' : 0, 'Team' : 0}
        worse_count = {'Player' : 0, 'Team' : 0}
        neutral_count = {'Player' : 0, 'Team' : 0}

        total_factor = 0
        factor_count = 0

        total_xWAR_increment = 0
        total_xWAR_increment_count = 0

        total_increment = {'Attack Damage' : 0, 'Health' : 0, 'Critical %' : 0, 'Critical X' : 0, 'Team xWAR' : 0}
        increment_count = {'Attack Damage' : 0, 'Health' : 0, 'Critical %' : 0, 'Critical X' : 0, 'Team xWAR' : 0}
        avg_increment = {'Attack Damage' : 0, 'Health' : 0, 'Critical %' : 0, 'Critical X' : 0, 'Team xWAR' : 0}


        seed(generate_seed())
        def level_out(pl, mine=False):
            level_age_factor = 1 - ((pl.age + 3) / 100)
            list_of_100 = [num for num in range(100)]

            if pl.power > 62:
                pl.power = 61
                if mine:
                    with open('off_season_report', 'a') as fle:
                        fle.write(f"{pl.name} power leveled out to 61.\n")
            if pl.atk_spd < 4:
                pl.atk_spd = 4
                if mine:
                    with open('off_season_report', 'a') as fle:
                        fle.write(f"{pl.name} attack speed leveled out to 4.\n")
            if pl.atk_spd > 10:
                pl.atk_spd = 10
                if mine:
                    with open('off_season_report', 'a') as fle:
                        fle.write(f"{pl.name} attack speed leveled out to 10.\n")
            if (pl.atk_dmg >= 68 and pl.trait_tag != "$l") or (pl.atk_dmg >= 90 and player.trait_tag=='$l'):
                pl.atk_dmg = 65 if pl.trait_tag != '$l' else 89
                if mine:
                    with open('off_season_report', 'a') as fle:
                        fle.write(f"{pl.name} attack damage leveled out to {str(70 if pl.trait_tag != '$l' else 89)}.\n")
            if pl.atk_dmg < 40:
                pl.atk_dmg = 40
                if mine:
                    with open('off_season_report', 'a') as fle:
                        fle.write(f"{pl.name} attack damage leveled out to 40.\n")

            if pl.max_health < 120:
                pl.max_health = 120
                if mine:
                    with open('off_season_report', 'a') as fle:
                        fle.write(f"{pl.name} health leveled out to 120.\n")
            while pl.max_health >= 329:
                pl.max_health = 310
                if mine:
                    with open('off_season_report', 'a') as fle:
                        fle.write(f"{pl.name} health leveled out to 310.\n")
            if pl.crit_x >= 14.5:
                pl.crit_x = choice([13,14])
                if mine:
                    with open('off_season_report', 'a') as fle:
                        fle.write(f"{pl.name} crit-x leveled out to {pl.crit_x}.\n")
            if pl.crit_x <= 5.00:
                pl.crit_x = choice([5.5,6.5,7.5])
                if mine:
                    with open('off_season_report', 'a') as fle:
                        fle.write(f"{pl.name} crit-x leveled out to {pl.crit_x}.\n")

            if pl.crit_pct >= 0.13 or (pl.tier == '$l' and pl.insta_kill_pct >= 0.13):
                pl.crit_pct = choice([0.1213,0.12135,0.1214,0.12145])
                if pl.tier == '$l':
                    pl.insta_kill_pct = pl.crit_pct
                if mine:
                    with open('off_season_report', 'a') as fle:
                        fle.write(f"{pl.name} crit-pct leveled out to {pl.crit_pct}.\n")
            if pl.crit_pct <= 0.025:
                pl.crit_pct = 0.045
                if pl.tier == '$l':
                    pl.insta_kill_pct = pl.crit_pct
                if mine:
                    with open('off_season_report', 'a') as fle:
                        fle.write(f"{pl.name} crit-pct leveled out to {pl.crit_pct}.\n")

        for team in teams:
            mine = False
            old_team_xWAR = 0
            new_team_xWAR = 0
            if team.mine or team.is_noteworthy:
                mine = True

            for player in team.players:

                breakout_coin = randint(1,250)
                if player.breakout:
                    x_factor = choice([0.25, 0.3, 0.35, 0.4, 0.45, 0.5])
                    player.breakout = False
                elif breakout_coin in [99,199]:
                    x_factor = choice([0.2, 0.2, 0.2, 0.25, 0.25, 0.3, 0.35, 0.4, 0.45])
                    team.history[season_count] += f"\n\tLOTTERY: {player.name} will have a breakout season!\n"
                elif breakout_coin in range((250-player.age), 250) and player.age <= 3:
                    x_factor = choice([0.075,0.075,0.1,0.125,0.15])
                elif breakout_coin in [18,118,218] or breakout_coin in range(1,player.age) or (player.age >= 9 and choice([True,False,False])):
                    x_factor = choice([round(-0.045*player.age,2), round(-0.05*player.age, 2), round(-0.055*player.age, 2), -0.2, -0.25, -0.3, -0.35, -0.4, -0.45, -0.5])
                    team.history[season_count] += f"\n\tWASHED: {player.name} will significantly decline this season.\n"
                elif breakout_coin % 15 == 0:
                    x_factor = choice([0.1, 0.125, 0.15])
                elif breakout_coin in [x*15 - 5 for x in range(1,21)]:
                    x_factor = choice([-0.1, -0.125, -0.15])
                else:
                    x_factor = 0

                y1_factor = [0.95, 1.05]
                y2_factor = [1.1, 1.04, 1.04, 1, 0.99, 0.98, 0.97, 0.96]
                for i in range(math.ceil(player.amp*0.67)):
                    y1_factor[0]+=0.01
                    y1_factor.append(1.05)
                    y2_factor.append(1.025)
                year_one = choice(y1_factor)
                year_two = choice(y2_factor)
                age_factor = [year_one, year_two, choice([1.02, 1.01, 1, 0.99, 0.98]), 1,
                              choice([1, 0.98, 0.96, 0.94]), choice([0.97, 0.95, 0.93, 0.91]), choice([0.96, 0.94, 0.92, 0.9]), choice([0.95, 0.93, 0.91, 0.89]),
                              choice([0.94, 0.92, 0.9, 0.88]), choice([0.93, 0.91, 0.89, 0.87]), 0.8, 0.775, 0.75]
                for i in range(100):
                    age_factor.append((.75 - (i/1000)))
                tier_factor = {'S' : choice([-0.015, -0.0125, -0.01, -0.0075, -0.005, -0.0025, 0, 0.0025, 0.005]),
                               'A' : choice([-0.0125, -0.01, -0.0075, -0.005, -0.0025, 0, 0.0025, 0.005, 0.0075]),
                               'B' : choice([-0.01, -0.0075, -0.005, -0.0025, 0, 0.0025, 0.005, 0.0075, 0.01]),
                               'C' : choice([-0.005, -0.0025, 0, 0.0025, 0.005, 0.0075, 0.01, 0.0125]),
                               '$l' : choice([0, 0.005, 0.005, 0.01, 0.01, 0.015, 0.02])}
                trait_factor = { 'C%' : choice([-0.03, -0.025, -0.02, -0.015, -0.01, -0.005, 0, 0.005]),
                                 'I*': choice([-0.015, -0.01, -0.005, 0, 0.005, 0.01, 0.015]),
                                 'Pp': choice([-0.025, -0.025, -0.02, -0.2, -0.01, -0.01, 0, 0.025]),
                                 'R#': choice([-0.03, -0.0275, -0.025, -0.0225, -0.02, -0.0175, -0.015, -0.0125, -0.01, -0.0075, -0.005, -0.0025, 0, 0.0025, 0.005]),
                                 'X+': choice([-0.04, -0.035, -0.025, -0.015]),
                                 'U-' : choice([-0.03, -0.0275, -0.025, -0.0225, -0.02, -0.0175, -0.015, -0.0125, -0.01, -0.0075, -0.005, -0.0025, 0, 0.0025, 0.005]),
                                 '$l': choice([0, 0.005, 0.005, 0.01, 0.01, 0.015, 0.02]), #because crit multipliers naturally go up over time and slasher crit x stays the same, they need to be compensated
                                 'Sp' : choice([-0.01, -0.005, 0, 0.01]),
                                 'V.' : choice([-0.01, -0.005, 0, 0.01]),
                                 'Hn' : choice([-0.01, -0.005, 0, 0.01]),
                                 'Tx' : choice([-0.01, -0.005, 0, 0.01]),
                                 'Fl' : choice([-0.01, -0.005, 0, 0.01]),
                                 "None" : 0
                }
                #used for balancing purposes
                random_factor = choice([-0.02, -0.019, -0.018, -0.017, -0.016, -0.015, -0.014, -0.013, -0.012, -0.011, -0.01, 0, 0.01])
                random_factor *= choice([0.25,0.5,1,1,1,1,2,2,3])

                if player.tier not in tier_factor.keys():
                    tier_factor[player.tier] = 0
                t_factor = trait_factor[player.trait_tag] + tier_factor[player.tier] + random_factor
                factor = age_factor[player.age] + t_factor + x_factor
                if factor == 1:
                    factor = choice([0.99, 1.01])

                chance_for_extra_trait = abs(1 - factor)
                extra_trait_roll = uniform(0, 1)


                total_factor += factor
                factor_count += 1

                if mine:
                    with open('off_season_report', 'a') as file:
                        file.write(f"Changes for {player.name}\n")
                        file.write(f"Factor: {factor:.6f}\n\tAge Factor: {age_factor[player.age]}\n\tT_Factor: {t_factor:.6f}"
                                   f"\n\t\tTrait Factor: {trait_factor[player.trait_tag]}\n\t\tTier Factor: {tier_factor[player.tier]}\n\t\tRandom Factor: {random_factor}\n\tX_Factor: {x_factor}\n")

                power_coin = mean([uniform(1, 1.35), uniform(1,1.35)])
                if player.age >= 10:
                    player.power -= 1

                if factor > power_coin:
                    p2_coin = choice([0, -1, -1, -1, -1, -2])
                    player.power += p2_coin
                    if mine and p2_coin != 0:
                        coin_sign = "+" if p2_coin > 0 else ""
                        with open('off_season_report', 'a') as file:
                            file.write(f"Power: {coin_sign}{p2_coin}\n")
                else:
                    p2_coin = choice([-1, 0, 1, 1, 1])
                    player.power += p2_coin
                    if mine and p2_coin != 0:
                        coin_sign = "+" if p2_coin > 0 else ""
                        with open('off_season_report', 'a') as file:
                            file.write(f"Power: {coin_sign}{p2_coin}\n")

                coins = [choice([True, False]), choice([True,False])]
                if player.tier == '$l':
                    coins[0] = False
                    coins[1] = True

                if coins[0] and coins[1]:
                    #Heads and Heads: Attack Damage, Health, and Defense Absolute
                    pl_old_xWAR = player.get_xWAR()
                    old_team_xWAR += pl_old_xWAR

                    old_atk_dmg = player.atk_dmg
                    old_max_health = player.max_health
                    #old_defense_abs = player.defense_abs

                    player.atk_dmg = round(player.atk_dmg * half_to_one(factor))
                    player.max_health = round(player.max_health * factor, 2) if factor < 1.2 else round(player.max_health * 1.2, 2)

                    total_increment['Attack Damage'] += round((player.atk_dmg - old_atk_dmg),2)
                    total_increment['Health'] += round((player.max_health - old_max_health), 3)
                    increment_count['Attack Damage'] += 1
                    increment_count['Health'] += 1

                    pl_new_xWAR = player.get_xWAR()
                    player.xWAR = pl_new_xWAR
                    new_team_xWAR += player.get_xWAR()

                    total_xWAR_increment += (pl_new_xWAR - pl_old_xWAR)
                    total_xWAR_increment_count += 1

                    if pl_new_xWAR > pl_old_xWAR:
                        better_count['Player'] += 1
                    elif pl_old_xWAR > pl_new_xWAR:
                        worse_count['Player'] += 1
                    else:
                        neutral_count['Player'] += 1

                    if mine:
                        atk_dmg_sign = "+" if old_atk_dmg < player.atk_dmg else ""
                        max_health_sign = "+" if old_max_health < player.max_health else ""
                        with open('off_season_report', 'a') as file:
                            file.write(f"Attack Damage: {atk_dmg_sign}{player.atk_dmg - old_atk_dmg :.5f}\n"
                                       f"Max Health: {max_health_sign}{player.max_health - old_max_health :.5f}\n")
                    if extra_trait_roll >= chance_for_extra_trait:
                        ex_coin1 = choice([True,False])
                        if ex_coin1: #Critical-X
                            pl_old_xWAR = player.get_xWAR()
                            old_team_xWAR += pl_old_xWAR

                            old_crit_x = player.crit_x

                            player.crit_x = round(player.crit_x * factor, 3)

                            total_increment['Critical X'] += round((player.crit_x - old_crit_x), 3)
                            increment_count['Critical X'] += 1

                            pl_new_xWAR = player.get_xWAR()
                            player.xWAR = pl_new_xWAR
                            new_team_xWAR += player.get_xWAR()

                            total_xWAR_increment += (pl_new_xWAR - pl_old_xWAR)
                            total_xWAR_increment_count += 1

                            if pl_new_xWAR > pl_old_xWAR:
                                better_count['Player'] += 1
                            elif pl_old_xWAR > pl_new_xWAR:
                                worse_count['Player'] += 1
                            else:
                                neutral_count['Player'] += 1

                            if mine:
                                crit_x_sign = "+" if old_crit_x < player.crit_x else ""
                                with open('off_season_report', 'a') as file:
                                    file.write(f"Critical X: {crit_x_sign}{player.crit_x - old_crit_x :.5f}\n")
                        else: #Critical Percentage
                            pl_old_xWAR = player.get_xWAR()
                            old_team_xWAR += pl_old_xWAR

                            old_crit_pct = player.crit_pct

                            player.crit_pct = round(player.crit_pct * x_over_one(factor, choice([2, 2, 3])), 4)

                            total_increment['Critical %'] += round((player.crit_pct - old_crit_pct), 2)
                            increment_count['Critical %'] += 1

                            pl_new_xWAR = player.get_xWAR()
                            player.xWAR = pl_new_xWAR
                            new_team_xWAR += player.get_xWAR()

                            total_xWAR_increment += (pl_new_xWAR - pl_old_xWAR)
                            total_xWAR_increment_count += 1

                            if pl_new_xWAR > pl_old_xWAR:
                                better_count['Player'] += 1
                            elif pl_old_xWAR > pl_new_xWAR:
                                worse_count['Player'] += 1
                            else:
                                neutral_count['Player'] += 1

                            if mine:
                                crit_pct_sign = "+" if old_crit_pct < player.crit_pct else ""
                                with open('off_season_report', 'a') as file:
                                    file.write(f"Critical %: {crit_pct_sign}{player.crit_pct - old_crit_pct :.5f}\n")




                elif coins[0] and not coins[1]:
                    #Heads and Tails, Attack Damage and Critical Multiplier
                    pl_old_xWAR = player.get_xWAR()
                    old_team_xWAR += pl_old_xWAR

                    old_atk_dmg = player.atk_dmg
                    old_crit_x = player.crit_x

                    player.atk_dmg = round(player.atk_dmg * half_to_one(factor))
                    player.crit_x = round(player.crit_x*factor, 3)

                    total_increment['Attack Damage'] += round((player.atk_dmg - old_atk_dmg),2)
                    total_increment['Critical X'] += round((player.crit_x - old_crit_x), 3)
                    increment_count['Attack Damage'] += 1
                    increment_count['Critical X'] += 1

                    pl_new_xWAR = player.get_xWAR()
                    player.xWAR = pl_new_xWAR
                    new_team_xWAR += player.get_xWAR()

                    total_xWAR_increment += (pl_new_xWAR - pl_old_xWAR)
                    total_xWAR_increment_count += 1

                    if pl_new_xWAR > pl_old_xWAR:
                        better_count['Player'] += 1
                    elif pl_old_xWAR > pl_new_xWAR:
                        worse_count['Player'] += 1
                    else:
                        neutral_count['Player'] += 1

                    if mine:
                        atk_dmg_sign = "+" if old_atk_dmg < player.atk_dmg else ""
                        crit_x_sign = "+" if old_crit_x < player.crit_x else ""
                        with open('off_season_report', 'a') as file:
                            file.write(f"Attack Damage: {atk_dmg_sign}{player.atk_dmg - old_atk_dmg :.5f}\n"
                                       f"Critical X: {crit_x_sign}{player.crit_x - old_crit_x :.5f}\n")
                    if extra_trait_roll >= chance_for_extra_trait:
                        ex_coin2 = choice([True,False])
                        if ex_coin2: #Health
                            pl_old_xWAR = player.get_xWAR()
                            old_team_xWAR += pl_old_xWAR

                            old_max_health = player.max_health

                            player.max_health = round(player.max_health * factor, 2) if factor < 1.2 else round(player.max_health * 1.2, 2)

                            total_increment['Health'] += round((player.max_health - old_max_health), 3)
                            increment_count['Health'] += 1

                            pl_new_xWAR = player.get_xWAR()
                            player.xWAR = pl_new_xWAR
                            new_team_xWAR += player.get_xWAR()

                            total_xWAR_increment += (pl_new_xWAR - pl_old_xWAR)
                            total_xWAR_increment_count += 1

                            if pl_new_xWAR > pl_old_xWAR:
                                better_count['Player'] += 1
                            elif pl_old_xWAR > pl_new_xWAR:
                                worse_count['Player'] += 1
                            else:
                                neutral_count['Player'] += 1

                            if mine:
                                max_health_sign = "+" if old_max_health < player.max_health else ""
                                with open('off_season_report', 'a') as file:
                                    file.write(f"Max Health: {max_health_sign}{player.max_health - old_max_health :.5f}\n")

                        else: #Critical Percentage
                            pl_old_xWAR = player.get_xWAR()
                            old_team_xWAR += pl_old_xWAR

                            old_crit_pct = player.crit_pct

                            player.crit_pct = round(player.crit_pct * x_over_one(factor, choice([2, 2, 3])), 4)

                            total_increment['Critical %'] += round((player.crit_pct - old_crit_pct), 2)
                            increment_count['Critical %'] += 1

                            pl_new_xWAR = player.get_xWAR()
                            player.xWAR = pl_new_xWAR
                            new_team_xWAR += player.get_xWAR()

                            total_xWAR_increment += (pl_new_xWAR - pl_old_xWAR)
                            total_xWAR_increment_count += 1

                            if pl_new_xWAR > pl_old_xWAR:
                                better_count['Player'] += 1
                            elif pl_old_xWAR > pl_new_xWAR:
                                worse_count['Player'] += 1
                            else:
                                neutral_count['Player'] += 1

                            if mine:
                                crit_pct_sign = "+" if old_crit_pct < player.crit_pct else ""
                                with open('off_season_report', 'a') as file:
                                    file.write(f"Critical %: {crit_pct_sign}{player.crit_pct - old_crit_pct :.5f}\n")

                elif not coins[0] and coins[1]:
                    #Tails and Heads, Critical Percentage and Health
                    pl_old_xWAR = player.get_xWAR()
                    old_team_xWAR += pl_old_xWAR

                    old_crit_pct = player.crit_pct
                    old_max_health = player.max_health

                    player.crit_pct = round(player.crit_pct * x_over_one(factor,choice([2,2,3])), 4)
                    player.max_health = round(player.max_health * factor, 2) if factor < 1.2 else round(player.max_health * 1.2, 2)

                    total_increment['Critical %'] += round((player.crit_pct - old_crit_pct), 2)
                    total_increment['Health'] += round((player.max_health - old_max_health), 3)
                    increment_count['Critical %'] += 1
                    increment_count['Health'] += 1

                    pl_new_xWAR = player.get_xWAR()
                    player.xWAR = pl_new_xWAR
                    new_team_xWAR += player.get_xWAR()

                    total_xWAR_increment += (pl_new_xWAR - pl_old_xWAR)
                    total_xWAR_increment_count += 1

                    if pl_new_xWAR > pl_old_xWAR:
                        better_count['Player'] += 1
                    elif pl_old_xWAR > pl_new_xWAR:
                        worse_count['Player'] += 1
                    else:
                        neutral_count['Player'] += 1

                    if mine:
                        crit_pct_sign = "+" if old_crit_pct < player.crit_pct else ""
                        max_health_sign = "+" if old_max_health < player.max_health else ""
                        with open('off_season_report', 'a') as file:
                            file.write(f"Critical %: {crit_pct_sign}{player.crit_pct - old_crit_pct :.5f}\n"
                                       f"Max Health: {max_health_sign}{player.max_health - old_max_health :.5f}\n")

                    if extra_trait_roll >= chance_for_extra_trait:
                        ex_coin3 = choice([True,False])
                        if ex_coin3: #Attack Damage
                            pl_old_xWAR = player.get_xWAR()
                            old_team_xWAR += pl_old_xWAR

                            old_atk_dmg = player.atk_dmg

                            player.atk_dmg = round(player.atk_dmg * half_to_one(factor))

                            total_increment['Attack Damage'] += round((player.atk_dmg - old_atk_dmg), 2)
                            increment_count['Attack Damage'] += 1

                            pl_new_xWAR = player.get_xWAR()
                            player.xWAR = pl_new_xWAR
                            new_team_xWAR += player.get_xWAR()

                            total_xWAR_increment += (pl_new_xWAR - pl_old_xWAR)
                            total_xWAR_increment_count += 1

                            if pl_new_xWAR > pl_old_xWAR:
                                better_count['Player'] += 1
                            elif pl_old_xWAR > pl_new_xWAR:
                                worse_count['Player'] += 1
                            else:
                                neutral_count['Player'] += 1

                            if mine:
                                atk_dmg_sign = "+" if old_atk_dmg < player.atk_dmg else ""
                                with open('off_season_report', 'a') as file:
                                    file.write(f"Attack Damage: {atk_dmg_sign}{player.atk_dmg - old_atk_dmg :.5f}\n")
                        else: #Critical X
                            pl_old_xWAR = player.get_xWAR()
                            old_team_xWAR += pl_old_xWAR

                            old_crit_x = player.crit_x

                            player.crit_x = round(player.crit_x * factor, 3)

                            total_increment['Critical X'] += round((player.crit_x - old_crit_x), 3)
                            increment_count['Critical X'] += 1

                            pl_new_xWAR = player.get_xWAR()
                            player.xWAR = pl_new_xWAR
                            new_team_xWAR += player.get_xWAR()

                            total_xWAR_increment += (pl_new_xWAR - pl_old_xWAR)
                            total_xWAR_increment_count += 1

                            if pl_new_xWAR > pl_old_xWAR:
                                better_count['Player'] += 1
                            elif pl_old_xWAR > pl_new_xWAR:
                                worse_count['Player'] += 1
                            else:
                                neutral_count['Player'] += 1

                            if mine:
                                crit_x_sign = "+" if old_crit_x < player.crit_x else ""
                                with open('off_season_report', 'a') as file:
                                    file.write(f"Critical X: {crit_x_sign}{player.crit_x - old_crit_x :.5f}\n")


                else:
                    #Tails and Tails, Critical Percentage and Critical Multiplier
                    pl_old_xWAR = player.get_xWAR()
                    old_team_xWAR += pl_old_xWAR

                    old_crit_pct = player.crit_pct
                    old_crit_x = player.crit_x

                    player.crit_pct = round(player.crit_pct * x_over_one(factor,choice([2,2,3])), 4)
                    player.crit_x = round(player.crit_x*factor, 3)

                    total_increment['Critical %'] += round((player.crit_pct - old_crit_pct), 2)
                    total_increment['Critical X'] += round((player.max_health - old_crit_x), 3)
                    increment_count['Critical %'] += 1
                    increment_count['Critical X'] += 1

                    pl_new_xWAR = player.get_xWAR()
                    player.xWAR = pl_new_xWAR
                    new_team_xWAR += player.get_xWAR()

                    total_xWAR_increment += (pl_new_xWAR - pl_old_xWAR)
                    total_xWAR_increment_count += 1

                    if pl_new_xWAR > pl_old_xWAR:
                        better_count['Player'] += 1
                    elif pl_old_xWAR > pl_new_xWAR:
                        worse_count['Player'] += 1
                    else:
                        neutral_count['Player'] += 1

                    if mine:
                        crit_pct_sign = "+" if old_crit_pct < player.crit_pct else ""
                        crit_x_sign = "+" if old_crit_x < player.crit_x else ""
                        with open('off_season_report', 'a') as file:
                            file.write(f"Critical %: {crit_pct_sign}{player.crit_pct - old_crit_pct :.5f}\n"
                                       f"Critical X: {crit_x_sign}{player.crit_x - old_crit_x :.5f}\n")

                    if extra_trait_roll >= chance_for_extra_trait:
                        ex_coin4 = choice([True,False])
                        if ex_coin4: #Attack Damage
                            pl_old_xWAR = player.get_xWAR()
                            old_team_xWAR += pl_old_xWAR

                            old_atk_dmg = player.atk_dmg

                            player.atk_dmg = round(player.atk_dmg * half_to_one(factor))

                            total_increment['Attack Damage'] += round((player.atk_dmg - old_atk_dmg), 2)
                            increment_count['Attack Damage'] += 1

                            pl_new_xWAR = player.get_xWAR()
                            player.xWAR = pl_new_xWAR
                            new_team_xWAR += player.get_xWAR()

                            total_xWAR_increment += (pl_new_xWAR - pl_old_xWAR)
                            total_xWAR_increment_count += 1

                            if pl_new_xWAR > pl_old_xWAR:
                                better_count['Player'] += 1
                            elif pl_old_xWAR > pl_new_xWAR:
                                worse_count['Player'] += 1
                            else:
                                neutral_count['Player'] += 1

                            if mine:
                                atk_dmg_sign = "+" if old_atk_dmg < player.atk_dmg else ""
                                with open('off_season_report', 'a') as file:
                                    file.write(f"Attack Damage: {atk_dmg_sign}{player.atk_dmg - old_atk_dmg :.5f}\n")
                        else: #Health
                            pl_old_xWAR = player.get_xWAR()
                            old_team_xWAR += pl_old_xWAR

                            old_max_health = player.max_health

                            player.max_health = round(player.max_health * factor, 2) if factor < 1.2 else round(player.max_health * 1.2, 2)

                            total_increment['Health'] += round((player.max_health - old_max_health), 3)
                            increment_count['Health'] += 1

                            pl_new_xWAR = player.get_xWAR()
                            player.xWAR = pl_new_xWAR
                            new_team_xWAR += player.get_xWAR()

                            total_xWAR_increment += (pl_new_xWAR - pl_old_xWAR)
                            total_xWAR_increment_count += 1

                            if pl_new_xWAR > pl_old_xWAR:
                                better_count['Player'] += 1
                            elif pl_old_xWAR > pl_new_xWAR:
                                worse_count['Player'] += 1
                            else:
                                neutral_count['Player'] += 1

                            if mine:
                                max_health_sign = "+" if old_max_health < player.max_health else ""
                                with open('off_season_report', 'a') as file:
                                    file.write(
                                        f"Max Health: {max_health_sign}{player.max_health - old_max_health :.5f}\n")






                if mine:
                    with open('off_season_report', 'a') as file:
                        file.write(f"New Stats: {str(player)}\n")
                player.crit_dmg = player.crit_x * player.atk_dmg
                level_out(player, mine)

                player.age += 1

            total_increment['Team xWAR'] += (new_team_xWAR - old_team_xWAR)
            increment_count['Team xWAR'] += 1

            if old_team_xWAR < new_team_xWAR:
                xWAR_sign = '+'
                better_count['Team'] += 1
            elif new_team_xWAR < old_team_xWAR:
                xWAR_sign = ''
                worse_count['Team'] += 1
            else:
                xWAR_sign = ''
                neutral_count['Team'] += 1

            if team.is_noteworthy:
                team.is_noteworthy = False
            if mine:
                with open('off_season_report', 'a') as file:
                    file.write(f"{team.name} Old xWAR: {old_team_xWAR}\nNew xWAR: {new_team_xWAR}\n{xWAR_sign}{new_team_xWAR - old_team_xWAR}\n\n")
        avg_factor = total_factor / factor_count

        with open('off_season_report', 'a') as file:
            file.write(f"Season No. {season_count}\n"
                       f"Average Player Change Factor: {avg_factor}\n"
                       f"Of {factor_count} players receiving changes, {better_count['Player']} players improved, while {worse_count['Player']} players got worse, and {neutral_count['Player']} did not change.\n"
                       f"Average PLAYER xWAR Increment: {total_xWAR_increment / total_xWAR_increment_count:.4f}\n"
                       f"Of {increment_count['Team xWAR']} teams, {better_count['Team']} improved, while {worse_count['Team']} got worse, and {neutral_count['Team']} did not change.\n"
                       f"Average TEAM xWAR Increment: {total_increment['Team xWAR'] / increment_count['Team xWAR']:.4f}\n")
            for key in ['Attack Damage', 'Health', 'Critical %', 'Critical X']:
                avg_increment[key] = total_increment[key] / increment_count[key]
                file.write(f"Average {key} Increment: {avg_increment[key]:.4f} per player ({increment_count[key]} total players affected).\n")
            file.write('\n')


def single_elim_16(t, r1_thresh=200, r2_thresh=250, r3_thresh=300, final_thresh=400, is_relegation=False, upset_list = None, upset_count = None, region = 'Universal', season_count=-1):


    m1, m2, m3, mF = 60, 65, 75, 90

    sk1, sk2, sk3, skF = [100,85], [125, 100], [140,110], [200,160]
    # skunk thresh and margin

    one, two, three, four, five, six, seven, eight = t[0], t[1], t[2], t[3], t[4], t[5], t[6], t[7]
    nine, ten, eleven, twelve, thirteen, fourteen, fifteen, sixteen = t[8], t[9], t[10], t[11], t[12], t[13], t[14], t[15]

    one.seed, two.seed, three.seed, four.seed, five.seed, six.seed, seven.seed, eight.seed, nine.seed, ten.seed, eleven.seed, twelve.seed, thirteen.seed, fourteen.seed, fifteen.seed, sixteen.seed = 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16
    print(Fore.RED + "UNIVERSAL PLAYOFFS" + Fore.RESET)

    print(Fore.GREEN + f"ROUND ONE (to {r1_thresh} / by {m1})" + Fore.RESET)
    context = f"S{season_count} Universal Playoffs, Round of 16"
    w1, l1 = best_of(one, sixteen, r1_thresh, 10, True, m1, test_output=True, is_uni=not is_relegation,
                     upset_list=upset_list, upset_count=upset_count, context=context, skunk=sk1)
    w2, l2 = best_of(eight, nine, r1_thresh, 10, True, m1, test_output=True, is_uni=not is_relegation,
                     upset_list=upset_list, upset_count=upset_count, context=context, skunk=sk1)
    w3, l3 = best_of(five, twelve, r1_thresh, 10, True, m1, test_output=True, is_uni=not is_relegation,
                     upset_list=upset_list, upset_count=upset_count, context=context, skunk=sk1)
    w4, l4 = best_of(four, thirteen, r1_thresh, 10, True, m1, test_output=True, is_uni=not is_relegation,
                     upset_list=upset_list, upset_count=upset_count, context=context, skunk=sk1)
    w5, l5 = best_of(three, fourteen, r1_thresh, 10, True, m1, test_output=True, is_uni=not is_relegation,
                     upset_list=upset_list, upset_count=upset_count, context=context, skunk=sk1)
    w6, l6 = best_of(six, eleven, r1_thresh, 10, True, m1, test_output=True, is_uni=not is_relegation,
                     upset_list=upset_list, upset_count=upset_count, context=context, skunk=sk1)
    w7, l7 = best_of(seven, ten, r1_thresh, 10, True, m1, test_output=True, is_uni=not is_relegation,
                     upset_list=upset_list, upset_count=upset_count, context=context, skunk=sk1)
    w8, l8 = best_of(two, fifteen, r1_thresh, 10, True, m1, test_output=True, is_uni=not is_relegation,
                     upset_list=upset_list, upset_count=upset_count, context=context, skunk=sk1)
    out1 = sorted([l1, l2, l3, l4, l5, l6, l7, l8], key=lambda x: x.seed)

    print(Fore.GREEN + f"QUARTERFINALS (to {r2_thresh} / by {m2})" + Fore.RESET)
    context = f"S{season_count} Universal Playoffs, Quarterfinals"

    r2_actual = [w1, w2, w3, w4, w5, w6, w7, w8]
    r2_seeded = r2_actual      #sorted([w1, w2, w3, w4, w5, w6, w7, w8], key=lambda x: x.seed) to sort by seed

    w9, l9 = best_of(r2_seeded[0], r2_seeded[1], r2_thresh, 11, True, m2, test_output=True, is_uni=not is_relegation,
                       upset_list=upset_list, upset_count=upset_count, context=context, skunk=sk2)
    w10, l10 = best_of(r2_seeded[2], r2_seeded[3], r2_thresh, 11, True, m2, test_output=True, is_uni=not is_relegation,
                       upset_list=upset_list, upset_count=upset_count, context=context, skunk=sk2)
    w11, l11 = best_of(r2_seeded[4], r2_seeded[5], r2_thresh, 11, True, m2, test_output=True, is_uni=not is_relegation,
                       upset_list=upset_list, upset_count=upset_count, context=context, skunk=sk2)
    w12, l12 = best_of(r2_seeded[6], r2_seeded[7], r2_thresh, 11, True, m2, test_output=True, is_uni=not is_relegation,
                       upset_list=upset_list, upset_count=upset_count, context=context, skunk=sk2)
    out2 = sorted([l9, l10, l11, l12], key=lambda x: x.seed)

    print(Fore.GREEN + f"SEMIFINALS (to {r3_thresh} / by {m3})" + Fore.RESET)
    context = f"S{season_count} Universal Playoffs, Semifinals"

    r3_actual = [w9, w10, w11, w12]
    r3_seeded = r3_actual  #sorted([w9, w10, w11, w12], key=lambda x: x.seed) to re-seed

    w13, l13 = best_of(r3_seeded[0], r3_seeded[1], r3_thresh, 11, True, m3, test_output=True, is_uni=not is_relegation,
                     upset_list=upset_list, upset_count=upset_count, context=context, skunk=sk3)
    w14, l14 = best_of(r3_seeded[2], r3_seeded[3], r3_thresh, 11, True, m3, test_output=True, is_uni=not is_relegation,
                       upset_list=upset_list, upset_count=upset_count, context=context, skunk=sk3)
    out3 = sorted([l13, l14], key=lambda x: x.seed)

    print(Fore.GREEN + f"FINALS (to {final_thresh} / by {mF})" + Fore.RESET)
    context = f"S{season_count} Universal Playoffs, Finals"

    champ, outFinal = best_of(w13, w14, final_thresh, 12, True, mF, test_output=True, is_uni=not is_relegation,
                              upset_list=upset_list, upset_count=upset_count, context=context, skunk=skF)

    return champ, outFinal, out3[0], out3[1], out2[0], out2[1], out2[2], out2[3], out1[0], out1[1], out1[2], out1[3], out1[4], out1[5], out1[6], out1[7]

def double_elim_12(t, upset_list = None, upset_count = None, region = None, season_count=-1):
    #t = teams // out1-out3 should contain the lists of teams which lose in the respective round of the loser bracket

    r1_thresh, r2_thresh, r3_thresh, r4_thresh, final_thresh = 32, 35, 38, 42, 50
    r1_margin, r2_margin, r3_margin, r4_margin, final_margin = 15, 16, 17, 18, 20

    if region == "Universal":
        for n in [r1_thresh, r2_thresh, r3_thresh, r4_thresh, final_thresh,r1_margin, r2_margin, r3_margin, r4_margin, final_margin]:
            n -= 5

    sk1, sk2, sk3, sk4, skF = [20,16], [23,18], [26,20], [30,23], [40,31]
    out1 = []
    out2 = []
    out3 = []
    # out1-out3 lists are in descending order, so better seeds come last
    # out_finals is in order from when they were eliminated, as there are 3 different teams which will be eliminated in the finals

    one, two, three, four, five, six, seven, eight, nine, ten, eleven, twelve = t[0], t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[8], t[9], t[10], t[11]

    print(Fore.GREEN + f"R1 winner bracket (to {r1_thresh} / by {r1_margin})" + Fore.RESET)
    context = f"S{season_count} R1W {region} Playoffs"
    w1, l1 = best_of(eight, nine, r1_thresh, both_return=True, win_by=r1_margin, upset_list=upset_list, upset_count=upset_count,context=context,skunk=sk1)
    w2, l2 = best_of(five, twelve, r1_thresh, both_return=True, win_by=r1_margin, upset_list=upset_list, upset_count=upset_count,context=context,skunk=sk1)
    w3, l3 = best_of(six, eleven, r1_thresh, both_return=True, win_by=r1_margin, upset_list=upset_list, upset_count=upset_count,context=context,skunk=sk1)
    w4, l4 = best_of(seven, ten, r1_thresh, both_return=True, win_by=r1_margin, upset_list=upset_list, upset_count=upset_count,context=context,skunk=sk1)

    print(Fore.GREEN + f"R2 winner bracket (to {r2_thresh} / by {r2_margin})" + Fore.RESET)
    context = f"S{season_count} R2W {region} Playoffs"
    w5, l5 = best_of(one, w1, r2_thresh, both_return=True, win_by=r2_margin, upset_list=upset_list,
                     upset_count=upset_count, context=context,skunk=sk2)
    w6, l6 = best_of(four, w2, r2_thresh, both_return=True, win_by=r2_margin, upset_list=upset_list,
                     upset_count=upset_count, context=context,skunk=sk2)
    w7, l7 = best_of(three, w3, r2_thresh, both_return=True, win_by=r2_margin, upset_list=upset_list,
                     upset_count=upset_count, context=context,skunk=sk2)
    w8, l8 = best_of(two, w4, r2_thresh, both_return=True, win_by=r2_margin, upset_list=upset_list,
                     upset_count=upset_count, context=context,skunk=sk2)

    print(Fore.GREEN + f"R1 loser bracket (to {r1_thresh} / by {r1_margin-2})" + Fore.RESET)
    context = f"S{season_count} R1L {region} Playoffs"

    #no upsets: l3: 11 seed, l6: five seed, l4: ten seed, l5: eight seed, l1: nine seed, l8: seven seed, l2: twelve seed, l7: six seed

    w9, l9 = best_of(l6,l3, r1_thresh, both_return=True, win_by=r1_margin-2, upset_list=upset_list,
                     upset_count=upset_count, context=context,advantage=5,skunk=sk1)
    w10, l10 = best_of(l5,l4, r1_thresh, both_return=True, win_by=r1_margin-2, upset_list=upset_list,
                     upset_count=upset_count, context=context,advantage=5,skunk=sk1)
    w11, l11 = best_of(l8,l1, r1_thresh, both_return=True, win_by=r1_margin-2, upset_list=upset_list,
                     upset_count=upset_count, context=context,advantage=5,skunk=sk1)
    w12, l12 = best_of(l7,l2, r1_thresh, both_return=True, win_by=r1_margin-2, upset_list=upset_list,
                     upset_count=upset_count, context=context,advantage=5,skunk=sk1)
    out1 = sorted([l9, l10, l11, l12], key=lambda x: x.seed, reverse=True)

    print(Fore.GREEN + f"R3 winner bracket (to {r3_thresh} / by {r3_margin})" + Fore.RESET)
    context = f"S{season_count} R3W {region} Playoffs"
    w13, l13 = best_of(w5, w6, r3_thresh, both_return=True, win_by=r3_margin, test_output=True, upset_list=upset_list,
                     upset_count=upset_count, context=context,skunk=sk3)
    w14, l14 = best_of(w7, w8, r3_thresh, both_return=True, win_by=r3_margin, test_output=True, upset_list=upset_list,
                     upset_count=upset_count, context=context,skunk=sk3)

    print(Fore.GREEN + f"R2 loser bracket (to {r2_thresh} / by {r2_margin-2})" + Fore.RESET)
    context = f"S{season_count} R2L {region} Playoffs"
    w15, l15 = best_of(w9, w10, r2_thresh, both_return=True, win_by=r2_margin-2, test_output=True, upset_list=upset_list,
                     upset_count=upset_count, context=context,skunk=sk2)
    w16, l16 = best_of(w11, w12, r2_thresh, both_return=True, win_by=r2_margin-2, test_output=True, upset_list=upset_list,
                       upset_count=upset_count, context=context,skunk=sk2)
    out2 = sorted([l15, l16], key=lambda x: x.seed, reverse=True)

    print(Fore.GREEN + f"R3 loser bracket (to {r3_thresh} / by {r3_margin-2})" + Fore.RESET)
    context = f"S{season_count} R3L {region} Playoffs"
    w17, l17 = best_of(l14, w15, r3_thresh, both_return=True, win_by=r3_margin-2, test_output=True, upset_list=upset_list,
                       upset_count=upset_count, context=context,skunk=sk3)
    w18, l18 = best_of(l13, w16, r3_thresh, both_return=True, win_by=r3_margin-2, test_output=True, upset_list=upset_list,
                       upset_count=upset_count, context=context,skunk=sk3)
    out3 = sorted([l17, l18], key=lambda x: x.seed, reverse=True)

    print(Fore.GREEN + f"winner bracket finals (to {r4_thresh} / by {r4_margin})")
    context = f"S{season_count} WB Finals {region} Playoffs"
    w19, l19 = best_of(w13, w14, r4_thresh, both_return=True, win_by=r4_margin, test_output=True, upset_list=upset_list,
                       upset_count=upset_count, context=context,skunk=sk4)

    print(Fore.GREEN + f"loser bracket finals (to {r4_thresh} / by {r4_margin-2})")
    context = f"S{season_count} LB Finals {region} Playoffs"
    w20, out_fourth = best_of(w17, w18, r4_thresh, both_return=True, win_by=r4_margin-2, test_output=True, upset_list=upset_list,
                       upset_count=upset_count, context=context,skunk=sk4)

    print(Fore.GREEN + f"winner bracket finals loser vs loser bracket champ (to {r4_thresh} / by {r4_margin-2})" + Fore.RESET)
    context = f"S{season_count} WBFL v LBC {region} Playoffs"
    w21, out_third = best_of(w20, l19, r4_thresh, both_return=True, win_by=r4_margin, test_output=True, upset_list=upset_list,
                       upset_count=upset_count, context=context,skunk=sk4)
    print(Fore.GREEN + f"grand finals (to {final_thresh} / by {final_margin})" + Fore.RESET)
    context = f"S{season_count} Grand Finals {region} Playoffs"
    w22 = best_of(w19, w21, final_thresh, both_return=False, win_by=final_margin, test_output=True, upset_list=upset_list,
                       upset_count=upset_count, context=context,skunk=skF)
    if w22 == w19:
        print(Fore.GREEN + f"{w22.name} are flawless." + Fore.RESET)
        champ = w22
        runner_up = w21
    else:
        print(Fore.GREEN + f"{w19.name} has only lost once. {w21.full_name} must win again." + Fore.RESET)
        champ, runner_up = best_of(w19, w21, final_thresh, both_return=True, win_by=final_margin, test_output=True, upset_list=upset_list,
                       upset_count=upset_count, context=context,skunk=skF)

    playoff_standings = out1 + out2 + out3 + [out_fourth, out_third, runner_up, champ]
    return playoff_standings[0], playoff_standings[1], playoff_standings[2], playoff_standings[3],\
        playoff_standings[4], playoff_standings[5], playoff_standings[6], playoff_standings[7],\
        playoff_standings[8], playoff_standings[9], playoff_standings[10], playoff_standings[11]




def double_elim_16(t, r1_thresh=40, r2_thresh=40, r3_thresh=50, r4_thresh=55, final_thresh=60, is_relegation=False, upset_list = None, upset_count = None, region = 'Universal', season_count=-1):

    out1 = [0,0,0,0]
    out2 = [0,0,0,0]
    out3 = [0,0]
    out4 = [0,0]


    m1,m2,m3,m4,mF,mGF = 11, 12, 15, 18, 21, 21

    one, two, three, four, five, six, seven, eight = t[0], t[1], t[2], t[3], t[4], t[5], t[6], t[7]
    nine, ten, eleven, twelve, thirteen, fourteen, fifteen, sixteen = t[8], t[9], t[10], t[11], t[12], t[13], t[14], t[15]
    if is_relegation:
        one.seed, two.seed, three.seed, four.seed, five.seed, six.seed, seven.seed, eight.seed, nine.seed, ten.seed, eleven.seed, twelve.seed, thirteen.seed, fourteen.seed, fifteen.seed, sixteen.seed = 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30
        print(Fore.RED + "RELEGATION TOURNAMENT" + Fore.RESET)
    else:
        one.seed, two.seed, three.seed, four.seed, five.seed, six.seed, seven.seed, eight.seed, nine.seed, ten.seed, eleven.seed, twelve.seed, thirteen.seed, fourteen.seed, fifteen.seed, sixteen.seed = 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16
        print(Fore.RED + "UNIVERSAL PLAYOFFS" + Fore.RESET)
    print(Fore.GREEN + "R1 winner bracket" + Fore.RESET)
    context = f"S{season_count} R1W {region} "
    if is_relegation:
        context += "Relegation Tournament"
    else:
        context += "Playoffs"
    w1, l1 = best_of(one, sixteen, r1_thresh,10,True,m1,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    w2, l2 = best_of(eight, nine, r1_thresh,10,True,m1,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    w3, l3 = best_of(five, twelve, r1_thresh,10,True,m1,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    w4, l4 = best_of(four, thirteen, r1_thresh,10,True,m1,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    w5, l5 = best_of(three, fourteen, r1_thresh,10,True,m1,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    w6, l6 = best_of(six, eleven, r1_thresh,10,True,m1,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    w7, l7 = best_of(seven, ten, r1_thresh,10,True,m1,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    w8, l8 = best_of(two, fifteen, r1_thresh,10,True,m1,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    print(Fore.GREEN + "R1 loser bracket" + Fore.RESET)
    context = f"S{season_count} R1L {region} "
    if is_relegation:
        context += "Relegation Tournament"
    else:
        context += "Playoffs"
    w9, out1[0] = best_of(l1, l2, r1_thresh, 10, True,m1,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    w10, out1[1] = best_of(l3, l4, r1_thresh, 10,True,m1,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    w11, out1[2] = best_of(l5, l6, r1_thresh, 10, True,m1,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    w12, out1[3] = best_of(l7, l8, r1_thresh, 10, True,m1,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    print(Fore.GREEN + "R2 winner bracket" + Fore.RESET)
    context = f"S{season_count} R2W {region} "
    if is_relegation:
        context += "Relegation Tournament"
    else:
        context += "Playoffs"
    w13, l13 = best_of(w1, w2, r2_thresh, 11, True,m2,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    w14, l14 = best_of(w3, w4, r2_thresh, 11, True,m2,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    w15, l15 = best_of(w5, w6, r2_thresh, 11, True,m2,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    w16, l16 = best_of(w7, w8, r2_thresh, 11, True,m2,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    print(Fore.GREEN + "R2 loser bracket" + Fore.RESET)
    context = f"S{season_count} R2L {region} "
    if is_relegation:
        context += "Relegation Tournament"
    else:
        context += "Playoffs"
    w17, out2[0] = best_of(w9, l16, r2_thresh, 10, True,m2,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    w18, out2[1] = best_of(w10, l15, r2_thresh, 10, True,m2,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    w19, out2[2] = best_of(w11, l14, r2_thresh, 10, True,m2,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    w20, out2[3] = best_of(w12, l13, r2_thresh, 10, True,m2,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    print(Fore.GREEN + "R3 winner bracket" + Fore.RESET)
    context = f"S{season_count} R3W {region} "
    if is_relegation:
        context += "Relegation Tournament"
    else:
        context += "Playoffs"
    w21, l21 = best_of(w13, w14, r3_thresh, 12, True,m3,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    w22, l22 = best_of(w15, w16, r3_thresh, 12, True,m3,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    print(Fore.GREEN + "R3 loser bracket" + Fore.RESET)
    context = f"S{season_count} R3L {region} "
    if is_relegation:
        context += "Relegation Tournament"
    else:
        context += "Playoffs"
    w23, out3[0] = best_of(w17, w18, r3_thresh, 10, True,m3,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    w24, out3[1] = best_of(w19, w20, r3_thresh, 10, True,m3,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    print(Fore.GREEN + "R4 loser bracket" + Fore.RESET)
    context = f"S{season_count} R4L {region} "
    if is_relegation:
        context += "Relegation Tournament"
    else:
        context += "Playoffs"

    r4l = [l22, l21, w24, w23]
    r4l_seeded = sorted(r4l, key= lambda x: x.seed)

    w25, out4[0] = best_of(r4l_seeded[0], r4l_seeded[3], r4_thresh, 10, True,m4,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    w26, out4[1] = best_of(r4l_seeded[1], r4l_seeded[2], r4_thresh, 10, True,m4,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    print(Fore.GREEN + "winner bracket finals" + Fore.RESET)
    context = f"S{season_count} WB Finals {region} "
    if is_relegation:
        context += "Relegation Tournament"
    else:
        context += "Playoffs"
    w27, l27 = best_of(w21, w22, r4_thresh, 13, True,mF,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    print(Fore.GREEN + "loser bracket finals" + Fore.RESET)
    context = f"S{season_count} LB Finals {region} "
    if is_relegation:
        context += "Relegation Tournament"
    else:
        context += "Playoffs"
    w28, out5 = best_of(w25, w26, r4_thresh, 10, True,mF,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    print(Fore.GREEN + "winner bracket finals LOSER vs loser bracket champ" + Fore.RESET)
    context = f"S{season_count} WBFL v LBC {region} "
    if is_relegation:
        context += "Relegation Tournament"
    else:
        context += "Playoffs"
    w29, out6 = best_of(w28, l27, r4_thresh, 13, True,mF,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    print(Fore.GREEN + "grand finals" + Fore.RESET)
    context = f"S{season_count} Grand Finals {region} "
    if is_relegation:
        context += "Relegation Tournament"
    else:
        context += "Playoffs"
    w30, out7 = best_of(w27, w29, final_thresh, 14, True,mGF,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
    if w30 == w27:
        print(Fore.GREEN + f"{w30.full_name} are flawless." + Fore.RESET)
        champ = w30
    else:
        print(Fore.GREEN + f"{w27.full_name} has only lost once. {w29.full_name} must win again." + Fore.RESET)
        w31, out7 = best_of(w27, w29, final_thresh, 14, True,mGF+1,test_output=True,is_uni=not is_relegation,upset_list=upset_list,upset_count=upset_count,context=context)
        champ = w31
    out1.sort(key = lambda t : t.seed)
    out2.sort(key=lambda t: t.seed)
    out3.sort(key=lambda t: t.seed)
    out4.sort(key=lambda t: t.seed)
    return champ, out7, out6, out5, out4[0], out4[1], out3[0], out3[1], out2[0], out2[1], out2[2], out2[3], out1[0], out1[1], out1[2], out1[3]


def double_elim_8(t,r1_thresh=30, r2_thresh=30, r3_thresh=35, r4_thresh=40, final_thresh=50, upset_list = None, upset_count = None, region = None, season_count=-1):
    out_1 = []
    out_2 = []

    r1_margin, r2_margin, r3_margin, r4_margin, final_margin = round(r1_thresh/5)+6, round(r2_thresh/5)+6, round(r3_thresh/5)+6, round(r4_thresh/5)+7, round(final_thresh/5)+10

    one, two, three, four, five, six, seven, eight = t[0], t[1], t[2], t[3], t[4], t[5], t[6], t[7]
    one.seed, two.seed, three.seed, four.seed, five.seed, six.seed, seven.seed, eight.seed = 1, 2, 3, 4, 5, 6, 7, 8
    print(Fore.GREEN + "R1 winner bracket" + Fore.RESET)
    context = f"S{season_count} R1W {region} Playoffs"
    w1, l1 = best_of(one, eight, r1_thresh,3, True,r1_margin, upset_list=upset_list,upset_count=upset_count,context=context)
    w2, l2 = best_of(four, five, r1_thresh,3,True,r1_margin, upset_list=upset_list,upset_count=upset_count,context=context)
    w3, l3 = best_of(three, six, r1_thresh,3,True,r1_margin, upset_list=upset_list,upset_count=upset_count,context=context)
    w4, l4 = best_of(two, seven, r1_thresh,3,True,r1_margin, upset_list=upset_list,upset_count=upset_count,context=context)
    print(Fore.GREEN + "R1 loser bracket" + Fore.RESET)
    context = f"S{season_count} R1L {region} Playoffs"
    w5, out_temp = best_of(l1, l2, r1_thresh-2, 3, True,r1_margin-2, upset_list=upset_list,upset_count=upset_count,context=context)
    out_1.append(out_temp)
    w6, out_temp = best_of(l3, l4, r1_thresh-2, 3, True,r1_margin-2, upset_list=upset_list,upset_count=upset_count,context=context)
    out_1.append(out_temp)
    print(Fore.GREEN + "R2 winner bracket" + Fore.RESET)
    context = f"S{season_count} R2W {region} Playoffs"
    w7, l7 = best_of(w1, w2, r2_thresh, 4, True,r2_margin, upset_list=upset_list,upset_count=upset_count,context=context)
    w8, l8 = best_of(w3, w4, r2_thresh, 4, True,r2_margin, upset_list=upset_list,upset_count=upset_count,context=context)
    print(Fore.GREEN + "R2 loser bracket" + Fore.RESET)
    context = f"S{season_count} R2L {region} Playoffs"
    w9, out_temp = best_of(w5, l8, r2_thresh-2, 4, True,r2_margin-2, upset_list=upset_list,upset_count=upset_count,context=context)
    out_2.append(out_temp)
    w10, out_temp = best_of(w6, l7, r2_thresh-2, 4, True,r2_margin-2, upset_list=upset_list,upset_count=upset_count,context=context)
    out_2.append(out_temp)
    print(Fore.GREEN + "winner bracket finals" + Fore.RESET)
    context = f"S{season_count} WB Finals {region} Playoffs"
    w11, l11 = best_of(w7, w8, r3_thresh, 5, True,r3_margin,test_output=True, upset_list=upset_list,upset_count=upset_count,context=context)
    print(Fore.GREEN + "loser bracket finals" + Fore.RESET)
    context = f"S{season_count} LB Finals {region} Playoffs"
    w12, out_final = best_of(w9, w10, r3_thresh-2, 5, True,r3_margin-2,test_output=True, upset_list=upset_list,upset_count=upset_count,context=context)
    print(Fore.GREEN + "winner bracket finals loser vs loser bracket champ" + Fore.RESET)
    context = f"S{season_count} WBFL v LBC {region} Playoffs"
    w13, out_third = best_of(w12, l11, r4_thresh, 5, True,r4_margin,test_output=True, upset_list=upset_list,upset_count=upset_count,context=context)
    print(Fore.GREEN + "grand finals" + Fore.RESET)
    context = f"S{season_count} Grand Finals {region} Playoffs"
    w14 = best_of(w11, w13, final_thresh, 6, False,final_margin,test_output=True, upset_list=upset_list,upset_count=upset_count,context=context)
    if w14 == w11:
        print(Fore.GREEN + f"{w14.name} are flawless." + Fore.RESET)
        champ = w14
        runner_up = w13
    else:
        print(Fore.GREEN + f"{w11.name} has only lost once. {w13.full_name} must win again." + Fore.RESET)
        champ, runner_up = best_of(w11, w13, final_thresh, 6, True,final_margin+1,test_output=True, upset_list=upset_list,upset_count=upset_count,context=context)
    out_1.sort(key=lambda x: x.seed, reverse=False)
    out_2.sort(key=lambda x: x.seed, reverse=False)
    s = [out_1[1], out_1[0], out_2[1], out_2[0], out_final, out_third, runner_up, champ]
    return s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7]

def swiss_format(teams, base_thresh, base_margin, win_thresh=3, season_count=0):
    advanced = []
    eliminated = []

    swiss_start_time = time()

    def parse_region_seed(team):
        # Split the region_seed into letters and integer
        region, seed = team.region_seed.split('-')
        return region, int(seed)


    def swiss_round(wins, losses):
        #note that 2 is the highest seed, and 8 is the lowest seed

        print(Fore.RED + f"ROUND ({wins},{losses})" + Fore.RESET)
        while len(league_records[(wins,losses)]) >= 2:
            round_thresh = base_thresh + wins + losses
            round_margin = base_margin

            remaining_seeds = [parse_region_seed(team)[1] for team in league_records[(wins,losses)]]
            high_seed = min(remaining_seeds)
            low_seed = max(remaining_seeds)
            low_seed_teams = [team for team in league_records[(wins,losses)] if parse_region_seed(team)[1] == low_seed]
            high_seed_teams = [team for team in league_records[(wins,losses)] if parse_region_seed(team)[1] == high_seed]

            #new function should select random team of the highest remaining seed
            #select opponent which is the lowest remaining seed not from the same region

            cont1 = choice(high_seed_teams)
            #randomly chooses team 1 from the group
            league_records[(wins, losses)].remove(cont1)
            cont2 = choice(low_seed_teams)
            for team in low_seed_teams:
                if team.region != cont1.region:
                    cont2 = team
                    break
                else:
                    cont2 = choice(low_seed_teams)
                    while cont2.name == cont1.name:
                        cont2 = choice(low_seed_teams)
            #randomly chooses team 2 from the group
            winner, loser = best_of(cont1, cont2, thresh=round_thresh, amp=4, both_return=True, win_by=round_margin, context=f"S{season_count} Pre-Qualifying ({wins},{losses})")
            league_records[(wins, losses)].remove(cont2)
            if wins+1 < win_thresh:
                league_records[(wins+1, losses)].append(winner)
            elif wins+1 == win_thresh:
                print(Fore.GREEN + f"{winner.name} advance." + Fore.RESET)
                advanced.append(winner)
            if losses+1 < win_thresh:
                league_records[(wins, losses+1)].append(loser)
            elif losses+1 == win_thresh:
                print(Fore.GREEN + f"{loser.name} are eliminated." + Fore.RESET)
                eliminated.append(loser)


    league_records = {} # keys = list which contains wins and losses
    # values are lists of teams which have that record
    for j in range(0,win_thresh):
        for i in range(0,win_thresh):
            league_records[(i,j)] = []
    league_records[(0, 0)] = teams.copy()
    for j in range(0,win_thresh):
        for i in range(0,win_thresh):
            swiss_round(i,j)

    swiss_end_time = time()
    with open('execution_time', 'a') as file:
        file.write(f"Season {season_count} Pre-Qualifying Execution Time: {round((swiss_end_time-swiss_start_time)/60)} minutes, {round(((swiss_end_time-swiss_start_time)%60),2)} seconds.\n")

    return advanced, eliminated



def league_season(TEAMS,use_saved=False,season_count=-1,final_reversed=True,region='Universal', stats_list=None, upset_list = None, upset_count = None, champ_list=None,franchise_mode=False):
    # the stats_list parameter will take in a dictionary with keys of season numbers and values of lists of
    #player seasons, with one object for each player in that league
    #after edits, this function will create a key in that dictionary corresponding to season_count
    #and a list value with all the players' REGULAR SEASON statistics as a value

    season_start_time = time()

    cyan_seeds, yellow_seeds, red_seeds = [], [], []

    missed_playoffs = []
    play_in = []
    dumpster_fire = []
    coach_hot_seat = []

    if use_saved:
        TEAMS = load_pkl()
    if len(TEAMS) >= 30:
        post_range = 16
        chain_range = 8
    elif len(TEAMS) == 26:
        post_range = 12
        chain_range = None
    elif len(TEAMS) == 22:
        post_range = 12
        chain_range = None
    else: #should never happen
        post_range = None
        chain_range = None
    # see scratch_paper notes on relegation chain
    sub_season = f"{region} Regular Season"



    if region == 'Universal':
        for tm in TEAMS:
            tm.accolades['Universal-League'] += 1

        if chain_range: #season 1+ universal league
            postseason, relegation_chain = round_robin(TEAMS, r=5, qualify_range=post_range, alt_qualify_range=chain_range,franchise_mode=True,
                                                       cyan_seeds=[c for c in range(16)],
                                                       yellow_seeds=[y for y in range(16,24)],
                                                       red_seeds=[r for r in range(24,len(TEAMS))])
        else: #season 0 universal league
            postseason = round_robin(TEAMS, 1, qualify_range=post_range,franchise_mode=True,
                                                       cyan_seeds=[c for c in range(12)],
                                                       red_seeds=[r for r in range(10,len(TEAMS))])
            relegation_chain = None
    else: #regional league
        postseason = round_robin(TEAMS, 1.5, qualify_range=post_range,franchise_mode=True,
                                                       cyan_seeds=[c for c in range(12)],
                                                       red_seeds=[r for r in range(12,len(TEAMS))])
        relegation_chain = None

    for team in TEAMS:

        if team not in postseason:
            if chain_range:
                if team in relegation_chain:
                    team.history[season_count] += f" {ordinal_string(team.seed)} in Universal League -> Relegation Match."
                else:
                    team.history[season_count] += f" {ordinal_string(team.seed)} in Universal League -> S_{season_count+1} Universal Qualifying."
                    missed_playoffs.append(team)
            else:
                missed_playoffs.append(team)
                team.history[season_count] += f" {ordinal_string(team.seed)} in {region} League, missed playoffs."
                team.second_pick = choice([0,2,2,2,2,2,3,3])
                if team.seed == 20 or team.seed == 21 or team.seed == 22:
                    dumpster_fire.append(team)
                if team.seed in range(13,23):
                    coach_hot_seat.append(team)

    if post_range in [10, 12]:
        one, two, three, four, five, six, seven, eight, nine, ten, eleven, twelve = postseason[0], postseason[1], postseason[2], postseason[3], postseason[4], postseason[5], postseason[6], postseason[7], postseason[8], postseason[9], postseason[10], postseason[11]

        playoff_one = [one, two, three, four, five, six, seven, eight, nine, ten, eleven, twelve]

        if season_count == 0 and region == "Universal":
            twelfth, eleventh, tenth, ninth, eighth, seventh, sixth, fifth, fourth, third, second, champ = twelve,eleven,ten,nine,eight,seven,six,five,four,three,two,one
        else:
            twelfth, eleventh, tenth, ninth, eighth, seventh, sixth, fifth, fourth, third, second, champ = double_elim_12(
                playoff_one,upset_list=upset_list,upset_count=upset_count,region=region, season_count=season_count)



        for team in playoff_one:
            team.accolades['Regional-Playoffs'] += 1

        champ.accolades['Regional-Champ'] += 1
        playoff_standings = [champ, second, third, fourth, fifth, sixth, seventh, eighth, ninth, tenth, eleventh, twelfth]

    #new relegation standings: 15, 16 (regular season seeds), winners of play-in matchups (17/24, 18/23, 19/22, 20/21) sorted by seed, play-in losers (sorted by seed), 25-30 (regular season)
    # chain_range is 8 in the universal league, meaning relegation chain contains teams 17-24 and all other teams are added to missed_playoffs



    elif post_range == 16 or post_range == 14 or chain_range:
        print(Fore.GREEN + "Relegation Matches" + Fore.RESET)


        advantage_17v24 = relegation_chain[0].points - relegation_chain[7].points
        upi_g1W, upi_g1L = best_of( relegation_chain[0], relegation_chain[7],
                                     thresh=120, win_by=32,
                                     both_return=True, upset_list=upset_list, upset_count=upset_count,
                                     context=f"S{season_count} Relegation Match (17v24)", advantage=advantage_17v24
        )
        upi_g1W.history[season_count] += f" Won 17/24 Relegation Match -> S{season_count+1} Universal League."
        upi_g1L.history[season_count] += f" Lost 17/24 Relegation Match -> S{season_count + 1} Universal Qualifying."

        advantage_18v23 = relegation_chain[1].points - relegation_chain[6].points
        upi_g2W, upi_g2L = best_of(relegation_chain[1], relegation_chain[6],
                                   thresh=120, win_by=32,
                                   both_return=True, upset_list=upset_list, upset_count=upset_count,
                                   context=f"S{season_count} Relegation Match (18v23)", advantage=advantage_18v23
                                   )
        upi_g2W.history[season_count] += f" Won 18/23 Relegation Match -> S{season_count + 1} Universal League."
        upi_g2L.history[season_count] += f" Lost 18/23 Relegation Match -> S{season_count + 1} Universal Qualifying."

        advantage_19v22 = relegation_chain[2].points - relegation_chain[5].points
        upi_g3W, upi_g3L = best_of(relegation_chain[2], relegation_chain[5],
                                   thresh=120, win_by=32,
                                   both_return=True, upset_list=upset_list, upset_count=upset_count,
                                   context=f"S{season_count} Relegation Match (19v22)",advantage=advantage_19v22
                                   )
        upi_g3W.history[season_count] += f" Won 19/22 Relegation Match -> S{season_count + 1} Universal League."
        upi_g3L.history[season_count] += f" Lost 19/22 Relegation Match -> S{season_count + 1} Universal Qualifying."

        advantage_20v21 = relegation_chain[3].points - relegation_chain[4].points
        upi_g4W, upi_g4L = best_of(relegation_chain[3], relegation_chain[4],
                                   thresh=120, win_by=32,
                                   both_return=True, upset_list=upset_list, upset_count=upset_count,
                                   context=f"S{season_count} Relegation Match (20v21)", advantage=advantage_20v21
                                   )
        upi_g4W.history[season_count] += f" Won 20/21 Relegation Match -> S{season_count + 1} Universal League."
        upi_g4L.history[season_count] += f" Lost 20/21 Relegation Match -> S{season_count + 1} Universal Qualifying."

        upi_winners = [upi_g1W, upi_g2W, upi_g3W, upi_g4W]
        upi_winners.sort(key=lambda x : x.seed)

        upi_losers = [upi_g1L, upi_g2L, upi_g3L, upi_g4L]
        upi_losers.sort(key=lambda x: x.seed)

        missed_playoffs = upi_winners + upi_losers + missed_playoffs

        playoff_one = list(postseason)
        champ, second, third, fourth, fifth, sixth, seventh, eighth, ninth, tenth, eleventh, twelfth, thirteenth, fourteenth, fifteenth, sixteenth = single_elim_16(postseason,upset_list=upset_list,upset_count=upset_count,region=region, season_count=season_count)
        playoff_standings = [champ, second, third, fourth, fifth, sixth, seventh, eighth, ninth, tenth, eleventh, twelfth, thirteenth, fourteenth, fifteenth, sixteenth]
        for team in playoff_one:
            team.accolades['Universal-Playoffs'] += 1
        champ.accolades['Universal-Champ'] += 1




    playoff_standings_alt = [second, third, fourth, fifth, sixth, seventh, eighth, ninth, tenth, eleventh, twelfth] if post_range in [10,12] else [second, third, fourth, fifth, sixth, seventh, eighth, ninth, tenth, eleventh, twelfth, thirteenth, fourteenth, fifteenth, sixteenth]
    place = 1
    for team in playoff_standings_alt:
        place+=1
        team.history[season_count] += f" {region} playoffs as {team.seed} seed, finished {ordinal_string(place)}."
    if region != 'Universal':
        champ.history[
            season_count] += f" {region} playoffs as {champ.seed} seed, WON CHAMPIONSHIP. -> UNI Qualifier."
        for team in [second, third, fourth]:
            team.history[season_count] += f" -> Pre-Qualifying."
        for team in [fifth, sixth, seventh, eighth]:
            team.history[season_count] += f" -> Last Stand."
    else:
        champ.history[season_count] += f" Universal playoffs as {champ.seed} seed, WON CHAMPIONSHIP."

    print(Fore.RED + f"{champ.name} have won the {region} League." + Fore.RESET)
    if region == "Universal" and season_count != 0:
        sleep(3)
        champ.is_noteworthy = True


    final_standings = playoff_standings + missed_playoffs

    if region!="Universal":
        for i in range(11,22):

            final_standings[i].third_pick = 1 if uniform(0,1) <= (0.09 + (i/100)) else 0
            if final_standings[i].third_pick == 1:
                final_standings[i].history[season_count] += f"\n\tLUCKY: Third Round Pick obtained with {100*(0.09 + (i/100))}% chance\n"


    translated_region = region.replace(" Regional", "") if " Regional" in region else region
    for team in final_standings:
        if team.played_region[season_count] in ['Darkwing', 'Shining-Core', 'Diamond-Sea', 'Web-of-Nations', 'Ice-Wall',
                                    'Candyland', "Hell's-Circle", 'Steel-Heart'] and region == 'Universal':
            team.played_region[season_count] += 'Universal'
        else:
            team.played_region[season_count] = translated_region
        if team.mine:
            print(Fore.BLUE + f"{team.name}: {team.history[season_count]}"
                  + Fore.RESET)
            fire_coach = timed_input(f"Press Y to fire {str(team.team_coach)}, Press L to change lineup, press any other key to do nothing:\n")
            if fire_coach == "Y" or fire_coach == "y":
                team.history[season_count] += f"\n\tFired {team.team_coach.name}"
                new_coach = Coach(region=region)
                team.history[season_count] += f", Hired {new_coach.name}"
                team.change_coach(new_coach)
            elif fire_coach == 'l' or fire_coach == 'L':
                new_lineup_mod = input("What lineup modifier would you like to use?")
                team.team_coach.lineup_modifier = new_lineup_mod if new_lineup_mod in ['NC', '1S', '2S', '3S', '4S', '5S', '6S', '7S', '8S', '1C', '2C', '3C', '4C', '5C', '6C', '7C'] else choice(['1S', '2S', '3S', '4S', '5S', '6S', '7S', '8S', '1C', '2C', '3C', '4C', '5C', '6C', '7C'])


            write_to_file(filename='my_team_results', words=f"S{season_count}: {team.name}: {team.history[season_count]}", mode='a', error=False)




    #write_champ(champ, season_count, region, league=final_standings)


    abbreviated_region = {'Darkwing' : 'DW', 'Shining-Core' : 'SC', 'Diamond-Sea' : 'DS', 'Web-of-Nations' : 'WON', 'Ice-Wall' : 'IW',
                                    'Candyland' : 'CL', "Hell's-Circle" : "HC", 'Steel-Heart' : 'SH'}
    for pos in range(len(final_standings)):
        final_standings[pos].seed = pos
    if translated_region != 'Universal':
        for pos in range(len(final_standings)):
            final_standings[pos].region_seed = f"{abbreviated_region[translated_region]}-{pos+1}"

    if final_reversed:
        final_standings.reverse()
    for t in coach_hot_seat:
        coach_roll = randint(0,100)
        if coach_roll <= 5 or (coach_roll <= 15 and t.mine):
            lucky_slot_amp_possibilities = [
                ["Power", round(uniform(0.69, 0.99), 2)],  # % chance to add power
                ["Attack Damage", randint(4, 7)],  # raw increment
                ["Critical Chance", round(uniform(0.025, 0.05), 2)],  # raw increment
            ]
            lucky_slots_amped = choice([
            [0,4,5], [1,3,5], [2,3,4]
        ])
            lucky_slot_effect = [lucky_slots_amped] + choice(lucky_slot_amp_possibilities)

            t.history[season_count] += f"\n\tFired {t.team_coach.name}, Hired Guy Lucky"
            t.change_coach(Coach(fixed_name="Guy Lucky",fixed_slot_effect=lucky_slot_effect,region=region))

        elif coach_roll <= 35:
            t.history[season_count] += f"\n\tFired {t.team_coach.name}"
            new_coach = Coach(region=region)
            t.history[season_count] += f", Hired {new_coach.name}"
            t.change_coach(new_coach)

    for t in dumpster_fire:
        if choice([True,True,False,False,False]):
            t.third_pick = 1

        coin = choice([0,0,0,0,1,1,1,1,1,1,1,1,1,1,2,3])
        unblessed = [0, 1, 2]
        if coin != 0:
            for _ in range(coin):
                blessed_index = choice(unblessed)
                t.players[blessed_index].breakout = True
                try:
                    unblessed.remove(blessed_index)
                except IndexError:
                    pass
                t.history[season_count] += f"\n\tBLESSING: {t.players[blessed_index].name}(Slot {blessed_index}) will have a breakout season!"

    team_season_dataframe(final_standings, season_no=season_count)

    if stats_list:

        if region == 'Universal':
            names_standings = {team.name.replace('*', '').replace('#',''): rank + 1 for rank, team in enumerate(reversed(final_standings))}
            a=0
            for team in final_standings:
                a+=1
                for player in team.players:
                    temp = PlayerSeason(player, season_count, sub_season=sub_season, capt_str=str(team.captain))
                    stats_list[season_count].append(temp)
        #           temp.print_player_season(filename='uni_player_seasons',team_standing=a)

        else:
            names_standings = {team.name.replace('*', '').replace('#',''): rank + 1 for rank, team in enumerate(final_standings)}
            for team in final_standings:
                for player in team.players:
                    temp = PlayerSeason(player, season_count, sub_season=sub_season, capt_str=str(team.captain))
                    stats_list[season_count].append(temp)
        averages = get_league_averages(final_standings, season_count, region, for_xWAR=True)
        stats = ["power", "dps", "crit_pct", "crit_x", "mit_pct", 'defense_pct', 'defense_abs', "max_health", "spawn_time"]
        deviations = {"Power": 0, "DPS": 0, "Critical %": 0, "Critical X": 0, "Mitigated %" : 0, 'Defense %' : 0, 'Defense Absolute' : 0, "Health": 0, "Spawn Time": 0}
        translated_stats = {'power': 'Power', 'dps' : 'DPS', 'crit_pct' : 'Critical %', 'crit_x' : 'Critical X', 'mit_pct' : 'Mitigated %',
                            'defense_pct' : 'Defense %', 'defense_abs' : 'Defense Absolute',
                            'max_health' : 'Health',
                            'spawn_time' : 'Spawn Time'}
        for stat in stats:
            values = [getattr(p, stat) for p in stats_list[season_count]]  # or p[stat] if using dicts
            deviations[translated_stats[stat]] = stdev(values)


        region_mvp(stats_list, season_count, region, names_standings)
        player_season_excel(stats_list[season_count],season_count=season_count,averages=averages,deviations=deviations)


    season_end_time = time()
    league_extra_str = " League" if region == 'Universal' else ""

    with open('execution_time', 'a') as file:
        file.write(f"Season {season_count} {region}{league_extra_str} Execution Time: {round((season_end_time-season_start_time)/60)} minutes, {round(((season_end_time-season_start_time)%60),2)} seconds.\n")
    if champ_list:
        return  final_standings, champ_list
    else:
        return final_standings

