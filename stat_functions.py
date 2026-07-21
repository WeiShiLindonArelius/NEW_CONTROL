import sqlite3
from scipy.stats import binomtest
from colorama import Fore
import numpy as np
from Players import NO_SQL
import pandas as pd

def QUERY(sql, connect=sqlite3.connect('ControlDataBase.db'), params=None, is_select=False):
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

def clear_all_databases():
    connect = sqlite3.connect('ControlDataBase.db')
    query = "DROP TABLE IF EXISTS Game;"
    QUERY(query, connect, is_select=False)

    query = "DROP TABLE IF EXISTS Match;"
    QUERY(query, connect, is_select=False)

    query = "DROP TABLE IF EXISTS Series;"
    QUERY(query, connect, is_select=False)

    query = "DROP TABLE IF EXISTS Coach;"
    QUERY(query, connect, is_select=False)

    query = "DROP TABLE IF EXISTS TeamSeason;"
    QUERY(query, connect, is_select=False)

    query = "DROP TABLE IF EXISTS Team;"
    QUERY(query, connect, is_select=False)

    query = "DROP TABLE IF EXISTS Player;"
    QUERY(query, connect, is_select=False)

    query = "DROP TABLE IF EXISTS PlayerSeason;"
    QUERY(query, connect, is_select=False)

    query = "DROP TABLE IF EXISTS CoachSeason;"
    QUERY(query, connect, is_select=False)

    query = "DROP TABLE IF EXISTS CaptainSeason;"
    QUERY(query, connect, is_select=False)
def initiate_databases():
    connect = sqlite3.connect("ControlDataBase.db")

    query = """ CREATE TABLE IF NOT EXISTS Team (
                    team_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    coach_id INTEGER REFERENCES Coach(coach_id) DEFERRABLE INITIALLY DEFERRED,
                    team_name TEXT,
                    region_of_origin TEXT,
                    season_of_origin INTEGER)
        """
    QUERY(query, connect, is_select=False)
    query = """ CREATE TABLE IF NOT EXISTS Player (
                    player_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amp REAL,
                    tier TEXT,
                    primary_trait TEXT,
                    secondary_trait TEXT,
                    player_name TEXT,
                    season_of_origin INTEGER)
        """
    QUERY(query, connect, is_select=False)

    query = """ CREATE TABLE IF NOT EXISTS PlayerSeason (
                    player_season_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER REFERENCES Player(player_id) DEFERRABLE INITIALLY DEFERRED,
                    season_count INTEGER,
                    team_id INTEGER REFERENCES Team(team_id) DEFERRABLE INITIALLY DEFERRED,
                    team_season_id INTEGER REFERENCES TeamSeason(team_season_id) DEFERRABLE INITIALLY DEFERRED,
                    amp REAL,
                    tier TEXT,
                    games INTEGER,
                    matches INTEGER,
                    games_per_match REAL,
                    xWAR REAL,
                    primary_trait TEXT,
                    secondary_trait TEXT,
                    player_name TEXT,
                    season_of_origin INTEGER,
                    power REAL,
                    atk_dmg REAL,
                    atk_spd INTEGER,
                    crit_pct REAL,
                    crit_x REAL,
                    mit_pct REAL,
                    defense_abs REAL,
                    defense_pct REAL,
                    health REAL,
                    spawn_time INTEGER,
                    age INTEGER,
                    kills REAL,
                    deaths REAL,
                    ticks_alive REAL,
                    ticks_dead REAL,
                    crit_kills REAL,
                    damage REAL,
                    mitigated REAL,
                    defense_pct_blocked REAL,
                    defense_abs_blocked REAL,
                    attacks REAL,
                    total_effect REAL,
                    overkill_effect REAL,
                    non_overkill_effect REAL,
                    overkill_effect_pct REAL,
                    primary_trait_stat_1 BLOB,
                    primary_trait_stat_2 BLOB,
                    secondary_trait_stat_1 BLOB,
                    secondary_trait_stat_2 BLOB)
        """
    QUERY(query, connect, is_select=False)


    query = """ CREATE TABLE IF NOT EXISTS Series (
                                series_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                season_count INTEGER,
                                winning_team_id INTEGER REFERENCES Team(team_id),
                                losing_team_id INTEGER REFERENCES Team(team_id),
                                winning_team_season_id INTEGER REFERENCES Team(team_id),
                                losing_team_season_id INTEGER REFERENCES Team(team_id),
                                winning_seed BLOB,
                                losing_seed BLOB,
                                seed_diff BLOB,
                                winner_name TEXT,
                                loser_name TEXT,
                                series_score TEXT,
                                _0N_score TEXT,
                                _1N_score TEXT,
                                _2N_score TEXT,
                                _3N_score TEXT,
                                _4N_score TEXT,
                                _5N_score TEXT,
                                _6N_score TEXT,
                                series_game_score TEXT,
                                context TEXT)        
                    """
    QUERY(query, connect, is_select=False)
    #regional_playoff_seed = 0 if the team started in the universal league
    #for last_stand, pre_qualifying, and uni_qualifying, there are four possibilities (exclude no. 3 for uni_qualifying obviously)
    # 0 - failed to qualify
    # 1 - qualified, failed to advance
    # 2 - qualified, advanced
    # 3 - advanced with a bye
    # playoff_seed, both regional and universal, includes the standing of the teams which did not make the playoffs
    # team_id comes from Team.team_id
    # coach_id comes from Team.team_coach.coach_id
    # region_of_origin comes from Team.region
    # season_of_origin comes from Team.season_origin
    # everything else comes from Team.team_seasons[season_count].variable
    query = """ CREATE TABLE IF NOT EXISTS TeamSeason (
                                team_season_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                team_id INTEGER REFERENCES Team(team_id),
                                coach_id INTEGER REFERENCES Coach(coach_id),
                                slot_0_season_id INTEGER REFERENCES PlayerSeason(player_season_id) DEFERRABLE INITIALLY DEFERRED,
                                slot_1_season_id INTEGER REFERENCES PlayerSeason(player_season_id) DEFERRABLE INITIALLY DEFERRED,
                                slot_2_season_id INTEGER REFERENCES PlayerSeason(player_season_id) DEFERRABLE INITIALLY DEFERRED,
                                slot_3_season_id INTEGER REFERENCES PlayerSeason(player_season_id) DEFERRABLE INITIALLY DEFERRED,
                                slot_4_season_id INTEGER REFERENCES PlayerSeason(player_season_id) DEFERRABLE INITIALLY DEFERRED,
                                slot_5_season_id INTEGER REFERENCES PlayerSeason(player_season_id) DEFERRABLE INITIALLY DEFERRED,
                                team_name TEXT,
                                season_count INTEGER,
                                region_started TEXT,
                                xWAR BLOB,
                                started_universal_league BOOLEAN,
                                regional_playoff_seed INTEGER,
                                regional_final_seed INTEGER, 
                                last_stand INTEGER,
                                pre_qualifying INTEGER,
                                uni_qualifying INTEGER,
                                ended_universal_league BOOLEAN,
                                uni_playoff_seed INTEGER,
                                uni_final_seed INTEGER)        
                    """
    QUERY(query, connect, is_select=False)

    query = """ CREATE TABLE IF NOT EXISTS Coach (
                    coach_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    team_id INTEGER REFERENCES Team(team_id) DEFERRABLE INITIALLY DEFERRED,
                    coach_name TEXT,
                    lineup_modifier TEXT,
                    slots_amped TEXT,
                    attribute_amped TEXT,
                    attribute_amp_mult REAL,
                    trait_amped TEXT,
                    trait_amp_mult REAL,
                    match_wins INTEGER,
                    match_losses INTEGER,
                    match_draws INTEGER)
        """
    QUERY(query, connect, is_select=False)


    query = """ CREATE TABLE IF NOT EXISTS CoachSeason (
                coach_id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_season_id INTEGER REFERENCES TeamSeason(team_season_id) DEFERRABLE INITIALLY DEFERRED,
                coach_name TEXT,
                lineup_modifier TEXT,
                slots_amped TEXT,
                attribute_amped TEXT,
                attribute_amp_mult REAL,
                trait_amped TEXT,
                trait_amp_mult REAL,
                match_wins INTEGER,
                match_losses INTEGER,
                match_draws INTEGER)
    """
    QUERY(query, connect, is_select=False)

    query = """ CREATE TABLE IF NOT EXISTS CaptainSeason (
                    captain_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    team_season_id INTEGER REFERENCES TeamSeason(team_season_id) DEFERRABLE INITIALLY DEFERRED,
                    captain_name TEXT,
                    dmg_taken REAL,
                    health REAL,
                    base_dmg_bonus REAL,
                    crit_dmg REAL,
                    power_bonus REAL,
                    pct_ticks_alive REAL)
        """
    QUERY(query, connect, is_select=False)


    return 0


def write_to_file(filename=None, words=None, mode='w', error=False):
    if error:
        filename = 'error_output'
        mode = 'a'

    with open(filename, mode) as f:
        f.write(words + '\n')



def finalize_series_data():
    query = """
        UPDATE Series
        SET winning_seed = 
    CASE
        WHEN instr(winner_name, '(') = 0 OR instr(winner_name, ')') = 0 THEN CAST('n/a' AS BLOB)
        ELSE CAST(
                substr(
                    winner_name, 
                    instr(winner_name, '(') + 1, 
                    instr(winner_name, ')') - instr(winner_name, '(') - 1
                ) AS INTEGER
            )
    END;  """
    QUERY(query)
    query = """
        UPDATE Series
        SET losing_seed = 
    CASE
        WHEN instr(loser_name, '(') = 0 OR instr(loser_name, ')') = 0 THEN CAST('n/a' AS BLOB)
        ELSE CAST(
                substr(
                    loser_name, 
                    instr(loser_name, '(') + 1, 
                    instr(loser_name, ')') - instr(loser_name, '(') - 1
                ) AS INTEGER
            )
    END;  """
    QUERY(query)
    query = """
    UPDATE Series
    SET seed_diff = CASE
        WHEN winning_seed LIKE '%n/a%' OR losing_seed LIKE '%n/a%' THEN CAST('n/a' AS BLOB)
        ELSE (winning_seed - losing_seed)
        END;
    """
    QUERY(query)


def series_test(wins, losses):
    result = binomtest(wins, wins+losses, 0.50)
    p_val = result.pvalue
    np.set_printoptions(precision=4, suppress=True)
    return Fore.RED + f"There is a {round((p_val*100),2)}% chance the result was due to chance alone." + Fore.RESET