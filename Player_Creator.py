import math

from Players import Player
from random import randint, choice, uniform
import numpy as np
from lists import player_names
names = player_names

#If the reflector trait doesn't hit, this will trigger next.
#This returns "" if the player is not given a trait, and the trait tag along with a multiplier if they are

def new_trait_roll(tier, fixed=("NotNone", "NotNone")):
    fixed = list(fixed)
    primary_tag = "None"
    secondary_tag = "None"
    multiplier = {}
    primary_tag_possibilities = ['R#', 'Hn', 'Fl', 'Sp', 'X+','R#', 'Fl',
                                 'Sp', 'X+','R#', 'Hn', 'Fl', 'Sp', 'X+'] #Healer is 1 in 7, everything else 3 in 14
    if choice([True,False,False,False,False,False,False,False,False,False]):
        primary_tag_possibilities.remove("Hn")
    if choice([True,False,False,False,False,False,False,False,False,False]):
        primary_tag_possibilities.remove("Fl")
    secondary_tag_possibilities = ['Pp', 'C%', 'I*', 'Tx', 'U-', 'V.']
    #this function will roll traits in accordance to the new primary/secondary split
    #a player will have a 40% chance to gain one of 6 primary traits and a 75% chance to gain one of 6 secondary traits
    #trait_mult = {'Prim' : mult, 'Secondary' : mult}. As usual, mult can be a list.
    clutch_lower_bound = 1.1
    inc_lower_bound = 0.05
    pp_lower_bound = 0.3
    explode_lower_bound = 40 #now does raw damage instead of being linked to attack damage
    undead_lower_bound = 0.25
    reflector_lower_bound = 0.1
    splitter_lower_bound = 0.3
    vampire_lower_bound = 0.4
    heal_nova_possibilities = [36, 42, 48, 54]
    heal_tick_possibilities = [13, 13, 12, 12, 11, 11]
    stun_tick_possibilities = [10, 10, 11] #will never hit two attacks
    if tier == 'S':
        heal_nova_possibilities.pop()
        heal_tick_possibilities.pop()
        stun_tick_possibilities.pop()
    if tier == 'A' and choice([True, False]):
        heal_nova_possibilities.pop()
        heal_tick_possibilities.pop()
        stun_tick_possibilities.pop()

    # multipliers for Toxic, Healer, Flasher, have to be selected a different way
    def toxic_mult(upper_bound):
        return [round(uniform(0.25, upper_bound), 2),
                [choice([10, 11, 12, 13]), choice([6, 7, 7, 7, 8, 8])]]  # chance, damage, time

    def healer_mult():
        return [choice(heal_tick_possibilities), choice(heal_nova_possibilities), False]

    def flasher_mult(upper_bound):
        return [round(uniform(0.075, upper_bound), 2), choice(stun_tick_possibilities)]

    if tier == 'S':
        clutch_upperbound = 1.3
        inc_upperbound = 0.15
        pp_upperbound = 0.5
        explode_upperbound = 60
        undead_upperbound = 0.35
        reflector_upperbound = 0.15
        splitter_upper_bound = 0.35
        vampire_upper_bound = 0.55
        toxic_upper_bound = 0.33
        flasher_upper_bound = 0.115
    elif tier == 'A':
        clutch_upperbound = 1.28
        inc_upperbound = 0.14
        pp_upperbound = 0.45
        explode_upperbound = 59
        undead_upperbound = 0.34
        reflector_upperbound = 0.14
        splitter_upper_bound = 0.34
        vampire_upper_bound = 0.54
        toxic_upper_bound = 0.32
        flasher_upper_bound = 0.11
    elif tier == 'B':
        clutch_upperbound = 1.26
        inc_upperbound = 0.13
        pp_upperbound = 0.425
        explode_upperbound = 58
        undead_upperbound = 0.33
        reflector_upperbound = 0.13
        splitter_upper_bound = 0.33
        vampire_upper_bound = 0.53
        toxic_upper_bound = 0.31
        flasher_upper_bound = 0.105
    elif tier == 'C':
        clutch_upperbound = 1.25
        inc_upperbound = 0.12
        pp_upperbound = 0.4
        explode_upperbound = 57
        undead_upperbound = 0.32
        reflector_upperbound = 0.12
        splitter_upper_bound = 0.32
        vampire_upper_bound = 0.52
        toxic_upper_bound = 0.3
        flasher_upper_bound = 0.10
    else:
        # Error handling block; this should never happen
        clutch_upperbound = 1.3
        inc_upperbound = 0.1
        pp_upperbound = 0.14
        explode_upperbound = 55
        undead_upperbound = 0.5
        reflector_upperbound = 0.5
        splitter_upper_bound = 0.15
        vampire_upper_bound = 0.5
        toxic_upper_bound = 0.35
        flasher_upper_bound = 0.21


    #PRIMARY ROLL
    if fixed[0] not in ['R#', 'Hn', 'Fl', 'Sp', 'X+', 'None']: #only roll for trait if player is not already assigned a primary trait
        if uniform(0,1) <= 0.4:
            primary_tag = choice(primary_tag_possibilities)
    else:
        primary_tag = fixed[0]

    if fixed[1] not in ['Pp', 'C%', 'I*', 'Tx', 'U-', 'V.', 'None']:
        if uniform(0,1) <= 0.7 and primary_tag != "Hn": #Healers are too strong to have another trait.
            secondary_tag = choice(secondary_tag_possibilities)
    else:
        secondary_tag = fixed[1]

    #primary_tag_possibilities = ['$l', 'R#', 'Hn', 'Fl', 'Sp', 'X+']
    #secondary_tag_possibilities = ['Pp', 'C%', 'I*', 'Tx', 'U-', 'V.']

    if primary_tag == "$l":
        multiplier.update({"$l": "N/A"})
    elif primary_tag == 'R#':
        multiplier.update({"R#" : round(uniform(reflector_lower_bound, reflector_upperbound), 2)})
    elif primary_tag == 'Hn':
        healer_mult_instance = healer_mult()
        multiplier.update({'Hn' : healer_mult_instance})
    elif primary_tag == 'Fl':
        flasher_mult_instance = flasher_mult(flasher_upper_bound)
        multiplier.update({'Fl' : flasher_mult_instance})
    elif primary_tag == 'Sp':
        multiplier.update({'Sp' : round(uniform(splitter_lower_bound, splitter_upper_bound), 2)})
    elif primary_tag == 'X+':
        multiplier.update(({'X+' : [randint(explode_lower_bound, explode_upperbound), 1]}))

    if secondary_tag == 'Pp':
        multiplier.update({'Pp' : round(uniform(pp_lower_bound, pp_upperbound), 2)})
    if secondary_tag == 'C%':
        multiplier.update({'C%' : round(uniform(clutch_lower_bound, clutch_upperbound), 2)})
    if secondary_tag == 'I*':
        multiplier.update({'I*' : round(uniform(inc_lower_bound, inc_upperbound), 2)})
    if secondary_tag == 'Tx':
        toxic_mult_instance = toxic_mult(toxic_upper_bound)
        multiplier.update({'Tx' : toxic_mult_instance})
    if secondary_tag == 'U-':
        multiplier.update({'U-' : round(uniform(undead_lower_bound, undead_upperbound), 2)})
    if secondary_tag == 'V.':
        multiplier.update({'V.' : round(uniform(vampire_lower_bound, vampire_upper_bound), 2)})

    return [primary_tag, secondary_tag] , multiplier
    # primary_tag = tag str
    # secondary_tag = tag str
    # multiplier = dict with
    #   key = tag
    #   value = mult

def s_tier(amp=0, season_count=-1, pre_reflect=0, trait_amp=0, fixed='None'):

    atk_dmg = randint(53, 63)
    atk_spd = randint(6, 9)
    if amp>=5:
        if atk_spd != 6:
            atk_spd-=1
        else:
            atk_dmg += round(amp*0.67)
    if amp<=-1:
        if atk_spd != 9:
            atk_spd+=1
        else:
            atk_dmg = round(atk_dmg-abs(amp*0.33),2)
    crit_pct = round(((randint(50, 75)) / 1000),4)
    crit_x = round(((randint(650, 900)/100) + (amp * 0.1)), 2)
    mit_pct = round(uniform(0.025, 0.0899), 4)
    defense_abs = round(uniform(4,8))
    defense_pct = round(uniform(0.025,0.075), 4)
    health = round(uniform(205,240),2)
    power = randint(53, 59) #avg 55.5
    spawn_time = choice([6,6,6,6,6,7,7,8])
    # Return a Player object initialized with the generated values

    amp_str = "" if amp == 0 else f"^{amp}"
    tag, mult = new_trait_roll('S', fixed=fixed)
    if tag == "None":
        non_trait_coin = choice([1,1,2,3,4,5,6])
        if non_trait_coin == 1:
            if atk_spd not in [6,7] and choice([True,False]):
                atk_spd -= 1
            else:
                atk_dmg += round(uniform(2,4))
        elif non_trait_coin == 2:
            crit_pct += round(uniform(0.005,0.099),4)
        elif non_trait_coin == 3:
            crit_x += round(uniform(1,2),2)
        elif non_trait_coin == 4:
            health += round(uniform(5,12),2)
        elif non_trait_coin == 5:
            power += choice([0,1,1,1,1,1,1,2,2])
        else:
            if spawn_time != 6 and choice([True,False]):
                spawn_time -= 1
            else:
                if atk_spd not in [6, 7] and choice([True, False]):
                    atk_spd -= 1
                else:
                    atk_dmg += round(uniform(2, 4))

    crit_dmg = atk_dmg * crit_x
    return Player('S', atk_dmg, atk_spd, crit_pct, crit_x, health, power, spawn_time, crit_dmg, mit_pct=mit_pct,defense_pct=defense_pct, defense_abs=defense_abs,
                  name=f"S{amp_str}_{choice(names)}", amp=amp, season_count=season_count,
                  trait_tag=tag, trait_multiplier=mult)




def a_tier(amp=0, season_count=-1, pre_reflect=0, trait_amp=0, fixed='None'):

    atk_dmg = randint(51, 63) + int(amp*0.6)
    atk_spd = randint(6, 9)
    crit_pct = (randint(54, 72))/1000
    crit_x = randint(640, 880)/100
    if amp>=5:
        crit_x = round(crit_x+(amp*0.2),2)
    elif amp<=-1:
        crit_x = round(crit_x-abs(amp*0.9))
    mit_pct = round(uniform(0.0225, 0.0849), 4)
    defense_abs = round(uniform(2.1, 5.75))
    defense_pct = round(uniform(0.026, 0.0625), 4)
    health = round(uniform(200,235),2) + round((4*amp),2)
    power = randint(52, 59) #avg 55
    spawn_time = choice([6,6,6,7,7,7,8,8])
    # Return a Player object initialized with the generated values
    amp_str = "" if amp == 0 else f"^{amp}"
    tag, mult = new_trait_roll('A', fixed=fixed)
    if tag == "None":
        non_trait_coin = choice([1,2,3,4,4,5,6])
        if non_trait_coin == 1:
            if atk_spd not in [6,7] and choice([True,False]):
                atk_spd -= 1
            else:
                atk_dmg += round(uniform(2,4))
        elif non_trait_coin == 2:
            crit_pct += round(uniform(0.005,0.099),4)
        elif non_trait_coin == 3:
            crit_x += round(uniform(1,2),2)
        elif non_trait_coin == 4:
            health += round(uniform(5,12),2)
        elif non_trait_coin == 5:
            power += choice([0,1,1,1,1,1,1,2,2])
        else:
            if spawn_time != 6 and choice([True,False]):
                spawn_time -= 1
            else:
                if atk_spd not in [6, 7] and choice([True, False]):
                    atk_spd -= 1
                else:
                    atk_dmg += round(uniform(2, 4))
    crit_dmg = atk_dmg * crit_x
    return Player('A', atk_dmg, atk_spd, crit_pct, crit_x, health, power, spawn_time, crit_dmg, mit_pct=mit_pct,defense_pct=defense_pct, defense_abs=defense_abs,
                  name=f"A{amp_str}_{choice(names)}", amp=amp, season_count=season_count,
                  trait_tag=tag, trait_multiplier=mult)


def b_tier(amp=0, season_count=-1, pre_reflect=0, trait_amp=0, fixed='None'):

    atk_dmg = randint(50, 61) + int(amp*1.5)
    atk_spd = randint(6, 9)
    crit_pct = (randint(52,72))/1000
    crit_x = randint(625, 875)/100
    mit_pct = round(uniform(0.02, 0.08), 4)
    defense_abs = round(uniform(2.2, 5.5))
    defense_pct = round(uniform(0.027, 0.06), 4)
    health = round(uniform(190,230),2)
    if amp>=5:
        health+=amp*2
    elif amp<=-1:
        health = round(health-abs(amp*10))
    power = randint(51, 58) #avg 54
    spawn_time = choice([6,6,7,7,7,8,8,8])
    # Return a Player object initialized with the generated values
    amp_str = "" if amp == 0 else f"^{amp}"
    tag, mult = new_trait_roll('B', fixed=fixed)
    if tag == "None":
        non_trait_coin = choice([1,2,3,4,5,5,6])
        if non_trait_coin == 1:
            if atk_spd not in [6,7] and choice([True,False]):
                atk_spd -= 1
            else:
                atk_dmg += round(uniform(2,4))
        elif non_trait_coin == 2:
            crit_pct += round(uniform(0.005,0.099),4)
        elif non_trait_coin == 3:
            crit_x += round(uniform(1,2),2)
        elif non_trait_coin == 4:
            health += round(uniform(5,12),2)
        elif non_trait_coin == 5:
            power += choice([0,1,1,1,1,1,1,2,2])
        else:
            if spawn_time != 6 and choice([True,False]):
                spawn_time -= 1
            else:
                if atk_spd not in [6, 7] and choice([True, False]):
                    atk_spd -= 1
                else:
                    atk_dmg += round(uniform(2, 4))
    crit_dmg = atk_dmg * crit_x
    return Player('B', atk_dmg, atk_spd, crit_pct, crit_x, health, power, spawn_time, crit_dmg, mit_pct=mit_pct,defense_pct=defense_pct, defense_abs=defense_abs,
                  name=f"B{amp_str}_{choice(names)}", amp=amp, season_count=season_count,
                  trait_tag=tag, trait_multiplier=mult)

def c_tier(amp=0, season_count=-1, pre_reflect=0, trait_amp=0, fixed='None'):

    atk_dmg = randint(49, 60)
    atk_spd = randint(7,9)
    crit_pct = round(((randint(53, 72)+(amp*(2/3))) / 1000),2)
    crit_x = randint(630, 860)/100 + float(3*amp/10)
    mit_pct = round(uniform(0.0175, 0.075), 4)
    defense_abs = round(uniform(2.3, 5.25))
    defense_pct = round(uniform(0.03, 0.055), 4)
    health = round(uniform(210,225),2)
    if amp>=5:
        health = round(health+(amp*2),2)
    elif amp<=-1:
        health = round(health-abs(amp*8))
    power = randint(50, 57) #avg 53
    spawn_time = choice([6,6,7,7,7,7,7,8,8,8,8,8])
            # Return a Player object initialized with the generated values
    amp_str = "" if amp == 0 else f"^{amp}"
    tag, mult = new_trait_roll('C', fixed=fixed)
    if tag == "None":
        non_trait_coin = choice([1,2,3,4,5,6,6])
        if non_trait_coin == 1:
            if atk_spd not in [6,7] and choice([True,False]):
                atk_spd -= 1
            else:
                atk_dmg += round(uniform(2,4))
        elif non_trait_coin == 2:
            crit_pct += round(uniform(0.005,0.099),4)
        elif non_trait_coin == 3:
            crit_x += round(uniform(1,2),2)
        elif non_trait_coin == 4:
            health += round(uniform(5,12),2)
        elif non_trait_coin == 5:
            power += choice([0,1,1,1,1,1,1,2,2])
        else:
            if spawn_time != 6 and choice([True,False]):
                spawn_time -= 1
            else:
                if atk_spd not in [6, 7] and choice([True, False]):
                    atk_spd -= 1
                else:
                    atk_dmg += round(uniform(2, 4))
    crit_dmg = atk_dmg * crit_x
    return Player('C', atk_dmg, atk_spd, crit_pct, crit_x, health, power, spawn_time, crit_dmg, mit_pct=mit_pct, defense_pct=defense_pct, defense_abs=defense_abs,
                  name=f"C{amp_str}_{choice(names)}", amp=amp, season_count=season_count,
                  trait_tag=tag, trait_multiplier=mult)