import math
import sqlite3
from random import randint, choice, seed, uniform
from stat_functions import series_test, QUERY
from colorama import Fore, Back, Style
from statistics import mean
import pandas as pd
import numpy as np
from seed import generate_seed
import re
from switches import game_length

import sys

def nothing():
    pass

def no_op(args):
    pass

def blockPrint():
    sys.stdout = nothing()

def enablePrint():
    sys.stdout = sys.__stdout__

def write_to_file(filename=None, words=None, mode='w', error=False):
    if error:
        filename = 'error_output'
        mode = 'a'

    with open(filename, mode) as f:
        f.write(words + '\n')


TEST_OUTPUT = False

connect = sqlite3.connect("ControlDataBase.db")

def game(team1, team2, amp=4, type_of='None', playoff_dict=None, playoffs=False,one_league=False):
    # enable / disable to have a constant / non-constant amp
    if amp != 4:
        amp = 4
    for ply in team1.players:
        ply.no_power = 0
        ply.is_alive = True
    for ply in team2.players:
        ply.no_power = 0
        ply.is_alive = True


    #At the moment, this will apply Pp and I*
    def apply_traits_before_lineup(t1lineup, t2lineup):
        for player in t1lineup:
            player.atk_counter = 0
            if 'I*' in player.trait_tag:
                inc_roll = uniform(0,1)
                if player.coach_trait_amp[0] == 'I*':
                    extra_inc_roll = uniform(0,1)
                else:
                    extra_inc_roll = 0
                if inc_roll <= player.trait_multiplier['I*'] or extra_inc_roll <= player.coach_trait_amp[1]:
                    player.trait_bools['I*'] = randint(105,125) / 100
                elif np.logical_and(inc_roll >= player.trait_multiplier['I*'], inc_roll <= (player.trait_multiplier['I*']*2)):
                    player.trait_bools['I*'] = randint(70,90) / 100
            elif 'Pp' in player.trait_tag and playoffs:
                add = 2
                pp1_roll = randint(0, 100)
                add += choice([0, 1, 1, 1, 2, 2, 3]) if pp1_roll % 2 == 0 else 1
                add += 1 if pp1_roll % 3 == 0 else 0
                add += 3 if pp1_roll <= (player.trait_multiplier['Pp'] * 100) else 0
                add += 2 if pp1_roll <= (player.trait_multiplier['Pp'] * 100) - 15 else 0
                add += 2 if pp1_roll <= (player.trait_multiplier['Pp'] * 100) - 30 else 0
                add += 2 if pp1_roll <= (player.trait_multiplier['Pp'] * 100) - 45 else 0
                add += player.coach_trait_amp[1] if player.coach_trait_amp[0] == 'Pp' else 0
                player.trait_bools['Pp'] = add
        for player in t2lineup:
            player.atk_counter = 0
            if 'I*' in player.trait_tag:
                inc_roll = uniform(0, 1)
                if player.coach_trait_amp[0] == 'I*':
                    extra_inc_roll = uniform(0,1)
                else:
                    extra_inc_roll = 0

                if inc_roll <= player.trait_multiplier['I*'] or extra_inc_roll <= player.coach_trait_amp[1]:
                    player.trait_bools['I*'] = randint(105, 125) / 100
                elif np.logical_and(inc_roll >= player.trait_multiplier['I*'], inc_roll <= (player.trait_multiplier['I*'] * 2)):
                    player.trait_bools['I*'] = randint(70, 90) / 100
            elif 'Pp' in player.trait_tag and playoffs:
                add = 2
                pp2_roll = randint(0, 100)
                add += choice([0,1,1,1,2,2,3])  if pp2_roll % 2 == 0 else 1
                add += 1 if pp2_roll % 3 == 0 else 0
                add += 3 if pp2_roll <= (player.trait_multiplier['Pp']*100) else 0
                add += 2 if pp2_roll <= (player.trait_multiplier['Pp'] * 100) - 15 else 0
                add += 2 if pp2_roll <= (player.trait_multiplier['Pp'] * 100) - 30 else 0
                add += 2 if pp2_roll <= (player.trait_multiplier['Pp'] * 100) - 45 else 0
                add += player.coach_trait_amp[1] if player.coach_trait_amp[0] == 'Pp' else 0
                player.trait_bools['Pp'] = add

    def remove_traits_after_lineup(t1lineup, t2lineup):
        for player in t1lineup:
            player.trait_bools = {'C%' : False, 'I*' : 0, 'Pp' : 0}
        for player in t2lineup:
            player.trait_bools = {'C%' : False, 'I*' : 0, 'Pp' : 0}

    def apply_living_tick_data(team1p, team2p, living_team1, living_team2):
        for player in team1p:
            if player in living_team1:
                player.damage_data['Ticks Alive'] += 1
            else:
                player.damage_data['Ticks Dead'] += 1
        for player in team2p:
            if player in living_team2:
                player.damage_data['Ticks Alive'] += 1
            else:
                player.damage_data['Ticks Dead'] += 1


    def apply_tick_effects(team1p, team2p, living_team1, living_team2, yta_team1, yta_team2, tick, TESSERACT):
        for player in team1p:
            if "Hn" in player.trait_tag and (tick % player.trait_multiplier['Hn'][0] == 0 or player.trait_multiplier['Hn'][2]):
                coach_bonus = 10 if (team1.team_coach.trait_effect[0] == 'Hn' and uniform(0,1) < team1.team_coach.trait_effect[1]) else 0
                if player in living_team1:
                    player.damage_data['Team Healed'] += player.trait_multiplier['Hn'][1]
                    amt = (player.trait_multiplier['Hn'][1] + coach_bonus) / len(living_team1)
                    for plr in living_team1:
                        plr.health += amt
                    player.trait_multiplier['Hn'][2] = False
                else:
                    player.trait_multiplier['Hn'][2] = True
        for player in team2p:
            if "Hn" in player.trait_tag and (tick % player.trait_multiplier['Hn'][0] == 0 or player.trait_multiplier['Hn'][2]):
                coach_bonus = 10 if (team2.team_coach.trait_effect[0] == 'Hn' and uniform(0, 1) < team2.team_coach.trait_effect[1]) else 0
                if player in living_team2:
                    player.damage_data['Team Healed'] += player.trait_multiplier['Hn'][1]
                    amt = (player.trait_multiplier['Hn'][1] + coach_bonus) / len(living_team2)
                    for plr in living_team2:
                        plr.health += amt
                    player.trait_multiplier['Hn'][2] = False
                else:
                    player.trait_multiplier['Hn'][2] = True


        for player in living_team1:
            if player.status["Toxin"][1] > 0:
                toxin_dealer = player.status["Toxin"][2]
                coach_tx_bonus = team2.team_coach.trait_effect[1] if team2.team_coach.trait_effect[0] == 'Tx' else 1
                player.status["Toxin"][1] -= 1
                toxin_dealer.damage_data['Toxin'] += player.status["Toxin"][1]
                toxin_dealer.damage_data['Total-Damage'] += player.status["Toxin"][1]
                player.take_damage(player.status["Toxin"][0]*coach_tx_bonus)
                if not player.is_alive:
                    toxin_dealer.damage_data['Toxin Kills'] += 1
                    toxin_dealer.kills += 1
                    # if player is killed by toxin
                    living_team1.remove(player)
                    if player in yta_team1:
                        TESSERACT -= abs(3 * player.health)
                        toxin_dealer.damage_data['Overkill'] += abs(3 * player.health)
                        yta_team1.remove(player)

            if player.status["Stun"][0] > 0:
                player.status["Stun"][0] -= 1


        for player in living_team2:
            toxin_dealer = player.status["Toxin"][2]
            coach_tx_bonus = team1.team_coach.trait_effect[1] if team1.team_coach.trait_effect[0] == 'Tx' else 1
            if player.status["Toxin"][1] > 0:
                player.status["Toxin"][1] -= 1
                toxin_dealer.damage_data['Toxin'] += player.status["Toxin"][1]
                toxin_dealer.damage_data['Total-Damage'] += player.status["Toxin"][1]
                player.take_damage(player.status["Toxin"][0]*coach_tx_bonus)
                if not player.is_alive:
                    toxin_dealer.damage_data['Toxin Kills'] += 1
                    toxin_dealer.kills += 1
                    # if player is killed by toxin
                    living_team2.remove(player)
                    if player in yta_team2:
                        TESSERACT += abs(3 * player.health)
                        toxin_dealer.damage_data['Overkill'] += abs(3 * player.health)
                        yta_team2.remove(player)
            if player.status["Stun"][0] > 0:
                player.status["Stun"][0] -= 1


    def lineup(team1_lineup, team2_lineup, lineup_index, team1=team1, team2=team2, tiebreak=False):

        team1_captain_alive = (team1.captain.max_health > 0) #Test "non-captains" have 0 max health, should be initialized as dead
        team2_captain_alive = (team2.captain.max_health > 0)
        team1_capt_damage_reduction = team1.captain.damage_taken #this is passed into attack when the respective team is defending
        team2_capt_damage_reduction = team2.captain.damage_taken

        team1.captain.health = team1.captain.max_health
        team2.captain.health = team2.captain.max_health

        #todo create function apply_captain_bonus and apply_protector_bonus which will set bonus values for each player in the following format:
        # captain: [life status, atk spd bonus, atk dmg bonus, critical mult bonus]
        # protector: [life status, mit% bonus, defense absolute]
        # in attack(), the life status will be checked when relevant, and a bonus will be applied if the status is True

        seed(generate_seed())

        for player in team1_lineup:
            player.health = player.max_health
        for player in team2_lineup:
            player.health = player.max_health

        #write_to_file(mode='a', words=f"Lineup start between {team1.name} and {team2.name}")

        #team1_lineup and team2_lineup objects being passed into this function are LISTs OF PLAYERS
        apply_traits_before_lineup(team1_lineup, team2_lineup)

        TESSERACT = 0
        length = game_length
        #length *= amp
        length += 1

        for tick in range(1, length):
            living_team1 = []
            living_team2 = []
            yta_team1 = []
            yta_team2 = []
            if team1_captain_alive:
                team1.living_captain[0] += 1
                team1_capt_damage_reduction = team1.captain.damage_taken
            else:
                team1.living_captain[1] += 1
                team1_capt_damage_reduction = 0
            if team2_captain_alive:
                team2.living_captain[0] += 1
                team2_capt_damage_reduction = team2.captain.damage_taken
            else:
                team2.living_captain[1] += 1
                team2_capt_damage_reduction = 0

            for pl in team1_lineup:
                if pl.is_alive:
                    pl.atk_counter+=1
                    living_team1.append(pl)
                    yta_team1.append(pl)
                elif pl.countdown == 0:
                    pl.respawn()
                    living_team1.append(pl)
                    yta_team1.append(pl)
                else:
                    pl.countdown -= 1

            for pl in team2_lineup:
                if pl.is_alive:
                    pl.atk_counter += 1
                    living_team2.append(pl)
                    yta_team2.append(pl)
                elif pl.countdown == 0:
                    pl.respawn()
                    living_team2.append(pl)
                    yta_team2.append(pl)
                else:
                    pl.countdown -= 1

            #applying clutch for games of length 72
            if playoffs:
                clutch_time = 50
            else:
                clutch_time = 52

            if tick >= clutch_time or ((tick >= (clutch_time - 12)) and abs(TESSERACT) <= 100):
                for player in living_team1:
                    if 'C%' in player.trait_tag:
                        player.trait_bools['C%'] = True
                for player in living_team2:
                    if 'C%' in player.trait_tag:
                        player.trait_bools['C%'] = True


            #Basic Gameplay Loop:
            #team (alternating) chooses a random living player who has not yet attacked this turn (if there is one)
            #if tick%atk_spd=0, or they have a delayed attack, a random living enemy player is chosen if there is one.
            #if not, the attacker gets delayed_attack+=1, meaning the next time he is yet to attack during a tick and there is a living player,
            #he will attack regardless of the tick%atk_spd.
            #if there is no living team 1 player who has not yet attacked, the above process happens for team 2
            #this continues, alternating between team 1 attacking first and team 2 attacking first via the sub_count,
            #and the while loop breaks when there are no players on either team who are alive and yet to attack
            #once the loop breaks, the next tick begins in the larger for loop

            apply_tick_effects(team1_lineup, team2_lineup, living_team1, living_team2, yta_team1, yta_team2, tick, TESSERACT)
            apply_living_tick_data(team1_lineup, team2_lineup, living_team1, living_team2)
            sub_count = choice([0,1])
            while True:
                sub_count += 1
                if not living_team1 and not living_team2:
                    break
                if sub_count%2 == 0: #team 1 attacking
                    if yta_team1:
                        attacker = choice(yta_team1)
                        yta_team1.remove(attacker)
                        if attacker.atk_counter == attacker.atk_spd or attacker.delayed_atk != 0:
                            if living_team2:
                                defender = choice(living_team2)
                                if team1_captain_alive:
                                    team2_capt_damage_taken = attacker.attack(defender, clutch=attacker.trait_bools['C%'],
                                                                              captain_bonus=[team1.captain.atk_dmg_bonus, team1.captain.crit_x_bonus,
                                                                              team1.captain.crit_pct_bonus],
                                                                              defending_capt = team2_capt_damage_reduction)
                                else:
                                    team2_capt_damage_taken = attacker.attack(defender,clutch=attacker.trait_bools['C%'], defending_capt = team2_capt_damage_reduction)
                                if team2_captain_alive:
                                    team2.captain.health -= team2_capt_damage_taken
                                    if team2.captain.health <= 0:
                                        team2_captain_alive = False
                                        team2_capt_damage_reduction = 0
                                if not defender.is_alive:
                                    # if defender is killed
                                    living_team2.remove(defender)
                                    if defender in yta_team2:
                                        yta_team2.remove(defender)
                                    #deal explosion damage to all living players on team 1 if defender is an exploder
                                    if 'X+' in defender.trait_tag:
                                        for player in living_team1:
                                            coach_damage_increment = defender.coach_trait_amp[1] if defender.coach_trait_amp[0] == 'X+' else 0
                                            player.take_damage(defender.trait_multiplier['X+'][0]*defender.trait_multiplier['X+'][1] + coach_damage_increment)
                                            defender.damage_data['Explosion'] += defender.trait_multiplier['X+'][0]*defender.trait_multiplier['X+'][1]
                                            defender.damage_data['Total-Damage'] += defender.trait_multiplier['X+'][0]*defender.trait_multiplier['X+'][1]
                                            if not player.is_alive:
                                                living_team1.remove(player)
                                                if player in yta_team1:
                                                    yta_team1.remove(player)
                                                defender.damage_data['Explosion-Kills'] += 1
                                                defender.kills += 1
                                    #Overkill impact
                                    if '$l' in attacker.trait_tag:
                                        if team1.team_coach.trait_effect[0] != '$l':
                                            TESSERACT += abs(4 * defender.health)
                                        else:
                                            TESSERACT += abs((4+team1.team_coach.trait_effect[1]) * defender.health)
                                    else:
                                        TESSERACT += abs(3 * defender.health)
                                elif 'R#' in defender.trait_tag and not attacker.is_alive: #this can happen when lethal damage is reflected back because reflect_damage happens within the attack function
                                    if attacker in living_team1: #it is possible for attacker to die to explosion damage, which will remove them from living_team1
                                        living_team1.remove(attacker)
                                        if attacker in yta_team1:
                                            yta_team1.remove(attacker)
                                    TESSERACT -= abs(3*attacker.health)
                            else:
                                attacker.delayed_atk = 1
                        if attacker.no_power == 0:
                            TESSERACT += attacker.tesseract(clutch=attacker.trait_bools['C%'],
                                                            inc=attacker.trait_bools['I*'],
                                                            pp=attacker.trait_bools['Pp'],
                                                            capt_bonus = team1.captain.power_bonus if team1_captain_alive else 0)
                        else:
                            attacker.no_power -= 1
                    elif yta_team2:
                        #TEAM2 DELAYED ATTACK
                        attacker = choice(yta_team2)
                        yta_team2.remove(attacker)
                        if attacker.atk_counter == attacker.atk_spd or attacker.delayed_atk != 0:
                            if living_team1:
                                defender = choice(living_team1)
                                if team2_captain_alive:
                                    team1_capt_damage_taken = attacker.attack(defender,
                                                                              clutch=attacker.trait_bools['C%'],
                                                                              captain_bonus=[
                                                                                  team2.captain.atk_dmg_bonus,
                                                                                  team2.captain.crit_x_bonus,
                                                                              team2.captain.crit_pct_bonus],
                                                                              defending_capt=team1_capt_damage_reduction)
                                else:
                                    team1_capt_damage_taken = attacker.attack(defender,
                                                                              clutch=attacker.trait_bools['C%'],
                                                                              defending_capt=team1_capt_damage_reduction)
                                if team1_captain_alive:
                                    team1.captain.health -= team1_capt_damage_taken
                                    if team1.captain.health <= 0:
                                        team1_captain_alive = False
                                        team1_capt_damage_reduction = 0
                                # if attacker is a splasher, run the splash damage roll here and attack all enemies if the roll returns true
                                if not defender.is_alive:
                                    # if defender is killed
                                    living_team1.remove(defender)
                                    if defender in yta_team1:
                                        yta_team1.remove(defender)
                                    # deal explosion damage to all living players on team 2 if defender is an exploder
                                    if 'X+' in defender.trait_tag:
                                        for player in living_team2:
                                            coach_damage_increment = defender.coach_trait_amp[1] if \
                                            defender.coach_trait_amp[0] == 'X+' else 0
                                            player.take_damage(defender.trait_multiplier['X+'][0]*defender.trait_multiplier['X+'][1] + coach_damage_increment)
                                            defender.damage_data['Explosion'] += defender.trait_multiplier['X+'][0]*defender.trait_multiplier['X+'][1]
                                            defender.damage_data['Total-Damage'] += defender.trait_multiplier['X+'][0]*defender.trait_multiplier['X+'][1]
                                            if not player.is_alive:
                                                living_team2.remove(player)
                                                if player in yta_team2:
                                                    yta_team2.remove(player)
                                                defender.damage_data['Explosion-Kills'] += 1
                                                defender.kills += 1
                                    # Overkill impact
                                    if '$l' in attacker.trait_tag:
                                        if team2.team_coach.trait_effect[0] != '$l':
                                            TESSERACT += abs(4 * defender.health)
                                        else:
                                            TESSERACT += abs((4+team2.team_coach.trait_effect[1]) * defender.health)
                                    else:
                                        TESSERACT -= abs(3 * defender.health)
                                elif 'R#' in defender.trait_tag and not attacker.is_alive:  # this can happen when lethal damage is reflected back
                                    if attacker in living_team2:  # it is possible for attacker to die to explosion damage, which will remove them from living_team2
                                        living_team2.remove(attacker)
                                        if attacker in yta_team2:
                                            yta_team2.remove(attacker)
                                    TESSERACT += abs(3 * attacker.health)
                            else:
                                attacker.delayed_atk = 1
                        if attacker.no_power == 0:
                            TESSERACT -= attacker.tesseract(clutch=attacker.trait_bools['C%'],
                                                            inc=attacker.trait_bools['I*'],
                                                            pp=attacker.trait_bools['Pp'],
                                                            capt_bonus = team2.captain.power_bonus if team2_captain_alive else 0)
                        else:
                            attacker.no_power -= 1
                    else:
                        break
                elif sub_count%2 == 1: #team 2 attacking
                    if yta_team2:
                        attacker = choice(yta_team2)
                        yta_team2.remove(attacker)
                        if attacker.atk_counter == attacker.atk_spd or attacker.delayed_atk != 0:
                            if living_team1:
                                defender = choice(living_team1)
                                if team2_captain_alive:
                                    team1_capt_damage_taken = attacker.attack(defender,
                                                                              clutch=attacker.trait_bools['C%'],
                                                                              captain_bonus=[
                                                                                  team2.captain.atk_dmg_bonus,
                                                                                  team2.captain.crit_x_bonus,
                                                                              team2.captain.crit_pct_bonus],
                                                                              defending_capt=team1_capt_damage_reduction)
                                else:
                                    team1_capt_damage_taken = attacker.attack(defender,
                                                                              clutch=attacker.trait_bools['C%'],
                                                                              defending_capt=team1_capt_damage_reduction)
                                if team1_captain_alive:
                                    team1.captain.health -= team1_capt_damage_taken
                                    if team1.captain.health <= 0:
                                        team1_captain_alive = False
                                        team1_capt_damage_reduction = 0
                                # if attacker is a splasher, run the splash damage roll here and attack all enemies if the roll returns true
                                if not defender.is_alive:
                                    # if defender is killed
                                    living_team1.remove(defender)
                                    if defender in yta_team1:
                                        yta_team1.remove(defender)
                                    #deal explosion damage to all living players on team 2 if defender is an exploder
                                    if 'X+' in defender.trait_tag:
                                        for player in living_team2:
                                            coach_damage_increment = defender.coach_trait_amp[1] if defender.coach_trait_amp[0] == 'X+' else 0
                                            player.take_damage(defender.trait_multiplier['X+'][0]*defender.trait_multiplier['X+'][1] + coach_damage_increment)
                                            defender.damage_data['Explosion'] += defender.trait_multiplier['X+'][0]*defender.trait_multiplier['X+'][1]
                                            defender.damage_data['Total-Damage'] += defender.trait_multiplier['X+'][0]*defender.trait_multiplier['X+'][1]
                                            if not player.is_alive:
                                                living_team2.remove(player)
                                                if player in yta_team2:
                                                    yta_team2.remove(player)
                                                defender.damage_data['Explosion-Kills'] += 1
                                                defender.kills += 1
                                    #Overkill impact
                                    if '$l' in attacker.trait_tag:
                                        if team2.team_coach.trait_effect[0] != '$l':
                                            TESSERACT += abs(4 * defender.health)
                                        else:
                                            TESSERACT += abs((4+team2.team_coach.trait_effect[1]) * defender.health)
                                    else:
                                        TESSERACT -= abs(3 * defender.health)
                                elif 'R#' in defender.trait_tag and not attacker.is_alive: #this can happen when lethal damage is reflected back
                                    if attacker in living_team2:  # it is possible for attacker to die to explosion damage, which will remove them from living_team2
                                        living_team2.remove(attacker)
                                        if attacker in yta_team2:
                                            yta_team2.remove(attacker)
                                    TESSERACT += abs(3*attacker.health)
                            else:
                                attacker.delayed_atk = 1
                        if attacker.no_power == 0:
                            TESSERACT -= attacker.tesseract(clutch=attacker.trait_bools['C%'],
                                                            inc=attacker.trait_bools['I*'],
                                                            pp=attacker.trait_bools['Pp'],
                                                            capt_bonus = team2.captain.power_bonus if team2_captain_alive else 0)
                        else:
                            attacker.no_power -= 1
                    elif yta_team1:
                        #TEAM1 DELAYED ATTACK
                        attacker = choice(yta_team1)
                        yta_team1.remove(attacker)
                        if attacker.atk_counter == attacker.atk_spd or attacker.delayed_atk != 0:
                            if living_team2:
                                defender = choice(living_team2)
                                if team1_captain_alive:
                                    team2_capt_damage_taken = attacker.attack(defender,clutch=attacker.trait_bools['C%'],
                                                                              captain_bonus=[
                                                                                  team1.captain.atk_dmg_bonus,
                                                                                  team1.captain.crit_x_bonus,
                                                                              team1.captain.crit_pct_bonus],
                                                                              defending_capt=team2_capt_damage_reduction)
                                else:
                                    team2_capt_damage_taken = attacker.attack(defender,
                                                                              clutch=attacker.trait_bools['C%'],
                                                                              defending_capt=team2_capt_damage_reduction)
                                if team2_captain_alive:
                                    team2.captain.health -= team2_capt_damage_taken
                                    if team2.captain.health <= 0:
                                        team2_captain_alive = False
                                        team2_capt_damage_reduction = 0
                                if not defender.is_alive:
                                    # if defender is killed
                                    living_team2.remove(defender)
                                    if defender in yta_team2:
                                        yta_team2.remove(defender)
                                    # deal explosion damage to all living players on team 1 if defender is an exploder
                                    if 'X+' in defender.trait_tag:
                                        for player in living_team1:
                                            coach_damage_increment = defender.coach_trait_amp[1] if \
                                            defender.coach_trait_amp[0] == 'X+' else 0
                                            player.take_damage(defender.trait_multiplier['X+'][0]*defender.trait_multiplier['X+'][1] + coach_damage_increment)
                                            defender.damage_data['Explosion'] += defender.trait_multiplier['X+'][0]*defender.trait_multiplier['X+'][1]
                                            defender.damage_data['Total-Damage'] += defender.trait_multiplier['X+'][0]*defender.trait_multiplier['X+'][1]
                                            if not player.is_alive:
                                                living_team1.remove(player)
                                                if player in yta_team1:
                                                    yta_team1.remove(player)
                                                defender.damage_data['Explosion-Kills'] += 1
                                                defender.kills += 1
                                    # Overkill impact
                                    if '$l' in attacker.trait_tag:
                                        if team1.team_coach.trait_effect[0] != '$l':
                                            TESSERACT += abs(4 * defender.health)
                                        else:
                                            TESSERACT += abs((4+team1.team_coach.trait_effect[1]) * defender.health)
                                    else:
                                        TESSERACT += abs(3 * defender.health)
                                elif 'R#' in defender.trait_tag and not attacker.is_alive:  # this can happen when lethal damage is reflected back because reflect_damage happens within the attack function
                                    if attacker in living_team1:  # it is possible for attacker to die to explosion damage, which will remove them from living_team1
                                        living_team1.remove(attacker)
                                        if attacker in yta_team1:
                                            yta_team1.remove(attacker)
                                    TESSERACT -= abs(3 * attacker.health)
                            else:
                                attacker.delayed_atk = 1
                        if attacker.no_power == 0:
                            TESSERACT += attacker.tesseract(clutch=attacker.trait_bools['C%'],
                                                            inc=attacker.trait_bools['I*'],
                                                            pp=attacker.trait_bools['Pp'],
                                                            capt_bonus = team1.captain.power_bonus if team1_captain_alive else 0)
                        else:
                            attacker.no_power -= 1
                    else:
                        break
        for player in team2_lineup:
            player.games_played['This-Season'] += 1
        for player in team1_lineup:
            player.games_played['This-Season'] += 1

        remove_traits_after_lineup(team1_lineup, team2_lineup)
        if TESSERACT > 0: #Team 1 wins
            for player in team1_lineup:
                player.game_wins += 1
            for player in team2_lineup:
                player.game_losses += 1
            for player in team1.players:
                player.team_wins +=1
            for player in team2.players:
                player.team_losses +=1

            team1.wins += 1
            team1.margin += abs(round(TESSERACT,2))
            team1.lineup_wins[lineup_index] += 1
            team2.losses += 1
            team2.margin -= abs(round(TESSERACT,2))
            team2.lineup_losses[lineup_index] += 1
            return team1
        else: #Team 2 wins
            for player in team2_lineup:
                player.game_wins += 1
            for player in team1_lineup:
                player.game_losses += 1
            for player in team1.players:
                player.team_wins +=1
            for player in team2.players:
                player.team_losses +=1

            team1.losses += 1
            team1.margin -= abs(round(TESSERACT,2))
            team1.lineup_losses[lineup_index] += 1
            team2.wins += 1
            team2.margin += abs(round(TESSERACT,2))
            team2.lineup_wins[lineup_index] += 1
            return team2
        #end of lineup()

    lineup_count = 0
    team1_lineups_won = 0
    team2_lineups_won = 0

    for tp1 in team1.players:
        tp1.games_played['Matches'] += 1
    for tp2 in team2.players:
        tp2.games_played['Matches'] += 1


    if one_league:
        winner = lineup(team1.players,team2.players,team1=team1,team2=team2,lineup_index=0)
        if winner == team1:
            team1.match_wins+=1
            team2.match_losses+=1
        elif winner == team2:
            team2.match_wins += 1
            team1.match_losses+=1
        return winner

    if not playoff_dict:
        lw = [None for _ in range(9)]
        while team1_lineups_won < 4 and team2_lineups_won < 4 and lineup_count < 6:
            #in the regular season, lineup score of 3-3 is a draw
            winner = lineup(team1.lineups[lineup_count],team2.lineups[lineup_count], lineup_index=lineup_count, team1=team1, team2=team2)
            lw[lineup_count] = winner.team_id
            if winner == team1:
                team1_lineups_won += 1
            elif winner == team2:
                team2_lineups_won += 1
            lineup_count += 1
        if team1_lineups_won > team2_lineups_won:
            #match_params = (team1.team_id, team2.team_id, f"{team1_lineups_won}-{team2_lineups_won}",
            #                lw[0], lw[1], lw[2], lw[3], lw[4], lw[5], lw[6], lw[7], lw[8], 'No')
            #match_query = """
            #INSERT INTO Match (winning_team_id, losing_team_id, match_score, _0N_winner_id, _1N_winner_id, _2N_winner_id, _3N_winner_id, _4N_winner_id, _5N_winner_id, _6N_winner_id, _7N_winner_id, _8N_winner_id, playoffs)
            #VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            #"""
            #QUERY(match_query, connect, params=match_params, is_select=False)


            team1.match_wins += 1
            team2.match_losses += 1
            return team1
        elif team2_lineups_won > team1_lineups_won:
            #match_params = (team2.team_id, team1.team_id, f"{team2_lineups_won}-{team1_lineups_won}",
            #                lw[0], lw[1], lw[2], lw[3], lw[4], lw[5], lw[6], lw[7], lw[8],
            #                'No')
            #match_query = """
            #            INSERT INTO Match (winning_team_id, losing_team_id, match_score, _0N_winner_id, _1N_winner_id,
            #            _2N_winner_id, _3N_winner_id, _4N_winner_id, _5N_winner_id, _6N_winner_id, _7N_winner_id, _8N_winner_id, playoffs)
            #            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            #            """
            #QUERY(match_query, connect, params=match_params, is_select=False)

            team2.match_wins += 1
            team1.match_losses += 1
            return team2
        else:
            temp_winner = choice([team1, team2])
            #temp_loser = team1 if temp_winner == team2 else team2
            #match_params = (temp_winner.team_id, temp_loser.team_id, f"{team1_lineups_won}-{team2_lineups_won}",
            #                lw[0], lw[1], lw[2], lw[3], lw[4], lw[5], lw[6], lw[7], lw[8],
            #                'No')
            #match_query = """
            #            INSERT INTO Match (winning_team_id, losing_team_id, match_score, _0N_winner_id, _1N_winner_id,
            #            _2N_winner_id, _3N_winner_id, _4N_winner_id, _5N_winner_id, _6N_winner_id, _7N_winner_id, _8N_winner_id, playoffs)
            #            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            #            """
            #QUERY(match_query, connect, params=match_params, is_select=False)

            team1.match_draws += 1
            team2.match_draws += 1
            return temp_winner

    elif playoff_dict:
        lw = [None for _ in range(9)]

        #playoffs equals a dictionary which looks like
        # playoff_objects = {"Team 1 Series Lineups Won" : team1_alt_lineup_wins, "Team 1 Series Lineups Lost" : team1_alt_lineup_losses,
        #                        "Team 2 Series Lineups Won" : team2_alt_lineup_wins, "Team 2 Series Lineups Lost" : team2_alt_lineup_losses,
        #                        "Average Score Dictionary" : avg_match_score}
        playoff_dict['Team 1 Tiebreaker Wins'] = [0,0,0]
        playoff_dict['Team 2 Tiebreaker Wins'] = [0,0,0]

        while team1_lineups_won < 4 and team2_lineups_won < 4:
            if team1_lineups_won == 3 and team2_lineups_won == 3:
                winner = lineup(team1.lineups[lineup_count], team2.lineups[lineup_count], lineup_index=lineup_count,
                                team1=team1, team2=team2, tiebreak=True)
            else:
                winner = lineup(team1.lineups[lineup_count], team2.lineups[lineup_count], lineup_index=lineup_count,
                                team1=team1, team2=team2)
                lw[lineup_count] = winner.team_id
            if winner == team1:
                playoff_dict["Team 1 Series Lineups Won"][lineup_count] += 1
                playoff_dict["Team 2 Series Lineups Lost"][lineup_count] += 1

                team1_lineups_won += 1
            elif winner == team2:
                playoff_dict["Team 2 Series Lineups Won"][lineup_count] += 1
                playoff_dict["Team 1 Series Lineups Lost"][lineup_count] += 1

                team2_lineups_won += 1

            lineup_count += 1

        playoff_dict["Game Count"] += 1
        playoff_dict["Total Score Dictionary"]["Team 1 Total Lineup Wins"] += team1_lineups_won
        playoff_dict["Total Score Dictionary"]["Team 2 Total Lineup Wins"] += team2_lineups_won

        if team1_lineups_won > team2_lineups_won:
            #match_params = (team1.team_id, team2.team_id, f"{team1_lineups_won}-{team2_lineups_won}",
            #                lw[0], lw[1], lw[2], lw[3], lw[4], lw[5], lw[6], lw[7], lw[8],
            #                'Yes')
            #match_query = """
            #            INSERT INTO Match (winning_team_id, losing_team_id, match_score, _0N_winner_id, _1N_winner_id, _2N_winner_id, _3N_winner_id, _4N_winner_id, _5N_winner_id, _6N_winner_id, _7N_winner_id, _8N_winner_id, playoffs)
            #            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            #            """
            #QUERY(match_query, connect, params=match_params, is_select=False)
            return team1
        elif team2_lineups_won > team1_lineups_won:
            #match_params = (team2.team_id, team1.team_id, f"{team2_lineups_won}-{team1_lineups_won}",
            #                lw[0], lw[1], lw[2], lw[3], lw[4], lw[5], lw[6], lw[7], lw[8],
            #                'Yes')
            #match_query = """
            #            INSERT INTO Match (winning_team_id, losing_team_id, match_score, _0N_winner_id, _1N_winner_id, _2N_winner_id, _3N_winner_id, _4N_winner_id, _5N_winner_id, _6N_winner_id, _7N_winner_id, _8N_winner_id, playoffs)
            #            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            #            """
            #QUERY(match_query, connect, params=match_params, is_select=False)
            return team2

def best_of(team1,team2,thresh,amp=4,both_return=False,win_by=1,test_output=False,is_uni=False, context=None, advantage=0,skunk=None):

    t_dec_index = 0
    decrease_count = 0
    failsafe_count = 0

    trigger = win_by_immutable = win_by

    end_decrease = math.floor(win_by_immutable / 2.5)

    blockPrint()
    team1_wins = 0 + advantage
    team2_wins = 0
    game_count = 0

    season_count = int(context.split()[0][1:])

    if skunk:
        skunk_thresh = skunk[0]
        skunk_win_by = skunk[1]
    else:
        skunk_thresh = float('inf')
        skunk_win_by = float('inf')

    team1_alt_lineup_wins = [0] * 7
    team1_alt_lineup_losses = [0] * 7
    team2_alt_lineup_wins = [0] * 7
    team2_alt_lineup_losses = [0] * 7
    total_match_score = {"Team 1 Total Lineup Wins" : 0, "Team 2 Total Lineup Wins" : 0}

    playoff_objects = {"Team 1 Series Lineups Won" : team1_alt_lineup_wins, "Team 1 Series Lineups Lost" : team1_alt_lineup_losses,
                       "Team 2 Series Lineups Won" : team2_alt_lineup_wins, "Team 2 Series Lineups Lost" : team2_alt_lineup_losses,
                       "Total Score Dictionary" : total_match_score, "Game Count" : 0, "Team 1 Tiebreaker Wins" : [0,0,0],
                       "Team 2 Tiebreaker Wins" : [0,0,0]}

    def print_lineup_score(team1_lineup_wins, team1_lineup_losses, team2_lineup_wins, team2_lineup_losses,
                           team1_total_wins, team2_total_wins, team1_tb_wins, team2_tb_wins):
        #team1 is the WINNING TEAM, and team2 is the LOSING TEAM, regardless of what they are in the game
        length = 0
        total_games_played = team1_total_wins + team2_total_wins
        output_str = " ["
        if len(team1_lineup_wins) == len(team2_lineup_wins):
            length = len(team1_lineup_wins)

        for i in range(length):
            if team2_lineup_wins[i] > team1_lineup_wins[i]:
                output_str += "*"
            output_str += f"{i}N({team1_lineup_wins[i]}-{team2_lineup_wins[i]})"
            if team2_lineup_wins[i] > team1_lineup_wins[i]:
                output_str += "*"
            if i < length-1:
                output_str += ", "
            #the below code is part of an abandoned project to make each tiebreaker a 2 of 3 instead of one game
            #else:
            #    output_str += " |"
            #    for num in [0,1,2]:
            #        output_str += f"{team1_tb_wins[num]}-{team2_tb_wins[num]}"
            #        if num != 2:
            #            output_str += ", "
            #    output_str += "|"

        non_sweeps = team1_lineup_wins[4] + team2_lineup_wins[4]
        sweeps = total_games_played - non_sweeps

        tiebreak_games_played = team1_lineup_wins[6] + team2_lineup_wins[6]
        output_str += f"] TOTAL: {sum(team1_lineup_wins)}-{sum(team2_lineup_wins)}"
        tiebreak_str = f" ({tiebreak_games_played} of {total_games_played}" \
                       f" [{(tiebreak_games_played / total_games_played)*100:.2f}%] reached a tiebreak, and " \
                       f"{sweeps} of {total_games_played} [{(sweeps / total_games_played)*100:.2f}%]" \
                       f" were 4-0 sweeps.)"
        #



        return output_str, tiebreak_str

    def print_score_update(t1, t1_wins, t2, t2_wins, margin_str=""):
        #this function will print an update of the score in a playoff series when the game count equals any direct multiple of thresh,
        # and every time the margin decreases
        if advantage == 0:
            ad_string = ""
        elif team2_wins > team1_wins:
            ad_string = f" start ↓ 0-{advantage} and "
        else:
            ad_string = f" start ↑ {advantage}-0 and "

        if team1_wins > team2_wins:
            print(f"{t1.name}({t1.seed}){ad_string} lead {t2.name}({t2.seed}) by a score of {t1_wins}-{t2_wins}." + margin_str)
        elif team2_wins > team1_wins:
            print(f"{t2.name}({t2.seed}){ad_string} lead {t1.name}({t1.seed}) by a score of {t2_wins}-{t1_wins}." + margin_str)
        else:
            print(f"{t1.name}({t1.seed}){ad_string} are tied with {t2.name}({t2.seed}) by a score of {t1_wins}-{t2_wins}." + margin_str)



    playoffs = True if "Playoffs" in context or "Play-In" in context or "Relegation Match" in context else False
    enablePrint()
    if advantage:
        ad_string = f"start ↑ {advantage}-0 "
    else:
        ad_string = ""
    print(Fore.CYAN +
          f"{team1.name}({team1.seed}) {ad_string}VS {team2.name}({team2.seed})" + Fore.RESET )
    no_dec = True #this value means that the margin has not yet begun to decrease OR if it can no longer decrease
    team1_max_deficit = 0
    team2_max_deficit = 0
    team1_deficit_str = ""
    team2_deficit_str = ""
    skunk_bool = (abs(team1_wins - team2_wins) > skunk_win_by and (team1_wins > skunk_thresh or team2_wins > skunk_thresh))
    while (abs(team1_wins - team2_wins) < win_by or (team1_wins < thresh and team2_wins < thresh)) and not skunk_bool: #this loop is the series itself
        winner = game(team1, team2, amp, playoff_dict=playoff_objects,playoffs=playoffs)

        team1_wins += 1 if winner == team1 else 0
        team2_wins += 1 if winner == team2 else 0
        game_count += 1

        if team1_wins > team2_wins:
            lead = team1_wins-team2_wins
            if lead > team2_max_deficit:
                team2_max_deficit = lead
                team2_deficit_str = f"{team2_wins}-{team1_wins}"
        if team2_wins > team1_wins:
            lead = team2_wins-team1_wins
            if lead > team1_max_deficit:
                team1_max_deficit = lead
                team1_deficit_str = f"{team1_wins}-{team2_wins}"
        if game_count % thresh == 0 and no_dec:
            print_score_update(team1, team1_wins, team2, team2_wins)
        if game_count > math.floor(thresh*2.5) and decrease_count < end_decrease: #in each game after 2.5 * the initial game limit, the trigger ticks once
            t_dec_index += 1
        if t_dec_index == trigger and decrease_count <= end_decrease: #once the trigger hits, the margin needed to win the series is decreased by 1
            if decrease_count < end_decrease:
                win_by -= 1
                decrease_count += 1
                t_dec_index = 0
                no_dec = False  # margin decreasing every [win_by] games
                if decrease_count == end_decrease:
                    no_dec = True  # margin no longer decreasing
                    print_score_update(team1, team1_wins, team2, team2_wins,
                                   margin_str=f" The margin decreases from {win_by + 1} to {win_by}. The margin is {win_by} and can no longer decrease.")
                else:
                    print_score_update(team1, team1_wins, team2, team2_wins,
                                       margin_str=f" The margin decreases from {win_by + 1} to {win_by}.")

        #but, if the margin decreases by more than a third of its original value, it will not decrease further

    #if decrease_count != 0:
        #write_to_file(error=True, words = f"\nIn a series between {team1.name} and {team2.name}, the margin was decreased from {win_by_immutable} to {win_by}."
        #                                  f"\nThe margin was decreased every {trigger} matches after reaching {thresh*5} matches.\n")
        #if decrease_count == end_decrease:
        #    write_to_file(error=True, words=f"The limit of {end_decrease} was hit in this series, meaning that the margin of victory stuck at {win_by}")

    for player in team2.players:
        player.games_played['Playoffs'] += 1
    for player in team1.players:
        player.games_played['Playoffs'] += 1

    #reminder playoff_objects = {"Team 1 Series Lineups Won" : team1_alt_lineup_wins, "Team 1 Series Lineups Lost" : team1_alt_lineup_losses,
    #                   "Team 2 Series Lineups Won" : team2_alt_lineup_wins, "Team 2 Series Lineups Lost" : team2_alt_lineup_losses,
    #                   "Average Score Dictionary" : avg_match_score}

    #t1_avg_series_wins = playoff_objects["Total Score Dictionary"]["Team 1 Total Lineup Wins"] / game_count
    #t2_avg_series_wins = playoff_objects["Total Score Dictionary"]["Team 2 Total Lineup Wins"] / game_count

    t1_region_seed_str = f"({team1.region_seed})" if "Pre-Qualifying" in context else ""
    t2_region_seed_str = f"({team2.region_seed})" if "Pre-Qualifying" in context else ""
    if skunk_bool:
        skunk_str = "SKUNK: "
    else:
        skunk_str = ""

    if team1_wins > team2_wins:
        lineup_statement, tiebreak_statement = print_lineup_score(team1_lineup_wins=playoff_objects['Team 1 Series Lineups Won'],
                                              team1_lineup_losses=playoff_objects['Team 1 Series Lineups Lost'],
                                              team2_lineup_wins=playoff_objects['Team 2 Series Lineups Won'],
                                              team2_lineup_losses=playoff_objects['Team 2 Series Lineups Lost'],
                                              team1_total_wins=team1_wins, team2_total_wins=team2_wins,
                                              team1_tb_wins=playoff_objects['Team 1 Tiebreaker Wins'],
                                              team2_tb_wins=playoff_objects['Team 2 Tiebreaker Wins'])

        try:
            series_params = (season_count,
                             team1.team_id, team2.team_id,
                             team1.team_seasons[season_count].team_season_id,
                             team2.team_seasons[season_count].team_season_id,
                         team1.seed, team2.seed, (team1.seed - team2.seed),
                         (f"({team1.seed}){team1.name}" if context != 'Last Stand Tournament' else team1.name),
                         (f"({team2.seed}){team2.name}" if context != 'Last Stand Tournament' else team2.name),
                         f"{team1_wins}-{team2_wins}",
                         f"{team1_alt_lineup_wins[0]}-{team2_alt_lineup_wins[0]}",
                         f"{team1_alt_lineup_wins[1]}-{team2_alt_lineup_wins[1]}",
                         f"{team1_alt_lineup_wins[2]}-{team2_alt_lineup_wins[2]}",
                         f"{team1_alt_lineup_wins[3]}-{team2_alt_lineup_wins[3]}",
                         f"{team1_alt_lineup_wins[4]}-{team2_alt_lineup_wins[4]}",
                         f"{team1_alt_lineup_wins[5]}-{team2_alt_lineup_wins[5]}",
                         f"{team1_alt_lineup_wins[6]}-{team2_alt_lineup_wins[6]}",
                         f"{sum(team1_alt_lineup_wins)}-{sum(team2_alt_lineup_wins)}",
                         context)
            series_query = """
            INSERT INTO Series(season_count, winning_team_id, losing_team_id, winning_team_season_id, losing_team_season_id, winning_seed, losing_seed, seed_diff, winner_name, loser_name, series_score, _0N_score, _1N_score,
                _2N_score, _3N_score, _4N_score, _5N_score, _6N_score, series_game_score, context)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            QUERY(series_query, connect, params=series_params)
        except TypeError:
            pass

        enablePrint()
        # team1 will always have advantage if there is one
        if advantage == 0:
            adv_string = ""
        else:
            adv_string = f"start ↑ {advantage}-0 and "

        if team1_max_deficit > math.floor(0.49*win_by_immutable) or (win_by_immutable >= 60 and team1_max_deficit > math.floor(win_by_immutable/3)):
            comeback_string = f"return from down {team1_deficit_str} to "
        else:
            comeback_string = ""



        if team1.seed != -1:
            final_str = f"{skunk_str}{team1.name}({team1.seed}) {adv_string}{comeback_string}defeat {team2.name}({team2.seed}) by a score of {team1_wins}-{team2_wins}."
            print(Back.RED + Fore.BLACK + final_str + Fore.BLUE + Back.RESET + lineup_statement + Fore.RESET + tiebreak_statement)
        else:
            final_str = f"{skunk_str}{team1.name}{t1_region_seed_str}{comeback_string} defeat {team2.name}{t2_region_seed_str} by a score of {team1_wins}-{team2_wins}."
            print(Back.RED + Fore.BLACK + final_str + Fore.BLUE + Back.RESET + lineup_statement + Fore.RESET + tiebreak_statement)
        if test_output:
            print(series_test(team1_wins, team2_wins))
        print("\t-----")

        if comeback_string != "":
            write_to_file("comebacks", words=(re.sub(r'S\d+\s', '', context) + ': ' + final_str.replace("↑", "up") + '\n'), mode='a', error=False)

        if is_uni:
            team1.accolades['Uni-Playoff-Wins'] += 1
        if not both_return:
            return team1
        else:
            return team1, team2
    else:
        lineup_statement, tiebreak_statement = print_lineup_score(team1_lineup_wins=playoff_objects['Team 2 Series Lineups Won'],
                                              team1_lineup_losses=playoff_objects['Team 2 Series Lineups Lost'],
                                              team2_lineup_wins=playoff_objects['Team 1 Series Lineups Won'],
                                              team2_lineup_losses=playoff_objects['Team 1 Series Lineups Lost'],
                                              team1_total_wins=team2_wins, team2_total_wins=team1_wins,
                                              team1_tb_wins=playoff_objects['Team 2 Tiebreaker Wins'],
                                              team2_tb_wins=playoff_objects['Team 1 Tiebreaker Wins'])

        try:
            series_params = (season_count,
                             team2.team_id, team1.team_id,
                             team2.team_seasons[season_count].team_season_id,
                             team1.team_seasons[season_count].team_season_id,
                             team2.seed, team1.seed, (team2.seed - team1.seed),
                             (f"({team2.seed}){team2.name}" if context != 'Last Stand Tournament' else team1.name),
                             (f"({team1.seed}){team1.name}" if context != 'Last Stand Tournament' else team2.name),
                             f"{team2_wins}-{team1_wins}",
                             f"{team2_alt_lineup_wins[0]}-{team1_alt_lineup_wins[0]}",
                             f"{team2_alt_lineup_wins[1]}-{team1_alt_lineup_wins[1]}",
                             f"{team2_alt_lineup_wins[2]}-{team1_alt_lineup_wins[2]}",
                             f"{team2_alt_lineup_wins[3]}-{team1_alt_lineup_wins[3]}",
                             f"{team2_alt_lineup_wins[4]}-{team1_alt_lineup_wins[4]}",
                             f"{team2_alt_lineup_wins[5]}-{team1_alt_lineup_wins[5]}",
                             f"{team2_alt_lineup_wins[6]}-{team1_alt_lineup_wins[6]}",
                             f"{sum(team2_alt_lineup_wins)}-{sum(team1_alt_lineup_wins)}",
                             context)
            series_query = """
                    INSERT INTO Series(season_count, winning_team_id, losing_team_id, winning_team_season_id, losing_team_season_id, winning_seed, losing_seed, seed_diff, winner_name, loser_name, series_score, _0N_score, _1N_score,
                    _2N_score, _3N_score, _4N_score, _5N_score, _6N_score, series_game_score, context)
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
            QUERY(series_query, connect, params=series_params)
        except TypeError:
            pass


        enablePrint()
        # team1 will always have advantage if there is one
        if advantage == 0:
            adv_string = ""
        else:
            adv_string = f"start ↓ 0-{advantage} and "

        if team2_max_deficit > math.floor(0.49*win_by_immutable) or (win_by_immutable >= 60 and team2_max_deficit > math.floor(win_by_immutable/3)):
            comeback_string = f"return from down {team2_deficit_str} to "
        else:
            comeback_string = ""

        if team2.seed != -1:
            final_str = f"{skunk_str}{team2.name}({team2.seed}) {adv_string}{comeback_string}defeat {team1.name}({team1.seed}) by a score of {team2_wins}-{team1_wins}."
            print(Back.RED + Fore.BLACK + final_str + Fore.BLUE + Back.RESET + lineup_statement + Fore.RESET + tiebreak_statement)
        else:
            final_str = f"{skunk_str}{team2.name}{t2_region_seed_str}{comeback_string} defeat {team1.name}{t1_region_seed_str} by a score of {team2_wins}-{team1_wins}."
            print(Back.RED + Fore.BLACK + final_str + Fore.BLUE + Back.RESET + lineup_statement + Fore.RESET + tiebreak_statement)
        if test_output:
            print(series_test(team2_wins, team1_wins))
        print("\t-----")
        if comeback_string != "":
            write_to_file("comebacks", words=(re.sub(r'S\d+\s', '', context) + ': ' + final_str.replace("↓", "down") + '\n'), mode='a', error=False)
        if is_uni:
            team2.accolades['Uni-Playoff-Wins'] += 1
        if not both_return:
            return team2
        else:
            return team2, team1
