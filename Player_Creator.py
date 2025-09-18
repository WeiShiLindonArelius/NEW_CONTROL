import math

from Players import Player
from random import randint, choice, uniform
import numpy as np
from lists import player_names
names = player_names

#If the reflector trait doesn't hit, this will trigger next.
#This returns "" if the player is not given a trait, and the trait tag along with a multiplier if they are
def additional_trait_roll(tier, fixed="None",amp=0,pre_reflect=0):
    #amp is no longer being used because of mathematical issues
    clutch_lower_bound = 1.05
    inc_lower_bound = 0.11
    pp_lower_bound = 0.2
    explode_lower_bound = 0.4
    undead_lower_bound = 0.175
    reflector_lower_bound = 0.10
    splitter_lower_bound = 0.14
    vampire_lower_bound = 0.375
    heal_nova_possibilities = [x for x in range(36, 84) if x % 12 == 0]
    heal_tick_possibilities = [13,12,12,11,11,10]
    stun_tick_possibilities = [10,11,12,13]
    if tier == 'S':
        heal_nova_possibilities.pop()
        heal_tick_possibilities.pop()
        stun_tick_possibilities.pop()
    if tier == 'A' and choice([True,False]):
        heal_nova_possibilities.pop()
        heal_tick_possibilities.pop()
        stun_tick_possibilities.pop()
#multipliers for Toxic, Healer, Flasher, have to be selected a different way
    def toxic_mult(upper_bound):
        return [round(uniform(0.225, upper_bound), 2), [choice([6,6,7,7,8,8,9]), choice([9,10,10,10,11,11,12])]] #chance, damage, time
    def healer_mult():
        return [choice(heal_tick_possibilities), choice(heal_nova_possibilities), False]
    def flasher_mult(upper_bound):
        return [round(uniform(0.20, upper_bound), 2), choice(stun_tick_possibilities)]


    if tier == 'S':
        clutch_upperbound = 1.2
        inc_upperbound = 0.125
        pp_upperbound = 0.4
        explode_upperbound = 0.98
        undead_upperbound = 0.315
        reflector_upperbound = 0.17
        splitter_upper_bound = 0.155
        vampire_upper_bound = 0.52
        toxic_upper_bound = 0.29
        flasher_upper_bound = 0.25
    elif tier == 'A':
        clutch_upperbound = 1.25
        inc_upperbound = 0.14
        pp_upperbound = 0.45
        explode_upperbound = 0.9
        undead_upperbound = 0.32
        reflector_upperbound = 0.18
        splitter_upper_bound = 0.16
        vampire_upper_bound = 0.53
        toxic_upper_bound = 0.295
        flasher_upper_bound = 0.26
    elif tier == 'B':
        clutch_upperbound = 1.275
        inc_upperbound = 0.165
        pp_upperbound = 0.5
        explode_upperbound = 0.95
        undead_upperbound = 0.325
        reflector_upperbound = 0.19
        splitter_upper_bound = 0.17
        vampire_upper_bound = 0.54
        toxic_upper_bound = 0.3
        flasher_upper_bound = 0.27
    elif tier == 'C':
        clutch_upperbound = 1.2875
        inc_upperbound = 0.18
        pp_upperbound = 0.6
        explode_upperbound = 0.99
        undead_upperbound = 0.35
        reflector_upperbound = 0.2
        splitter_upper_bound = 0.18
        vampire_upper_bound = 0.55
        toxic_upper_bound = 0.31
        flasher_upper_bound = 0.28
    elif tier == '$l':
        return ["None",0]
    else:
        #Error handling block; this should never happen
        clutch_upperbound = 1.3
        inc_upperbound = 0.1
        pp_upperbound = 0.14
        explode_upperbound = 1.55
        undead_upperbound = 0.5
        reflector_upperbound = 0.5
        splitter_upper_bound = 0.15
        vampire_upper_bound = 0.5
        toxic_upper_bound = 0.35
        flasher_upper_bound = 0.21

    if fixed != "None" and fixed != 'NotNone':
        if fixed == 'C%':
            return ['C%', round(uniform(clutch_lower_bound,clutch_upperbound),2)]
        elif fixed == 'I*':
            return ['I*', round(uniform(inc_lower_bound,inc_upperbound),2)]
        elif fixed == 'Pp':
            return ['Pp', round(uniform(pp_lower_bound,pp_upperbound),2)]
        elif fixed == 'X+':
            return ['X+', [round(uniform(explode_lower_bound, explode_upperbound), 2), 1]]
        elif fixed == 'U-':
            return ['U-', round(uniform(undead_lower_bound, undead_upperbound), 2)]
        elif fixed == 'R#':
            return ['R#', uniform(reflector_lower_bound, reflector_upperbound)]
        elif fixed == 'Tx':
            return ['Tx', toxic_mult(toxic_upper_bound)]
        elif fixed == 'Hn':
            return ['Hn', healer_mult()]
        elif fixed == 'Fl':
            return ['Fl', flasher_mult(flasher_upper_bound)]
        elif fixed == 'V.':
            return ['V.', round(uniform(vampire_lower_bound, vampire_upper_bound), 2)]
        elif fixed == 'Sp':
            return ['Sp', round(uniform(splitter_lower_bound, splitter_upper_bound), 2)]
        else:
            return ["None",0]
    else:
        reflect_chance = 0.0585
        clutch_chance = 0.06
        inconsistent_chance = 0.06
        pp_chance = 0.06
        explode_chance = 0.04
        undead_chance = 0.05
        splitter_chance = 0.0575
        vampire_chance = 0.058
        toxic_chance = 0.057
        flasher_chance = 0.055
        healer_chance = 0.049

        reflect_odds = [0, reflect_chance]
        clutch_odds = [reflect_odds[1], reflect_chance + clutch_chance]
        inconsistent_odds = [clutch_odds[1], clutch_odds[1] + inconsistent_chance]
        pp_odds = [inconsistent_odds[1], inconsistent_odds[1] + pp_chance]
        explode_odds = [pp_odds[1], pp_odds[1] + explode_chance]
        undead_odds = [explode_odds[1], explode_odds[1] + undead_chance]
        splitter_odds = [undead_odds[1], undead_odds[1] + splitter_chance]
        vampire_odds = [splitter_odds[1], splitter_odds[1] + vampire_chance]
        toxic_odds = [vampire_odds[1], vampire_odds[1] + toxic_chance]
        flasher_odds = [toxic_odds[1], toxic_odds[1] + flasher_chance]
        healer_odds = [flasher_odds[1], flasher_odds[1] + healer_chance]

        trait_roll = randint(0,1000) / 1000 if fixed != 'NotNone' else randint(0,490) / 1000
        # Clutch 5% // Inconsistent 7.5% // Playoff Performer 7.5% // Reflector 4% // Exploder 4% // Undead 4%
        #
        # Total: 32% chance of trait
        if pre_reflect == 1:
            #positive values not equal to 1 should do nothing now that reflector is a normal trait and not separate from the others
            return ['R#', uniform(reflector_lower_bound, reflector_upperbound)]

        elif np.logical_and(clutch_odds[0] <= trait_roll, trait_roll <= clutch_odds[1]):
            return ['C%', round(uniform(clutch_lower_bound,clutch_upperbound),2)]

        elif np.logical_and(inconsistent_odds[0] < trait_roll, trait_roll <= inconsistent_odds[1]):
            return ['I*', round(uniform(inc_lower_bound,inc_upperbound),2)]

        elif np.logical_and(pp_odds[0] < trait_roll, trait_roll <= pp_odds[1]):
            return ['Pp', round(uniform(pp_lower_bound,pp_upperbound),2)]

        elif np.logical_and(reflect_odds[0] < trait_roll, trait_roll <= reflect_odds[1]):
            return ['R#', uniform(reflector_lower_bound, reflector_upperbound)]

        elif np.logical_and(explode_odds[0] < trait_roll, trait_roll <= explode_odds[1]):
            return ['X+', [round(uniform(explode_lower_bound, explode_upperbound), 2), 1]]

        elif np.logical_and(undead_odds[0] < trait_roll, trait_roll <= undead_odds[1]):
            return ['U-', round(uniform(undead_lower_bound,undead_upperbound),2)]

        elif np.logical_and(splitter_odds[0] < trait_roll, trait_roll <= splitter_odds[1]):
            return ['Sp', round(uniform(splitter_lower_bound, splitter_upper_bound), 2)]

        elif np.logical_and(vampire_odds[0] < trait_roll, trait_roll <= vampire_odds[1]):
            return ['V.', round(uniform(vampire_lower_bound, vampire_upper_bound), 2)]

        elif np.logical_and(toxic_odds[0] < trait_roll, trait_roll <= toxic_odds[1]):
            return ['Tx', toxic_mult(toxic_upper_bound)]
            # reflectors do not have a multiplier

        elif np.logical_and(flasher_odds[0] < trait_roll, trait_roll <= flasher_odds[1]):
            return ['Fl', flasher_mult(flasher_upper_bound)]

        elif np.logical_and(healer_odds[0] < trait_roll, trait_roll <= healer_odds[1]):
            return ['Hn', healer_mult()]

        else:
            return ["None",0]


def slasher(amp=0, season_count=-1):
    #SLASHER
    #Special Trait: all critical hits deal damage equal to the maximum health of the player they are attacking
    #Stat Pros: Very high attack damage, fast attack speed
    #Stat Cons: Very low health, very low power, high spawn time
    #Tag: '$'

    atk_dmg = randint(55, 69) + math.floor(amp)
    atk_spd = randint(6, 9)
    insta_kill_pct = round((((randint(64, 73)) / 1000) + (amp * 0.005)),2)
    crit_pct = insta_kill_pct
    crit_x = round((660 / atk_dmg), 2) #average health * 3 to estimate critical damage for xWAR
    mit_pct = round(uniform(0.01, 0.05))
    defense_pct = round(uniform(0.015, 0.04))
    defense_abs = round(uniform(1,4))
    health = choice([round(uniform(150, 180), 2), round(uniform(135, 200), 2)])
    power = choice([randint(52, 54), randint(50, 56)])
    spawn_time = choice([6,6,6,6,7,8,9])
    crit_dmg = 850

    amp_str = "" if amp==0 else f"^{amp}"
    return Player('$l', atk_dmg, atk_spd, crit_pct, crit_x, health, power, spawn_time, crit_dmg, f"$l{amp_str}_{choice(names)}",amp=amp, season_count=season_count, insta_kill_pct=insta_kill_pct, trait_tag="$l",
                  mit_pct=mit_pct, defense_pct=defense_pct, defense_abs=defense_abs)

def s_tier(amp=0, season_count=-1, pre_reflect=0, trait_amp=0, fixed='None'):
    slasher_roll = randint(0, (550-int(amp)))
    if slasher_roll % 280 == 0:
        add = round(uniform(-50,50+int(amp)))
        return slasher(amp=((slasher_roll+add)/100),season_count=season_count)


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
    tag, mult = additional_trait_roll('S',amp=trait_amp,pre_reflect=pre_reflect, fixed=fixed)
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
    tag, mult = additional_trait_roll('A',amp=trait_amp,pre_reflect=pre_reflect, fixed=fixed)
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
    slasher_roll = randint(0, (500 - int(amp)))
    if slasher_roll % 380 == 0:
        add = round(uniform(-150, 50 + int(amp)))
        return slasher(amp=((slasher_roll + add) / 100), season_count=season_count)

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
    tag, mult = additional_trait_roll('B',amp=trait_amp,pre_reflect=pre_reflect, fixed=fixed)
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
    slasher_roll = randint(0, (600 - int(amp*2.5)))
    if slasher_roll % 480 == 0:
        add = round(uniform(-200, 10 + int(amp)))
        return slasher(amp=((slasher_roll + add) / 100), season_count=season_count)

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
    tag, mult = additional_trait_roll('C',amp=trait_amp,pre_reflect=pre_reflect, fixed=fixed)
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