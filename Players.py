from random import uniform, seed, choice

import pandas as pd
from colorama import Fore, Style
import math
import numpy as np
from collections import OrderedDict
import sqlite3
import lightgbm as lgb
from datetime import datetime
from statistics import mean

from switches import NO_SQL



bst = lgb.Booster(model_file="new_player_model.bin")
bst.save_model("new_player_model.bin")

def remove_tag_from_name(s:str):
    targets = ["$l", "R#", "C%", "I*", "Tx", "Hn", "Sp", "Fl", "Pp", "U-", "X+", "V"]
    out = s
    for t in targets:
        out = out.replace(t, "")
    return out

def xwar_stats_df(player, dt, season_count, for_model=False):
    # averages and std devs
    avg_stats = {
        'Power': 55,
        'DPS': 55.5 / 7.5,
        'Critical %': 0.065,
        'Critical X': 7.5,
        'Mitigated %': 0.58,
        'Defense %': 0.04,
        'Defense Absolute': 4,
        'Health': 210,
        'Spawn Time': 6.9
    }
    std_devs = {
        'Power': 2.83,
        'DPS': 1.285,
        'Critical %': 0.01649,
        'Critical X': 1.1,
        'Mitigated %': 0.02381,
        'Defense %': 0.01155,
        'Defense Absolute': 1.155,
        'Health': 25.43,
        'Spawn Time': 0.849
    }

    # traits list
    trait_keys = ["$l","C%","I*","Pp","R#","U-","X+","Hn","Tx","Fl","Sp","V."]

    # calculate numeric stats
    crit_value = player.insta_kill_pct if "$l" in player.trait_tag else player.crit_pct

    values = [
        round((player.power - avg_stats["Power"]) / std_devs["Power"],3),
        round((crit_value - avg_stats["Critical %"]) / std_devs["Critical %"],3),
        round((player.crit_x - avg_stats["Critical X"]) / std_devs["Critical X"],3),
        round((player.max_health - avg_stats["Health"]) / std_devs["Health"],3),
        round((avg_stats["Spawn Time"] - player.spawn_time) / std_devs["Spawn Time"],3),
        round((player.dps - avg_stats["DPS"]) / std_devs["DPS"],3)
    ]

    # add one-hot traits
    for t in trait_keys:
        values.append(1 if t in player.trait_tag else 0)

    # add remaining numeric stats
    values += [
        round((player.mit_pct - avg_stats['Mitigated %']) / std_devs['Mitigated %'],3),
        round((player.defense_pct - avg_stats["Defense %"]) / std_devs["Defense %"],3),
        round((player.defense_abs - avg_stats["Defense Absolute"]) / std_devs["Defense Absolute"],3)
    ]

    # define column names
    cols = ["Power","Critical %","Critical X","Health","Spawn Time","DPS"] + \
           [f"Trait_{t}" for t in trait_keys] + \
           ["Mitigated %","Defense %","Defense Absolute"]

    if for_model:
        df = pd.DataFrame([values], columns=cols)
    else:
        df = pd.DataFrame([values])
    return df

def QUERY(sql, connect=sqlite3.connect('ControlDataBase.db'), params=None, is_select=True):
    if NO_SQL:
        return 0
    elif is_select:
        if params:
            return pd.read_sql_query(sql, connect, params=params)
        else:
            return pd.read_sql_query(sql, connect)
    else:
        cur = connect.cursor()
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        connect.commit()
        return cur.lastrowid

def write_to_file(filename=None, words=None, mode='w', error=False):
    if error:
        filename = 'error_output'
        mode = 'a'

    with open(filename, mode) as f:
        f.write(words + '\n')

def ordinal_string(n: int) -> str:
    if 10 <= n % 100 < 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    if n == 0:
        suffix = ''
    return f"{n}{suffix}"

def calculate_standard_deviation(number, sample_size, sample_average):
    deviation = number - sample_average
    standard_deviation = deviation / math.sqrt(sample_size)
    return standard_deviation


multiplier = 1

def grade_seasons(seasons, print_averages=False, import_averages = None, context = None, avg_stats_df = None, region=None):

    DATA_FRAME = False

    #todo at the moment, this is creating a new DF for each player season and appending it to the  excel file in both
    # best_of_stats and region_mvp, massively slowing down the code
    # adding a check for region  == 'All' makes it so that only one player gets added to the sheet for some reason

    MULT_NO_USE = True
    full_season = False
    avg_stats_df = None

    #iterate through each object, and create lists with values corresponding to each player
    #put each list through calculate_standard_deviations and use it to assign a coefficient variable to each player equivalent
    #a total season's grade is determined by the sum of all coefficients

    #the import_averages function is for when seasons are being graded for a team, so their season grades can be compared to those of the league they were in
    #instead of just the team

    if import_averages:
        size = len(import_averages)

        total_kills = 0
        total_deaths = 0
        total_crit_kills = 0
        total_damage = 0
        total_effect = 0
        total_overkill = 0
        total_mitigated = 0
        total_d_pct_blocked = 0
        total_d_abs_blocked = 0

        kills_list = []
        deaths_list = []
        crit_kills_list = []
        damage_list = []
        effect_list = []
        overkill_list = []
        mitigated_list = []
        d_pct_blocked_list = []
        d_abs_blocked_list = []

        #Remnant of a discarded function

        for season in import_averages:

            kills_list.append(season.kills*multiplier)
            deaths_list.append(season.deaths*multiplier)
            crit_kills_list.append(season.crit_kills*multiplier)
            damage_list.append(season.damage*multiplier)
            effect_list.append(season.effect*multiplier)
            overkill_list.append(season.overkill*multiplier)
            mitigated_list.append(season.mitigated*multiplier)
            d_abs_blocked_list.append(season.d_abs_blocked*multiplier)
            d_pct_blocked_list.append(season.d_pct_blocked * multiplier)

            total_kills += season.kills * multiplier
            total_deaths += season.deaths * multiplier
            total_crit_kills += season.crit_kills * multiplier
            total_damage += season.damage * multiplier
            total_effect += season.effect * multiplier
            total_overkill += season.overkill * multiplier
            total_mitigated += season.mitigated * multiplier
            total_d_pct_blocked += season.d_pct_blocked*multiplier
            total_d_abs_blocked += season.d_abs_blocked*multiplier
    else:
        size = len(seasons)

        total_kills = 0
        total_deaths = 0
        total_crit_kills = 0
        total_damage = 0
        total_effect = 0
        total_overkill = 0
        total_mitigated = 0
        total_d_pct_blocked = 0
        total_d_abs_blocked = 0

        kills_list = []
        deaths_list = []
        crit_kills_list = []
        damage_list = []
        effect_list = []
        overkill_list = []
        mitigated_list = []
        d_pct_blocked_list = []
        d_abs_blocked_list = []

        for season in seasons:

            kills_list.append(season.kills * multiplier)
            deaths_list.append(season.deaths * multiplier)
            damage_list.append(season.damage * multiplier)
            crit_kills_list.append(season.crit_kills*multiplier)
            effect_list.append(season.effect * multiplier)
            overkill_list.append(season.overkill * multiplier)
            mitigated_list.append(season.mitigated * multiplier)
            d_abs_blocked_list.append(season.d_abs_blocked * multiplier)
            d_pct_blocked_list.append(season.d_pct_blocked * multiplier)

            total_kills += season.kills * multiplier
            total_deaths += season.deaths * multiplier
            total_crit_kills += season.crit_kills * multiplier
            total_damage += season.damage * multiplier
            total_effect += season.effect * multiplier
            total_overkill += season.overkill * multiplier
            total_mitigated += season.mitigated * multiplier
            total_d_pct_blocked += season.d_pct_blocked * multiplier
            total_d_abs_blocked += season.d_abs_blocked * multiplier

    try:
        avg_kills = total_kills / size
        avg_deaths = total_deaths / size
        avg_crit_kills = total_crit_kills / size
        avg_damage = total_damage / size
        avg_effect = total_effect / size
        avg_overkill = total_overkill / size
        avg_mitigated = total_mitigated / size
        avg_d_pct_blocked = total_d_pct_blocked/size
        avg_d_abs_blocked = total_d_abs_blocked/size

#        with open('error_output', 'a') as e:
#            e.write(f"\n{context}League KD stats: {total_kills:.3f} total kills, {total_deaths:.3f} total deaths\n"
#                    f"{avg_kills:.3f} average kills, {avg_deaths:.3f} average deaths.")
#            if total_deaths == total_kills and avg_deaths == avg_kills:
#                e.write("(Values Equal)\n")
#            else:
#                e.write("(Values Unequal)\n")


    except ZeroDivisionError:
        avg_kills = -1
        avg_deaths = -1
        avg_crit_kills = -1
        avg_damage = -1
        avg_effect = -1
        avg_overkill = -1
        avg_mitigated = -1
        avg_d_pct_blocked = -1
        avg_d_abs_blocked = -1

    average_stats_num = {'Kills': avg_kills, 'Deaths': avg_deaths, 'Critical Kills' : avg_crit_kills, 'Damage': avg_damage, 'Effect': avg_effect, 'Overkill': avg_overkill, 'Mitigated': avg_mitigated, 'D% Blocked' : avg_d_pct_blocked, 'DAbs Blocked' : avg_d_abs_blocked}
    stat_words = ['Kills', 'Deaths', 'Damage', 'Effect', 'Overkill', 'Mitigated','Critical Kills', 'D% Blocked', 'DAbs Blocked']

    if not region:
        region = 'Error'


    average_stats_list = {'Kills' : kills_list, 'Deaths' : deaths_list, 'Critical Kills' : crit_kills_list, 'Damage' : damage_list, 'Effect' : effect_list,
                          'Overkill' : overkill_list, 'Mitigated' : mitigated_list, 'D% Blocked' : d_pct_blocked_list, 'DAbs Blocked' : d_abs_blocked_list}

    for season in seasons:

        if print_averages:
            season.grade_breakdown += f"Avg Kills: {avg_kills:.3f}, Avg Deaths: {avg_deaths:.3f}, Avg Critical Kills: {avg_crit_kills:.3f}, Avg Damage: {avg_damage:.3f},\n Avg Effect: {avg_effect:.3f}," \
                                      f"Avg Overkill: {avg_overkill:.3f}, Avg Mitigated: {avg_mitigated:.3f}\n Avg D% Blocked: {avg_d_pct_blocked}, Average DAbs Blocked: {avg_d_abs_blocked}\n"

        weights = {'Kills': 4, 'Deaths': -3, 'Damage': 0.75, 'Effect': 7, 'Overkill': 0.25, 'Mitigated': 0.2}


        translate = {'Kills' : season.kills*multiplier, 'Deaths' : season.deaths*multiplier, 'Critical Kills' : season.crit_kills*multiplier, 'Damage' : season.damage*multiplier, 'Effect' : season.effect*multiplier,
                     'Overkill' : season.overkill*multiplier, 'Mitigated' : season.mitigated*multiplier, 'D% Blocked' : season.d_pct_blocked*multiplier, 'DAbs Blocked' : season.d_abs_blocked*multiplier}

        iqr_stats = {}

        for word in stat_words:
            #iqr_stats contains is a dictionary which contains the word for each stat as a key, and the difference between the
            # 1st and 3rd quartiles as a value for each stat
            iqr_stats[word] = np.percentile(average_stats_list[word], 75) - np.percentile(average_stats_list[word], 25)
            season.league_averages[word] = round(average_stats_num[word], 3)

        #the next thing to do is find the difference between the average stat and player stat for each season,
        #and DIVIDE this number by the interquartile range to get the normalized difference between the average and player stat
        #then, multiply each normalized difference by the chosen weights, and add everything together to get the total grade

        norm_differences = {}

        for word in stat_words[:6]:
            if iqr_stats[word] != 0:
                norm_differences[word] = (translate[word] - average_stats_num[word]) / iqr_stats[word]
            elif word != 'Overkill':
                norm_differences[word] = (translate[word] - average_stats_num[word])
            else:
                norm_differences[word] = (translate[word] - average_stats_num[word]) / 10000
            season.season_grade_dict[word] = norm_differences[word] * weights[word]

        season.season_grade_data = (season.season_grade_dict['Kills']) + (season.season_grade_dict['Deaths']) + (season.season_grade_dict['Damage']) + (season.season_grade_dict['Effect']) + (season.season_grade_dict['Overkill']) + (season.season_grade_dict['Mitigated'])
        season.grade_breakdown += f"{season.season_grade_dict['Kills']:.3f} in kills * 5, {season.season_grade_dict['Deaths']:.3f} in deaths * -5, {season.season_grade_dict['Damage']:.3f} in damage / 2,\n{season.season_grade_dict['Effect']:.3f} in effect * 10, {season.season_grade_dict['Overkill']:.3f} in overkill effect / 4, {season.season_grade_dict['Mitigated']:.3f} in mitigated / 5."


    # takes in a list of PlayerSeason objects

class PlayerSeason:
    def __init__(self, player, season_count, sub_season=None, capt_str=''):
        #sub_season is for a PlayerSeason object is being created only for one part of the season, such as the regional regular season
        #this will be a string value

        self.tier = player.tier
        self.atk_dmg = player.atk_dmg
        self.atk_spd = player.atk_spd
        self.dps = player.atk_dmg / player.atk_spd
        self.insta_kill_pct = player.insta_kill_pct
        self.crit_pct = player.crit_pct
        self.crit_x = player.crit_x
        self.mit_pct = player.mit_pct
        self.defense_pct = player.defense_pct
        self.defense_abs = player.defense_abs
        self.overkill_x = 3
        self.max_health = player.max_health  # redundant
        self.spawn_time = player.spawn_time
        self.power = player.power

        self.trait_tag = player.trait_tag

        self.season = season_count
        self.player = player
        self.age = self.player.age
        self.game_count = player.games_played['This-Season']
        self.game_wins = player.game_wins #this season only
        self.game_losses = player.game_losses #this season only
        self.match_count = player.games_played['Matches']
        self.sub_season = sub_season
        self.season_grade_dict = {'Kills' : 0, 'Deaths' : 0, 'Damage' : 0, 'Effect' : 0, 'Overkill' : 0, 'Mitigated' : 0}
        self.league_averages = {'Kills' : 0, 'Deaths' : 0, 'Critical Kills' : 0, 'Damage' : 0, 'Effect' : 0, 'Overkill' : 0, 'Mitigated' : 0, "D% Blocked" : 0, "DAbs Blocked" : 0}
        self.season_grade_data = 0
        self.grade_breakdown = ""
        self.xWAR_breakdown = player.xWAR_breakdown
        self.captain_stats = capt_str
        if self.game_count > 0:
            self.kills = player.kills / self.game_count
            self.deaths = player.deaths / self.game_count
            self.crit_kills = player.crit_kills / self.game_count
            self.damage = player.damage_data['Total-Damage'] / self.game_count
            self.effect = player.damage_data['Tesseract'] / self.game_count
            self.total_attacks = player.damage_data['Total-Attacks'] / self.game_count
            self.total_delayed_damage = player.damage_data['Total-Delayed-Damage'] / self.game_count
            self.ticks_alive = player.damage_data['Ticks Alive'] / self.game_count
            self.ticks_dead = player.damage_data['Ticks Dead'] / self.game_count
            try:
                self.avg_delayed_x_per_atk = player.damage_data['Total-Delayed-X'] / player.damage_data['Total-Attacks']
            except ZeroDivisionError:
                self.avg_delayed_x_per_atk = 0
            self.overkill = player.damage_data['Overkill'] / self.game_count
            self.healed = 0 if 'U-' not in player.trait_tag else player.damage_data['Healed'] / self.game_count
            self.revived = 0 if 'U-' not in player.trait_tag else player.damage_data['Revived'] / self.game_count
            self.reflected = 0 if 'R#' not in player.trait_tag else player.damage_data['Reflected']/self.game_count
            self.reflect_kills = 0 if 'R#' not in player.trait_tag else player.damage_data['Reflect-Kills'] / self.game_count
            self.reflect_count = 0 if 'R#' not in player.trait_tag else player.damage_data['Reflect-Count'] / self.game_count
            self.crit_reflected = 0 if 'R#' not in player.trait_tag else player.damage_data['Crit-Reflects'] / self.game_count
            self.explosion_dmg = 0 if 'X+' not in player.trait_tag else player.damage_data['Explosion'] / self.game_count
            self.explosion_kills = 0 if 'X+' not in player.trait_tag else player.damage_data['Explosion-Kills'] / self.game_count
            self.toxin_dmg = 0 if 'Tx' not in player.trait_tag else player.damage_data['Toxin'] / self.game_count
            self.toxin_kills = 0 if 'Tx' not in player.trait_tag else player.damage_data['Toxin Kills'] / self.game_count
            self.attacks_stunned = 0 if 'Fl' not in player.trait_tag else player.damage_data['Attacks Stunned'] / self.game_count
            self.vamp_heal = 0 if 'V.' not in player.trait_tag else player.damage_data['Vampire Healed'] / self.game_count
            self.extra_attacks = 0 if 'Sp' not in player.trait_tag else player.damage_data['Extra Attacks'] / self.game_count
            self.team_heal = 0 if 'Hn' not in player.trait_tag else player.damage_data['Team Healed'] / self.game_count

            self.streak = player.kill_streak['Peak']
            self.mitigated = player.crit_data['Mitigated'] / self.game_count
            self.d_pct_blocked = player.damage_data['D% Blocked'] / self.game_count
            self.d_abs_blocked = player.damage_data['DAbs Blocked'] / self.game_count
            #self.crit_pct = player.crit_data['Ratio']
            self.parry_pct = player.crit_data['P_Ratio']
        else:
            self.kills = self.deaths = self.crit_kills = self.damage = self.effect = self.overkill = self.streak = self.mitigated = self.crit_pct = self.parry_pct = -1
            #self.healed = self.revived = self.reflected = self.reflect_kills = -1

    def print_kills_deaths(self):
        with open('best_stats', 'a') as p:
            p.write(f"{self.player.name} (for S{self.season}_{self.player.team})\n"
            f"Kills Per Game: {self.kills :.3f} (Avg {self.league_averages['Kills']})\n"
            f"Critical Kills Per Game: {self.crit_kills :.3f} (Avg {self.league_averages['Critical Kills']})\n"
            f"Deaths Per Game: {self.deaths :.3f} (Avg {self.league_averages['Deaths']})\n\n")

    def print_effect(self):
        with open('best_stats', 'a') as p:
            p.write(f"{self.player.name} (for S{self.season}_{self.player.team})\n"
                    f"Total Effect: {self.effect :.3f} (Avg {self.league_averages['Effect']})\n"
                    f"Overkill Effect: {self.overkill :.3f} (Avg {self.league_averages['Overkill']})\n\n")

    def print_streak(self):
        with open('best_stats', 'a') as p:
            p.write(f"{self.player.name} (for S{self.season}_{self.player.team})\n"
                    f"Best Kill Streak: {self.streak}\n\n")

    def print_mitigated(self):
        with open('best_stats', 'a') as p:
            p.write(f"{self.player.name} (for S{self.season}_{self.player.team})\n"
                    f"Damage Mitigated Per Game via Parry: {self.mitigated :.3f} (Avg {self.league_averages['Mitigated']})\n\n")

    def print_healed(self):
        with open('best_stats', 'a') as p:
            p.write(f"{self.player.name} (for S{self.season}_{self.player.team})\n"
                    f"Damage Mitigated Per Game via Healing: {self.healed :.3f}\n\n")

    def print_damage(self):
        with open('best_stats', 'a') as p:
            p.write(f"{self.player.name} (for S{self.season}_{self.player.team})\n"
                    f"Damage Dealt Per Game: {self.damage :.3f} (Avg {self.league_averages['Damage']})\n\n")

    def print_player_season(self, filename=None, team_standing=None):
        undead_str = f"Health Healed Per Game: {self.healed:.3f}\nRevives Per Game: {self.revived:.3f}\n" if 'U-' in self.player.trait_tag else ""
        reflector_str = f"Damage Reflected Per Game: {self.reflected:.3f}\nTotal Hits Reflected Per Game: {self.reflect_count:.3f}\nCritical Hits Reflected Per Game: {self.crit_reflected:.3f}\nKills via Reflect Per Game: {self.reflect_kills:.3f}\n" if 'R#' in self.player.trait_tag else ""
        exploder_str = f"Explosion Damage Per Game: {self.explosion_dmg:.3f}\nKills via Explosion Per Game: {self.explosion_kills:.3f}\n" if 'X+' in self.player.trait_tag else ""
        toxic_str = f"Toxin Damage Per Game: {self.toxin_dmg:.3f}\nKills via Toxin Per Game: {self.toxin_kills:.3f}\n" if 'Tx' in self.player.trait_tag else ""
        flasher_str = f"Attacks Prevented via Stun Per Game: {self.attacks_stunned:.3f}\n" if 'Fl' in self.player.trait_tag else ""
        vampire_str = f"Vampire Self-heal Per Game: {self.vamp_heal:.3f}\n" if 'V.' in self.player.trait_tag else ""
        splitter_str = f"Extra Attacks Per Game: {self.extra_attacks:.3f}\n" if 'Sp' in self.player.trait_tag else ""
        healer_str = f"Team Healing Per Game: {self.team_heal:.3f}\n" if 'Hn' in self.player.trait_tag else ""

        if not filename:
            print(f"{self.player.name} (for S{self.season}_{self.player.team}),", end='')
            print(self.player.drafted + f" (this is their {ordinal_string(self.age+1)} season).\n")

            if self.season_grade_data != 0:
                print(f"Season Grade: {round(self.season_grade_data, 3)}\n")

            print(f"Games Played: {self.player.games_played['This-Season']} ({self.match_count} matches)\n"
            f"{self.captain_stats}"
            f"Kills Per Game: {self.kills :.3f}\n"
            f"Deaths Per Game: {self.deaths :.3f}\n"
            f"Critical Kills Per Game: {self.crit_kills :.3f}\n"
            f"Damage Dealt Per Game: {self.damage :.3f}\n"
            f"Damage Mitigated Per Game: {self.mitigated :.3f}\n{reflector_str}{exploder_str}{toxic_str}{flasher_str}{vampire_str}{splitter_str}{healer_str}"
            f"Defense % Damage Blocked Per Game: {self.d_pct_blocked:.3f}"
            f"Defense Absolute Damage Blocked Per Game: {self.d_abs_blocked:.3f}"     
            f"Total Effect Per Game: {self.effect :.3f}\n"
            f"Overkill Effect Per Game: {self.overkill :.3f}\n{undead_str}"
            f"Best Kill Streak: {self.streak}\n\n")
        else:
            team_standing_str = f", finished {ordinal_string(team_standing)}" if team_standing else ""
            with open(filename, 'a') as p:
                p.write(f"{self.player.name} (for S{self.season}_{self.player.team}{team_standing_str})\n")
                p.write(self.player.drafted + f" (this is their {ordinal_string(self.age+1)} season)." + '\n')
                if self.season_grade_data != 0:
                    p.write(f"Season Grade: {round(self.season_grade_data, 3)}\n")
                p.write(f"Games Played: {self.player.games_played['This-Season']} ({self.match_count} matches)\n"
                f"{self.captain_stats}"
                f"xWAR: {self.player.xWAR}\n"
                f"Attack Damage: {self.player.atk_dmg}\n" 
                f"Attack Speed: {self.player.atk_spd}\n" 
                f"Crit %: {self.player.crit_pct}\n" 
                f"Crit X: {self.player.crit_x}\n" 
                f"Mitigated %: {self.player.mit_pct:.3f}\n"
                f"Defense %: {self.player.defense_pct}\n"
                f"Defense Absolute: {self.player.defense_abs}\n"
                f"Health: {self.player.max_health}\n"
                f"Power: {self.player.power}\n" 
                f"Spawn Time: {self.player.spawn_time}\n" 
                f"AGE: {self.player.age}\n"
                f"Kills Per Game: {self.kills :.3f} (Avg {self.league_averages['Kills']})\n"
                f"Deaths Per Game: {self.deaths :.3f} (Avg {self.league_averages['Deaths']})\n"
                f"Ticks Alive per Game: {self.ticks_alive :.3f}\n"
                f"Ticks Dead per Game: {self.ticks_dead :.3f}\n"
                f"Critical Kills Per Game: {self.crit_kills :.3f} (Avg {self.league_averages['Critical Kills']})\n"
                f"Damage Dealt Per Game: {self.damage :.3f} (Avg {self.league_averages['Damage']})\n"
                f"Damage Mitigated Per Game: {self.mitigated :.3f} (Avg {self.league_averages['Mitigated']})\n{reflector_str}{exploder_str}{toxic_str}{flasher_str}{vampire_str}{splitter_str}{healer_str}"
                f"Defense % Damage Blocked Per Game: {self.d_pct_blocked:.3f} (Avg {self.league_averages['D% Blocked']})\n"
                f"Defense Absolute Damage Blocked Per Game: {self.d_abs_blocked:.3f} (Avg {self.league_averages['DAbs Blocked']})\n"
                f"Total Attacks Per Game: {self.total_attacks:.3f}\nDelayed Damage Per Game: {self.total_delayed_damage:.3f}\n"
                f"Average Delayed Multiplier Per Attack: {self.avg_delayed_x_per_atk:.3f}\n"
                f"Total Effect Per Game: {self.effect :.3f} (Avg {self.league_averages['Effect']})\n"
                f"Overkill Effect Per Game: {self.overkill :.3f} [{100 * self.overkill/self.effect:.2f}% of total Effect] (Avg {self.league_averages['Overkill']})\n"
                f"Non-Overkill Effect Per Game: {self.effect-self.overkill:.3f} [{100 * (self.effect-self.overkill) / self.effect:.3f}% of Total Effect]\n{undead_str}\n")

        if '**' in self.player.team or '!' in self.player.team and filename != 'region_mvp': #region_mvp function writes to both region_mvp and playerstats, so if one of my players is
            #a region mvp, it will write twice
            team_standing_str = f", finished {ordinal_string(team_standing)}" if team_standing else ""
            with open('my_team_playerstats', 'a') as p:
                p.write(f"{self.player.name} (for S{self.season}_{self.player.team}{team_standing_str})\n")
                p.write(self.player.drafted + f" (this is their {ordinal_string(self.age + 1)} season)." + '\n')
                if self.season_grade_data != 0:
                    p.write(f"Season Grade: {round(self.season_grade_data, 3)}\n")
                p.write(f"Games Played: {self.player.games_played['This-Season']} ({self.match_count} matches)\n"
                        f"{self.captain_stats}"
                        f"xWAR: {self.player.xWAR}\n"
                        f"Attack Damage: {self.player.atk_dmg}\n"
                        f"Attack Speed: {self.player.atk_spd}\n"
                        f"Crit %: {self.player.crit_pct}\n"
                        f"Crit X: {self.player.crit_x}\n"
                        f"Mitigated %: {self.player.mit_pct:.3f}\n"
                        f"Defense %: {self.player.defense_pct}\n"
                        f"Defense Absolute: {self.player.defense_abs}\n"
                        f"Health: {self.player.max_health}\n"
                        f"Power: {self.player.power}\n"
                        f"Spawn Time: {self.player.spawn_time}\n"
                        f"AGE: {self.player.age}\n"
                        f"Kills Per Game: {self.kills :.3f} (Avg {self.league_averages['Kills']})\n"
                        f"Deaths Per Game: {self.deaths :.3f} (Avg {self.league_averages['Deaths']})\n"
                        f"Ticks Alive per Game: {self.ticks_alive :.3f}\n"
                        f"Ticks Dead per Game: {self.ticks_dead :.3f}\n"
                        f"Critical Kills Per Game: {self.crit_kills :.3f} (Avg {self.league_averages['Critical Kills']})\n"
                        f"Damage Dealt Per Game: {self.damage :.3f} (Avg {self.league_averages['Damage']})\n"
                        f"Damage Mitigated Per Game: {self.mitigated :.3f} (Avg {self.league_averages['Mitigated']})\n{reflector_str}{exploder_str}{toxic_str}{flasher_str}{vampire_str}{splitter_str}{healer_str}"
                        f"Defense % Damage Blocked Per Game: {self.d_pct_blocked:.3f} (Avg {self.league_averages['D% Blocked']})\n"
                        f"Defense Absolute Damage Blocked Per Game: {self.d_abs_blocked:.3f} (Avg {self.league_averages['DAbs Blocked']})\n"
                        f"Total Attacks Per Game: {self.total_attacks:.3f}\nDelayed Damage Per Game: {self.total_delayed_damage:.3f}\n"
                        f"Average Delayed Multiplier Per Attack: {self.avg_delayed_x_per_atk:.3f}\n"
                        f"Total Effect Per Game: {self.effect :.3f} (Avg {self.league_averages['Effect']})\n"
                        f"Overkill Effect Per Game: {self.overkill :.3f} [{100 * self.overkill/self.effect:.2f}% of total Effect] (Avg {self.league_averages['Overkill']})\n"
                        f"Non-Overkill Effect Per Game: {self.effect-self.overkill:.3f} [{100 * (self.effect-self.overkill) / self.effect:.3f}% of Total Effect]\n{undead_str}\n")



class Player:
    def __init__(self, tier, atk_dmg, atk_spd, crit_pct, crit_x, health, power, spawn_time, crit_dmg, name, mit_pct=0,
                 defense_abs=0, defense_pct=0,
                 team="None", insta_kill_pct = 0, trait_tag = ("None", "None"), amp=0, season_count=0, undead_chance=0,
                 trait_multiplier=None):

        primary_trait_tag = trait_tag[0]
        secondary_trait_tag = trait_tag[1]
        trait_trans = {'$l' : 'Slasher', 'R#' : 'Reflector', 'Hn' : 'Healer', 'Fl' : 'Flasher', 'Sp' : 'Splitter', 'X+' : 'Exploder',
                       'Pp' : 'Playoff Performer', 'C%' : 'Clutch', 'I*' : 'Inconsistent', 'Tx' : 'Toxic', 'U-' : 'Undead', 'V.' : 'Vampire'}
        try:
            primary_tag_param = trait_trans[primary_trait_tag]
        except KeyError:
            primary_tag_param = trait_tag[0]
        try:
            secondary_tag_param = trait_trans[secondary_trait_tag]
        except KeyError:
            secondary_tag_param = trait_tag[1]
        player_params = (amp, tier, primary_tag_param, secondary_tag_param, name, season_count)
        player_sql = """
        INSERT INTO Player(amp, tier, primary_trait, secondary_trait, player_name, season_of_origin)
        VALUES(?, ?, ?, ?, ?, ?)
        """

        #This is a universal number for calculating the impact of traits created AFTER Reflector.
        #Clutch, Inconsistent, and Playoff Performer use this multiplier in a formula contained in
        #a Google Doc called "CONTROL Traits"
        self.trait_multiplier = trait_multiplier

        #C% is assigned during the lineup. If the tick is above 90, it turns to true for the rest of the game
        #I* is assigned at the beginning of each lineup with a roll, the number is the multiplier on power
        #Pp is assigned at the beginning of a game and lasts throughout, the number is added to power
        #ALL TRAITS are removed where they are created. C% should be set to False at the end of a lineup,
        #I* should be set to False at the end of a lineup, and Pp should be set to False at the end of a game
        self.trait_bools = {'C%' : False, 'I*' : 0, 'Pp' : 0}

        self.player_id = QUERY(player_sql, params=player_params, is_select=False)

        #baseline stats
        self.tier = tier
        self.atk_dmg = atk_dmg
        self.atk_spd = atk_spd
        self.insta_kill_pct = insta_kill_pct
        self.crit_pct = crit_pct
        self.mit_pct = mit_pct
        self.defense_abs = defense_abs
        self.defense_pct = defense_pct
        self.crit_x = crit_x
        self.overkill_x = 3
        self.max_health = health #redundant
        self.health = health
        self.power = power
        self.spawn_time = spawn_time
        self.amp = amp
        self.coach_amp = ["None", float(0)]
        self.coach_def_amp = ["None", float(0)]
        self.coach_trait_amp = ["N/A", 0] if trait_tag == "None" else ["None", float(0)]
        self.slot = -1
        self.retired = False
        self.season_of_origin = season_count

        self.drafted = "Not Drafted (Intro)"

        #in-game and in-season stats
        self.delayed_atk = 0
        self.is_alive = True
        self.countdown = 0
        self.atk_counter = 0 #increases every tick; player attacks when this value = atk_spd
        self.kills = 0
        self.crit_kills = 0
        self.deaths = 0
        self.age = 0
        if trait_tag[0] != "None" and trait_tag[1] != "None":
            self.name = f"{trait_tag[0]}-{trait_tag[1]}{name}"
        elif trait_tag[0] != "None" and trait_tag[1] == "None":
            self.name = f"{trait_tag[0]}{name}"
        elif trait_tag[0] == "None" and trait_tag[1] != "None":
            self.name = f"{trait_tag[1]}{name}"
        else:
            self.name = name

        self.crit_dmg = crit_dmg
        self.crit_data = {'Hit' : 0, 'Miss' : 0, 'Ratio' : 0.0, 'Parry' : 0, 'P_Miss' : 0, "P_Ratio" : 0.0, "Mitigated" : 0.0}
        self.grade_data = 0
        self.grade_dict = {'Power' : 0, 'DPS' : 0,'Critical X' : 0, 'Critical %' : 0, 'Health' : 0, 'Spawn Time' : 0, 'Kills' : 0, 'Deaths' : 0, 'Effect' : 0, 'Overkill' : 0, 'Mitigated' : 0, 'Damage' : 0, 'Trait Bonus' : 0, 'Rank' : -1}
        self.ratio = -1
        self.team = team.replace('*','').replace('!-','').replace('-!','').replace('#','')
        self.dps = self.atk_dmg / self.atk_spd
        self.no_power = 0
        self.kill_streak = {'Current' : 0, 'Peak' : 0}
        self.damage_data = {'Tesseract' : 0.0, 'Total-Attacks' : 0, 'Total-Damage' : 0.0, 'Total-Delayed-Damage' : 0.0, 'Reflected' : 0.0, 'Crit-Reflects' : 0, 'Reflect-Count' : 0,
                            'Total-Delayed-X' : 0.0, 'Delayed-Count' : 0, 'Avg-Delayed-X' : 0.0, 'D% Blocked' : 0.0, "DAbs Blocked" : 0.0,
                            'Avg-Delayed-Damage' : 0.0, 'Overkill' : 0.0, 'Overkill-Count' : 0,
                            'Revived' : 0, 'Healed' : 0, 'Reflect-Kills' : 0, 'Explosion' : 0, 'Explosion-Kills' : 0,
                            'Toxin' : 0, 'Toxin Kills' : 0, 'Attacks Stunned' : 0,
                            'Vampire Healed' : 0, 'Extra Attacks' : 0, 'Team Healed' : 0,
                            'Ticks Alive' : 0, 'Ticks Dead' : 0,}
        self.games_played = {'All' : 0, 'This-Season' : 0, 'Playoffs' : 0, 'Matches' : 0}
        self.game_wins = 0 #explicitly refers to this season
        self.game_losses = 0 #only refers to this season
        self.game_stats = []
        self.team_wins = 0 #refers to games (lineups), NOT matches
        self.team_losses = 0

        self.xWAR_breakdown = ""
        self.breakout = False

        self.trait_tag = trait_tag #Can equal $l, U-, R#, C%, I*, Pp!, or X+ as of 11/09
        self.status = {"Stun" : [0,None], "Toxin" : [0,0,None], "Bloodlust" : 0, "Armor Lock" : 0}

        self.xWAR = self.get_xWAR()

    def __str__(self):
        if self.deaths != 0:
            self.ratio = round((self.kills/self.deaths),4)

        tag_str = f" ({self.trait_multiplier})"


        if self.kills != 0:

            holder = f"{self.name}{tag_str}\n" \
            f"\t{self.team}\n"\
            f"xWAR: {self.xWAR} (Rank {self.grade_dict['Rank']})\n" \
            f"Attack Damage: {self.atk_dmg}\n" \
            f"Attack Speed: {self.atk_spd}\n" \
            f"Crit %: {self.crit_pct}\n" \
            f"Mitigate %: {self.mit_pct}\n" \
            f"Defense Absolute: {self.defense_abs}\n"\
            f"Defense %: {self.defense_pct}\n"\
            f"Crit X: {self.crit_x}\n" \
            f"Health: {self.max_health}\n" \
            f"Power: {self.power}\n" \
            f"Spawn Time: {self.spawn_time}\n" \
            f"AGE: {self.age}\n\n"
        else:
            holder = f"{self.name}{tag_str}\n" \
            f"\t{self.team}\n" \
            f"xWAR: {self.xWAR} (Rank {self.grade_dict['Rank']})\n" \
            f"Attack Damage: {self.atk_dmg}\n" \
            f"Attack Speed: {self.atk_spd}\n" \
            f"Crit %: {self.crit_pct}\n" \
            f"Mitigate %: {self.mit_pct}\n" \
            f"Defense Absolute: {self.defense_abs}\n" \
            f"Defense %: {self.defense_pct}\n" \
            f"Crit X: {self.crit_x}\n" \
            f"Health: {self.max_health}\n" \
            f"Power: {self.power}\n" \
            f"Spawn Time: {self.spawn_time}\n" \
            f"AGE: {self.age}\n\n"
        return holder

    def reflect_damage(self, receiver, crit=False):
        #note that receiver, as in receiving the damage, is the attacker in an attack(), and self is the defender
        dmg = (receiver.atk_dmg*receiver.crit_x) if crit else receiver.atk_dmg
        dmg *= self.coach_trait_amp[1] if self.coach_trait_amp[0] == 'R#' else 1
        receiver.health -= dmg
        self.damage_data['Total-Damage'] += dmg
        self.damage_data['Reflected'] += dmg
        self.damage_data['Reflect-Count'] += 1
        if crit:
            self.damage_data['Crit-Reflects'] += 1
        if receiver.health <= 0:
            # game checks for defender life status after the attack function is over
            undead_roll = uniform(0, 1)
            coach_amp_increment = receiver.coach_trait_amp[1] if receiver.coach_trait_amp[0] == 'U-' else 1
            undead_roll = undead_roll / coach_amp_increment
            if 'U-' in receiver.trait_tag and undead_roll <= receiver.trait_multiplier['U-']:
                receiver.damage_data['Healed'] += (receiver.max_health * (2.25*receiver.trait_multiplier['U-']) * coach_amp_increment) - receiver.health
                receiver.damage_data['Revived'] += 1
                receiver.health = (receiver.max_health * (2.25*receiver.trait_multiplier['U-']) * coach_amp_increment)

            else:
                receiver.die()
                self.damage_data['Overkill'] += abs(3 * receiver.health) if '$l' not in self.trait_tag else abs(3.75 * receiver.health)
                self.damage_data['Overkill-Count'] += 1
                receiver.deaths += 1
                self.damage_data['Reflect-Kills'] += 1
                self.kills += 1
                self.kill_streak['Current'] += 1
                self.delayed_atk = 0


    def attack(self, defender, captain_bonus=None, protector_bonus=None, clutch=False, defending_capt = 0): #defending_capt is the damage reduction factor for the defender's captain. If the captain is dead, the value is 0.
        reflected=False
        if self.status["Stun"][0] > 0:
            self.status["Stun"][1].damage_data['Attacks Stunned'] += 1
            return 0
        if "Sp" in self.trait_tag and uniform(0, 1) <= self.trait_multiplier['Sp'] or (self.coach_trait_amp[0] == "Sp" and uniform(0, 1) <= self.coach_trait_amp[1]):
            self.atk_counter = self.atk_spd-1
            self.damage_data['Extra Attacks'] += 1
        else:
            self.atk_counter = 0
        self.damage_data['Total-Attacks'] += 1
        if "Tx" in self.trait_tag and uniform(0,1) < self.trait_multiplier['Tx'][0]:
            if defender.status["Toxin"][1] > 0:
                defender.status["Toxin"][0] += self.trait_multiplier['Tx'][1][0]
                defender.status["Toxin"][1] = mean([self.trait_multiplier['Tx'][1][1], defender.status["Toxin"][1]])
                defender.status["Toxin"][2] = self
            else:
                defender.status["Toxin"] = [self.trait_multiplier['Tx'][1][0], self.trait_multiplier['Tx'][1][1], self]
            #toxin status: damage, ticks
            #if defender already has toxin applied, we add the amount of ticks to the current amount and average the
            #amount of damage taken in case toxin is taken from two separate sources.
            #Sometimes, players will not be properly credited with toxin damage if someone applies more toxin before theirs
            #is done, but there is no way around this.
        elif "Fl" in self.trait_tag and uniform(0,1) < self.trait_multiplier['Fl'][0]:
            defender.status["Stun"] = [self.trait_multiplier['Fl'][1], self]
        damage = self.atk_dmg
        damage += self.coach_amp[1] if self.coach_amp[0] == "Attack Damage" else 0
        damage *= (1 + self.delayed_atk)
        if clutch:
            damage *= self.trait_multiplier['C%']
            damage *= self.coach_trait_amp[1] if self.coach_trait_amp[0] == 'C%' else 1
            damage += 2
        if self.delayed_atk > 0:
            self.damage_data['Total-Delayed-Damage'] += damage
            self.damage_data['Total-Delayed-X'] += self.delayed_atk
            self.damage_data['Delayed-Count'] += 1
        crit = False
        crit_roll = uniform(0, 1)
        coach_crit_increment = self.coach_amp[1] if self.coach_amp[0] == "Critical Chance" else 0
        if captain_bonus:
            capt_crit_increment = captain_bonus[2]
        else:
            capt_crit_increment = 1

        if crit_roll <= ((self.crit_pct + coach_crit_increment) * capt_crit_increment) and self.insta_kill_pct == 0:
            damage *= self.crit_x
            if captain_bonus:
                damage *= captain_bonus[1]
            crit = True
            if self.crit_data:
                self.crit_data['Hit'] += 1
        else:
            if self.crit_data:
                self.crit_data['Miss'] += 1

        parry_roll = uniform(0,1)
        coach_mit_increment = defender.coach_def_amp[1] if defender.coach_def_amp[0] == "Mitigated %" else 0
        if parry_roll <= (defender.mit_pct + coach_mit_increment): #if defender mitigates damage
            if defender.crit_data:
                defender.crit_data['Parry'] += 1
                defender.crit_data['Mitigated'] += damage

            if 'R#' in defender.trait_tag:
                temp_atkr = self
                defender.reflect_damage(temp_atkr,crit)
                reflected = True
            damage = 0

        else:
            if defender.crit_data:
                defender.crit_data['P_Miss'] += 1

        if 'R#' in defender.trait_tag and not reflected: #if the reflector has already parried the attack, it should not have the chance to reflect again
            reflect_roll = uniform(0,1)
            if reflect_roll <= defender.trait_multiplier['R#']:
                temp_atkr = self
                defender.reflect_damage(temp_atkr,crit)
                reflected=True

        if captain_bonus:
            damage*=captain_bonus[0]

        damage -= (damage*defender.defense_pct)
        damage -= defender.defense_abs
        if defender.coach_def_amp[0] == "Defense %":
            damage -= (damage * defender.coach_def_amp[1])

        if defender.coach_def_amp[0] == "Defense Absolute":
            damage -= defender.coach_def_amp[1]

        defender.damage_data['D% Blocked'] += (damage * defender.defense_pct)
        defender.damage_data['DAbs Blocked'] += defender.defense_abs


        if not reflected:

            if defending_capt != 0:
                defending_capt_damage = damage * defending_capt
                damage -= defending_capt_damage
            else:
                defending_capt_damage = 0

            defender.health -= damage
        else:
            defending_capt_damage = 0


        self.damage_data['Total-Damage'] += damage
        if "V." in self.trait_tag and uniform(0,1) < self.trait_multiplier['V.']:
            vamp_heal = damage*(uniform(0.5,0.7))
            self.health += vamp_heal
            self.damage_data['Vampire Healed'] += vamp_heal
        if defender.health <= 0:
            #lineup checks for defender life status after the attack function is over
            if 'U-' in defender.trait_tag:
                undead_roll = uniform(0, 1)
                coach_amp_increment = defender.coach_trait_amp[1] if defender.coach_trait_amp[0] == 'U-' else 1
                undead_roll = undead_roll / coach_amp_increment

                if undead_roll <= defender.trait_multiplier['U-']:
                    defender.damage_data['Healed'] += (defender.max_health * (2*defender.trait_multiplier['U-']) * coach_amp_increment) - defender.health
                    defender.damage_data['Revived'] += 1
                    defender.health = (defender.max_health * (2*defender.trait_multiplier['U-']) * coach_amp_increment)
                    self.delayed_atk = 0

                else:
                    defender.die()
                    if '$l' not in self.trait_tag:
                        self.damage_data['Overkill'] += abs(3 * defender.health)
                        self.damage_data['Tesseract'] += abs(3 * defender.health)
                    else:
                        self.damage_data['Overkill'] += abs(4 * defender.health)
                        self.damage_data['Tesseract'] += abs(4 * defender.health)
                    self.damage_data['Overkill-Count'] += 1
                    defender.deaths += 1
                    if crit:
                        self.crit_kills += 1
                    self.kills += 1
                    self.kill_streak['Current'] += 1
                    self.delayed_atk = 0

            else:
                defender.die()
                if '$l' not in self.trait_tag:
                    self.damage_data['Overkill'] += abs(3 * defender.health)
                    self.damage_data['Tesseract'] += abs(3 * defender.health)
                else:
                    self.damage_data['Overkill'] += abs(4 * defender.health)
                    self.damage_data['Tesseract'] += abs(4 * defender.health)
                self.damage_data['Overkill-Count'] += 1
                defender.deaths += 1
                if crit:
                    self.crit_kills += 1
                self.kills += 1
                self.kill_streak['Current'] += 1
                self.delayed_atk = 0

        else:
            self.delayed_atk = 0
        return defending_capt_damage

    def die(self):
        self.no_power += 1
        self.is_alive = False
        self.countdown = self.spawn_time
        if self.kill_streak['Current'] >= self.kill_streak['Peak']:
            self.kill_streak['Peak'] = self.kill_streak['Current']
        self.kill_streak['Current'] = 0
        self.status["Toxin"] = [0,0,None]
        self.status["Stun"] = [0,None]
        if 'X+' in self.trait_tag:
            self.trait_multiplier['X+'][1] = 1 #

    #These are variables coming from Game() passed when a player's trait is active.
    #When nothing is passed, they default to 0.
    def tesseract(self,clutch=False,inc=0,pp=0,capt_bonus=0):
        impact = self.power
        if clutch:
            impact *= self.trait_multiplier['C%']
            impact = round(impact*self.coach_trait_amp[1]) if self.coach_trait_amp[0] == 'C%' else impact
            impact += 1
        elif inc != 0:
            impact*=inc
        elif pp != 0:
            impact += pp
        if self.coach_amp[0] == "Power":
            coach_power_roll = uniform(0,1)
            if coach_power_roll <= self.coach_amp[1]:
                impact+=choice([1,1,1,2,2])
        if capt_bonus != 0:
            impact += capt_bonus

        self.damage_data['Tesseract'] += impact
        return impact

    def respawn(self):
        self.health = self.max_health
        self.is_alive = True

    def take_damage(self,dmg):
        #this function is only used when damage is taken from a source other than a base attack
        #so far, this only includes Exploder damage and Toxin damage
        self.health -= dmg
        if self.health <= 0:
            #lineup checks for life status after the attack function is over
            undead_roll = uniform(0, 1)
            coach_amp_increment = self.coach_trait_amp[1] if self.coach_trait_amp[0] == 'U-' else 1
            undead_roll = undead_roll / coach_amp_increment
            if 'U-' in self.trait_tag and undead_roll <= self.trait_multiplier['U-']:
                self.damage_data['Healed'] += (self.max_health * (2*self.trait_multiplier['U-']) * coach_amp_increment) - self.health
                self.damage_data['Revived'] += 1
                self.health = (self.max_health * (2.25*self.trait_multiplier['U-']) * coach_amp_increment)
                self.delayed_atk = 0
            else:
                self.die()
                self.deaths += 1
                if 'X+' in self.trait_tag: #when exploders die from toxin or explosion, they cannot do explosion damage, so it doubles for next time
                    self.trait_multiplier['X+'][1] += 1

    def get_xWAR(self,averages=None,set_stats=None,deviations=None):
        row = {
            "Power": self.power,
            "Critical Chance": self.crit_pct,
            "Critical Multiplier": self.crit_x,
            "Max Health": self.max_health,
            "Spawn Time": self.spawn_time,
            "Attack Damage": self.atk_dmg,
            "Attack Speed": self.atk_spd,

            "Primary Trait_R#": 0,
            "Primary Trait_X+": 0,
            "Primary Trait_Hn": 0,
            "Primary Trait_Fl": 0,
            "Primary Trait_Sp": 0,

            "Secondary Trait_C%": 0,
            "Secondary Trait_I*": 0,
            "Secondary Trait_Pp": 0,
            "Secondary Trait_U-": 0,
            "Secondary Trait_Tx": 0,
            "Secondary Trait_V.": 0,

            "Mitigation Chance": self.mit_pct,
            "Defense %": self.defense_pct,
            "Defense Absolute": self.defense_abs
        }

        # turn on trait columns
        if self.trait_tag[0] and self.trait_tag[0] != "None":
            row[f"Primary Trait_{self.trait_tag[0]}"] = 1

        if self.trait_tag[1] and self.trait_tag[1] != "None":
            row[f"Secondary Trait_{self.trait_tag[1]}"] = 1

        player_df = pd.DataFrame([row])

        xWAR = bst.predict(player_df)[0]

        return round(xWAR, 3)


