import math
import random
from random import choice, seed, uniform, randint
from Player_Creator import s_tier, a_tier, b_tier, c_tier, slasher, additional_trait_roll
from colorama import Fore, Back, Style
from numpy import mean
from stat_functions import QUERY
from lists import player_names
from Players import remove_tag_from_name

from switches import pick_perks

def timed_input(prompt): #False = auto-perk picks, True = manual perk picks

    if pick_perks:
        user_input = input(prompt)
        return user_input
    else:
        print(prompt)
        return "O"

def grade_players(players, is_team=None):
    for player in players:
        player.xWAR()

    players.sort(key=lambda pl: pl.xWAR, reverse=True)
    rank_index = 0
    for player in players:
        player.grade_dict['Rank'] = 1 + rank_index
        rank_index += 1

def write_to_file(filename=None, words=None, mode='w', error=False):
    if error:
        filename = 'error_output'
        mode = 'a'

    with open(filename, mode) as f:
        f.write(words + '\n')

def generate_lineups_six_to_four(six_lineup, team_coach, team_id=-1):

    four_lineups = [[] for _ in range(9)]
    six_lineup.sort(key=lambda player : player.xWAR, reverse=True)
    for i in range(6):
        six_lineup[i].slot = i

    for player in six_lineup:
        player.coach_amp = ["None", 0]
        player.coach_trait_amp = ["N/A", 0] if player.trait_tag == "None" else ["None", 0]


    amped_slots = team_coach.slot_effect[0]
    for i in amped_slots:
        six_lineup[i].coach_amp = [team_coach.slot_effect[1], team_coach.slot_effect[2]] #trait affected, amp amount
    for player in six_lineup:
        if player.trait_tag == team_coach.trait_effect[0]:
            player.coach_trait_amp = [player.trait_tag, team_coach.trait_effect[1]]


    four_lineups[0] = [six_lineup[0], six_lineup[1], six_lineup[2], six_lineup[3]]
    four_lineups[1] = [six_lineup[0], six_lineup[1], six_lineup[2], six_lineup[4]]
    four_lineups[2] = [six_lineup[0], six_lineup[1], six_lineup[2], six_lineup[5]]
    four_lineups[3] = [six_lineup[0], six_lineup[1], six_lineup[3], six_lineup[4]]
    four_lineups[4] = [six_lineup[1], six_lineup[2], six_lineup[3], six_lineup[5]]
    four_lineups[5] = [six_lineup[0], six_lineup[3], six_lineup[4], six_lineup[5]]

    if team_coach.lineup_modifier == "1C": #swap lineups 0 and 1, swap p3 and p4 in lineups 4 and 5
        four_lineups[0] = [six_lineup[0], six_lineup[1], six_lineup[2], six_lineup[4]]
        four_lineups[1] = [six_lineup[0], six_lineup[1], six_lineup[2], six_lineup[3]]
        four_lineups[4] = [six_lineup[1], six_lineup[2], six_lineup[4], six_lineup[5]]
        four_lineups[5] = [six_lineup[0], six_lineup[1], six_lineup[3], six_lineup[5]]
    elif team_coach.lineup_modifier == '2C': #swaps p0 and p2 in lineups 4 and 5 (2 new lineups: 0135 and 2345)
        four_lineups[4] = [six_lineup[0], six_lineup[1], six_lineup[3], six_lineup[5]]
        four_lineups[5] = [six_lineup[2], six_lineup[3], six_lineup[4], six_lineup[5]]
    elif team_coach.lineup_modifier == "3C": #swaps p4 and p5 in lineups 3 and 4 (2 new lineups: 0135 and 1234)
        four_lineups[3] = [six_lineup[0], six_lineup[1], six_lineup[3], six_lineup[5]]
        four_lineups[4] = [six_lineup[1], six_lineup[2], six_lineup[3], six_lineup[4]]

    elif team_coach.lineup_modifier == "4C": #swaps p0 and p1 in lineups 4 and 5 (2 new lineups: 0235 and 1345)
        four_lineups[4] = [six_lineup[0], six_lineup[2], six_lineup[3], six_lineup[5]]
        four_lineups[5] = [six_lineup[1], six_lineup[3], six_lineup[4], six_lineup[5]]

    elif team_coach.lineup_modifier == '5C': #swaps p2 and p4 in lineups 2 and 5 (2 new lineups: 0145 and 0235)
        four_lineups[2] = [six_lineup[0], six_lineup[1], six_lineup[4], six_lineup[5]]
        four_lineups[5] = [six_lineup[0], six_lineup[2], six_lineup[3], six_lineup[5]]
    elif team_coach.lineup_modifier == '6C': #swap p1 and p4 in lineups 0 and 5
        four_lineups[0] = [six_lineup[0], six_lineup[2], six_lineup[3], six_lineup[4]]
        four_lineups[5] = [six_lineup[0], six_lineup[1], six_lineup[3], six_lineup[5]]
    elif team_coach.lineup_modifier == '7C': #swap p2 and p3 in lineups 2 and 5
        four_lineups[5] = [six_lineup[0], six_lineup[2], six_lineup[4], six_lineup[5]]
        four_lineups[2] = [six_lineup[0], six_lineup[1], six_lineup[3], six_lineup[5]]
    elif team_coach.lineup_modifier == '1S': #swap lineups 1 and 2
        four_lineups[2] = [six_lineup[0], six_lineup[1], six_lineup[2], six_lineup[4]]
        four_lineups[1] = [six_lineup[0], six_lineup[1], six_lineup[2], six_lineup[5]]
    elif team_coach.lineup_modifier == '2S': #swap lineups 2 and 3
        four_lineups[3] = [six_lineup[0], six_lineup[1], six_lineup[2], six_lineup[5]]
        four_lineups[2] = [six_lineup[0], six_lineup[1], six_lineup[3], six_lineup[4]]
    elif team_coach.lineup_modifier == '3S': #swap lineups 3 and 4
        four_lineups[4] = [six_lineup[0], six_lineup[1], six_lineup[3], six_lineup[4]]
        four_lineups[3] = [six_lineup[1], six_lineup[2], six_lineup[3], six_lineup[5]]
    elif team_coach.lineup_modifier == '4S': #swap lineups 4 and 5
        four_lineups[5] = [six_lineup[1], six_lineup[2], six_lineup[3], six_lineup[5]]
        four_lineups[4] = [six_lineup[0], six_lineup[3], six_lineup[4], six_lineup[5]]
    elif team_coach.lineup_modifier == '5S': #swap lineups 0 and 2
        four_lineups[2] = [six_lineup[0], six_lineup[1], six_lineup[2], six_lineup[3]]
        four_lineups[0] = [six_lineup[0], six_lineup[1], six_lineup[2], six_lineup[5]]
    elif team_coach.lineup_modifier == '6S': #swap lineups 1 and 3
        four_lineups[3] = [six_lineup[0], six_lineup[1], six_lineup[2], six_lineup[4]]
        four_lineups[1] = [six_lineup[0], six_lineup[1], six_lineup[3], six_lineup[4]]
    elif team_coach.lineup_modifier == '7S': #swap lineups 2 and 4
        four_lineups[4] = [six_lineup[0], six_lineup[1], six_lineup[2], six_lineup[5]]
        four_lineups[2] = [six_lineup[1], six_lineup[2], six_lineup[3], six_lineup[5]]
    elif team_coach.lineup_modifier == '8S': #swap lineups 3 and 5
        four_lineups[5] = [six_lineup[0], six_lineup[1], six_lineup[3], six_lineup[4]]
        four_lineups[3] = [six_lineup[0], six_lineup[3], six_lineup[4], six_lineup[5]]





    team_coach.team_id = team_id
    query = """
    UPDATE Coach
    SET team_id = ?
    WHERE coach_id = ?;
    
    """
    params = (team_id, team_coach.coach_id)
    QUERY(query, params=params, is_select=False)

    return [four_lineups[0],four_lineups[1],four_lineups[2],four_lineups[3],four_lineups[4],four_lineups[5],six_lineup]


class Captain:
    def __init__(self):
        self.name = choice(player_names)
        self.damage_taken = round(uniform(0.09, 0.11), 4)
        self.max_health = round(uniform(85, 100))
        self.health = self.max_health
        self.atk_dmg_bonus = round(uniform(1.1, 1.25), 3)
        self.crit_pct_bonus = round(uniform(1.1, 1.25), 3)
        self.crit_x_bonus = round(uniform(1.25, 1.5), 3)
        self.power_bonus = round(uniform(1.6,2), 4)

    def __str__(self):
        return f"Captain: {self.name}, {self.damage_taken} damage taken, {self.max_health} health, {self.atk_dmg_bonus}x attack damage, {self.crit_x_bonus}x critical damage\n"




class Coach:
    from lists import coach_names, extra_first_names, extra_last_names
    def __init__(self,region=None,fixed_lineup_modifier=None,fixed_slot_effect=None,fixed_trait_effect=None,fixed_name=None):
        slots_amped = choice([ [0], [1], [2], [3], [4], [5],
            [0,5], [1,4], [2,3], [3,5], [3,4], [0,4], [1,3], [2,5],
            [0,4,5], [1,4,5], [1,3,5], [2,3,4], [2,3,5], [3,4,5]
        ])

        if len(slots_amped) == 3:
            slot_amp_possibilities = [
                ["Power", round(uniform(0.549, 0.809), 2)],
                ["Attack Damage", randint(2, 5)],
                ["Critical Chance", round(uniform(0.0175, 0.03), 2)]
            ]
        elif len(slots_amped) == 2:
            slot_amp_possibilities = [
                ["Power", round(uniform(0.59, 0.889), 2)],
                ["Attack Damage", randint(3, 6)],
                ["Critical Chance", round(uniform(0.0225, 0.04), 2)]
            ]
        else:
            slot_amp_possibilities = [
                ["Power", round(uniform(0.69, 0.959), 2)],  # % chance to add power
                ["Attack Damage", randint(4, 7)],  # raw increment
                ["Critical Chance", round(uniform(0.025, 0.05), 2)],  # raw increment
        ]

        trait_possibilities = [
            ["Pp", randint(1,6)], ['R#', round(uniform(1.425,2),2)],
            ['C%', round(uniform(1.2,1.45),2)],
            ['U-', round(uniform(1.25,1.5),2)], ['X+', randint(4,9)],
            ['Hn', round(uniform(0.75,0.9))], ['Tx', round(uniform(1.15,1.3),2)]
        ]

        if not fixed_name:
            try:
                self.name = choice(Coach.coach_names)
                Coach.coach_names.remove(self.name)
            except IndexError:
                self.name = choice(Coach.extra_first_names) + ' ' + choice(Coach.extra_last_names)
        else:
            self.name=fixed_name

        lineup_mod_roll = uniform(0,1)
        if lineup_mod_roll <= 0.4:
            self.lineup_modifier = "NC"
        elif lineup_mod_roll <= 0.8:
            self.lineup_modifier = choice(['1S', '2S', '3S', '4S', '5S', '6S', '7S', '8S'])
        else:
            self.lineup_modifier = choice(['1C', '2C', '3C', '4C', '5C', '6C', '7C'])

        self.slot_effect = fixed_slot_effect if fixed_slot_effect else [slots_amped] + choice(slot_amp_possibilities) #slots impacted, traits impacted, amplification amount
        self.trait_effect = fixed_trait_effect if fixed_trait_effect else choice(trait_possibilities) #trait impacted, amplification amount

        self.coach_record = {"Match Wins" : 0, "Match Losses" : 0, "Game Wins" : 0, "Game Losses" : 0}
        self.teams_coached = []
        self.team_id = -1 #SQL

        coach_sql = """ 
                                INSERT INTO Coach(coach_name, lineup_modifier, slots_amped, attribute_amped, attribute_amp_mult, trait_amped, trait_amp_mult)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                        """
        coach_params = (self.name, self.lineup_modifier, str(self.slot_effect[0]), self.slot_effect[1], self.slot_effect[2], self.trait_effect[0], self.trait_effect[1])
        self.coach_id = QUERY(coach_sql, params=coach_params, is_select=False)


    def __str__(self):
        return f"{self.name} (Lineup: {self.lineup_modifier} // Slots {self.slot_effect[0]} {self.slot_effect[1]} + {self.slot_effect[2]} // {self.trait_effect[0]} amp {self.trait_effect[1]})"





class Team:

    from lists import team_names

    names = list(set(team_names))
    names_copy = names.copy()
    names_backup = names_copy.copy()

    def __init__(self,region,mine=False,pre_name=None,season_count=-1,fixed_coach=None,jackson=False):
        seed()
        if pre_name:
            b = pre_name
        else:
            try:
                b = choice(Team.names_copy)
                Team.names_copy.remove(b)
            except IndexError:
                b = choice(Team.names_backup)
                Team.names_backup.remove(b)
        n = f"{region}_{b}"
        self.mine = mine
        self.jackson = jackson
        if self.mine and '*' not in n:
            if jackson:
                self.name = f"!-{n}-!"
                self.jackson = True #failsafe
            else:
                self.name = f"**{n}**"
        else:
            self.name = n
        self.region = region
        self.season_origin = season_count
        self.full_name = self.name

        self.is_noteworthy = False

        self.captain = Captain()
        self.living_captain = [0, 0] #ticks with a living captain, ticks with a dead captain

        self.rebuilding = False #this variable can be changed to True by a few epic perks. It means that three perks will be selected next season



        #ALL DONE: here, make it so that each team is given six players, and 15 lineups of 4 arranged from these players
        # will be saved in self.lineups which is a list of player lists
        # each team will also get a lineup_wins list and a lineup_losses list
        # and the number of wins/losses that lineup has
        # this will initiate the full lineup of six (team.players object) and generate...() will be run AFTER

        if region == 'OneLeague':
            self.players = [s_tier(season_count=season_count),s_tier(season_count=season_count),s_tier(season_count=season_count),
                           a_tier(season_count=season_count),a_tier(season_count=season_count),a_tier(season_count=season_count),
                           b_tier(season_count=season_count),b_tier(season_count=season_count),b_tier(season_count=season_count),
                           c_tier(season_count=season_count),c_tier(season_count=season_count),c_tier(season_count=season_count),
                           a_tier(season_count=season_count),b_tier(season_count=season_count),slasher(season_count=season_count)]

        elif region == 'Universal':
            uni_coin = choice([1,2,3,4])
            uni_coin2 = choice([1,2,3,4])

            if uni_coin == 1:
                coin_player = s_tier(round(uniform(5.01,6.99),2), season_count=season_count, fixed=choice(['R#', 'I*', 'C%']))
            elif uni_coin == 2:
                coin_player = slasher(round(uniform(2.09,3.49), 2), season_count=season_count)
            elif uni_coin == 3:
                coin_player = slasher(round(uniform(3.09,5.49), 2), season_count=season_count)
            else:
                coin_player = a_tier(round(uniform(5.49, 8.49), 2), season_count=season_count, trait_amp=0.9)

            if uni_coin2 == 1:
                coin2_player = s_tier(round(uniform(2.99, 9.99), 2), season_count=season_count)
            elif uni_coin2 == 2:
                coin2_player = s_tier(round(uniform(2.99, 9.99), 2), season_count=season_count)
            elif uni_coin2 == 3:
                coin2_player = s_tier(round(uniform(2.99, 9.99), 2), season_count=season_count)
            else:
                coin2_player = s_tier(round(uniform(2.99, 9.99), 2), season_count=season_count)




            self.players = [s_tier(round(uniform((3.99 if choice([True,True,True,False]) else -1.5),4.99),2), season_count=season_count),
                            a_tier(round(uniform((3.99 if choice([True,True,False]) else -1.5),5.99),2), season_count=season_count),
                            b_tier(round(uniform((3.99 if choice([True,False]) else -1.5),6.99),2), season_count=season_count),
                            c_tier(round(uniform((3.99 if choice([True,False,False,False,False]) else -1.5),8.99),2), season_count=season_count),
                            coin2_player, coin_player]

        elif region == 'Labyrinth':
            self.players = [slasher(round(uniform(1.09,3.49),2), season_count=season_count),
                            a_tier(round(uniform(-1.51,1.49),2), season_count=season_count, fixed=choice(["None", "None", choice(['I*', 'Pp', 'Pp', 'C%', 'R#', 'U-', 'X+'])])),
                            a_tier(round(uniform(-1.51,1.49),2), season_count=season_count, fixed=choice(["None", "None", choice(['I*', 'Pp', 'Pp', 'C%', 'R#', 'U-', 'X+'])])),
                            b_tier(round(uniform(-1.51,1.49),2), season_count=season_count, fixed=choice(["None", choice(['I*', 'Pp', 'Pp', 'C%', 'R#', 'U-', 'X+'])])),
                            b_tier(round(uniform(-1.51,1.49),2), season_count=season_count, fixed=choice(["None", choice(['I*', 'Pp', 'Pp', 'C%', 'R#', 'U-', 'X+'])])),
                            c_tier(round(uniform(-2.21,4.99)*uniform(-2.21,3.99),2),season_count=season_count, fixed=choice(["R#", "R#", "None"]))]
        elif region == 'Test':
            self.players = [s_tier(round(uniform(1,2.99),2), season_count=season_count), a_tier(round(uniform(1,3.99),2), season_count=season_count),
                            b_tier(round(uniform(0.5,4.99),2), season_count=season_count), b_tier(round(uniform(0.59,4.99),2), season_count=season_count),
                            c_tier(round(uniform(0,5.99),2), season_count=season_count), c_tier(round(uniform(0,6.99),2), season_count=season_count)]
        elif region == 'Cosmic':
            self.players = [slasher(round(uniform(1,4),2), season_count=season_count), slasher(round(uniform(1,3.8),2), season_count=season_count),
                            slasher(round(uniform(1,3.6),2), season_count=season_count), slasher(round(uniform(1,3.4),2), season_count=season_count),
                            slasher(round(uniform(1,3.2),2), season_count=season_count), slasher(round(uniform(1,3),2), season_count=season_count)]
        elif region == 'Tartarus':
            self.players = [s_tier(round(uniform(1.25, 2), 2), season_count=season_count, fixed='U-') if choice([True, False]) else a_tier(round(uniform(1, 1.59), 2), season_count=season_count, fixed='U-'),
                            a_tier(round(uniform(1.5, 2.5), 2), season_count=season_count, fixed='U-') if choice([True, True, False]) else b_tier(round(uniform(1, 1.49), 2), season_count=season_count, fixed='U-'),
                            a_tier(round(uniform(1.25, 3), 2), season_count=season_count, fixed='U-') if choice([True, False, False]) else b_tier(round(uniform(1, 2.99), 2), season_count=season_count,fixed='U-'),
                            b_tier(round(uniform(1.5, 2.5), 2), season_count=season_count, fixed='U-') if choice([True, True, False]) else c_tier(round(uniform(1, 1.59), 2), season_count=season_count,fixed='U-'),
                            b_tier(round(uniform(1.25, 3), 2), season_count=season_count, fixed='U-') if choice([True, False, False]) else c_tier(round(uniform(1, 1.99), 2), season_count=season_count,fixed='U-'),
                            c_tier(round(uniform(1.49, 3.99), 2), season_count=season_count, fixed='U-') if choice([True, False]) else s_tier(season_count=season_count, fixed='U-')]
        elif region == 'Beyond':
            self.players = [s_tier(round(uniform(1, 3.99), 2), season_count=season_count, fixed='I*'),
                            a_tier(round(uniform(1, 3.99), 2), season_count=season_count, fixed='I*'),
                            b_tier(round(uniform(1.5, 4.49), 2), season_count=season_count, fixed='I*'),
                            b_tier(round(uniform(1.5, 3.49), 2), season_count=season_count, fixed='I*'),
                            c_tier(round(uniform(3, 4.49), 2), season_count=season_count, fixed='I*'),
                            c_tier(round(uniform(2, 6.99), 2), season_count=season_count, fixed='I*')]
        elif region == 'Clasmia':
            self.players = [s_tier(round(uniform(0.25,2),2), season_count=season_count, fixed='X+') if choice([True, False]) else a_tier(round(uniform(0,1.59),2), season_count=season_count, fixed='X+'),
                            a_tier(round(uniform(0.5,2.5),2), season_count=season_count, fixed='X+') if choice([True, True, False]) else b_tier(round(uniform(0,1.59),2), season_count=season_count, fixed='X+'),
                            a_tier(round(uniform(0.25,3.99),2), season_count=season_count, fixed='X+') if choice([True, False, False]) else b_tier(round(uniform(0,1.99),2), season_count=season_count, fixed='X+'),
                            b_tier(round(uniform(0.5,2.59),2), season_count=season_count, fixed='X+') if choice([True, True, False]) else c_tier(round(uniform(0,1.59),2), season_count=season_count, fixed='X+'),
                            b_tier(round(uniform(0.25,2.99),2), season_count=season_count, fixed='X+') if choice([True, False, False]) else c_tier(round(uniform(0,1.99),2), season_count=season_count, fixed='X+'),
                            c_tier(round(uniform(0,3.99),2), season_count=season_count, fixed='X+') if choice([True, False]) else s_tier(season_count=season_count, fixed='X+')]

        elif jackson:
            self.players = [s_tier(season_count=season_count, fixed='I*'),
                            a_tier(round(uniform(0.01, 0.99), 2), season_count=season_count, fixed='I*'),
                            b_tier(round(uniform(-1, (4.515 if choice([True, False, False]) else 4)), 2),season_count=season_count, fixed='I*'),
                            (b_tier(round(uniform(0.02, 1.59),2), season_count=season_count, fixed='X+') if choice([True, True, False]) else a_tier(round(uniform(0, 2.59),2), season_count=season_count)),
                            (c_tier(round(uniform(-2.01, 6.99),2), season_count=season_count) if choice([True, True, True, False]) else s_tier(round(uniform(-0.05, 0.99),2),season_count=season_count, fixed='R#')),
                            (c_tier(round(uniform(-2.01, 6.99),2), season_count=season_count) if choice([True, True, False]) else b_tier(round(uniform(0, 1.99), 2), season_count=season_count,fixed='U-'))]

        elif self.mine:
            self.players = [s_tier(season_count=season_count,fixed='I*'),
                            a_tier(round(uniform(-0.01,2.99),2), season_count=season_count, fixed=choice(['Pp','Fl','Pp','Fl','Tx'])),
                            b_tier(round(uniform(-1,(2.515 if choice([True, False, False]) else 2)),2), season_count=season_count, fixed=choice(['C%','Sp','C%','Sp','Tx'])),
                            (b_tier(round(uniform(-0.02, 3.59),2), season_count=season_count,fixed=choice(['X+','V.','X+','V.','Tx'])) if choice([True, False, False]) else a_tier(round(uniform(1, 2.59),2),season_count=season_count)),
                            (c_tier(round(uniform(-1.01,6.99),2), season_count=season_count) if choice([True, True, False]) else s_tier(round(uniform(0.45,0.99),2), season_count=season_count, fixed=choice(['R#','Tx']))),
                            (c_tier(round(uniform(-1.81,6.59),2), season_count=season_count) if choice([True, False, False]) else b_tier(round(uniform(-0.89,2.99),2), season_count=season_count, fixed=choice(['U-','Hn'])))]

        else: #regional league season 0 teams
            self.players = [s_tier(round(uniform(-1.05, 4.99),2), season_count=season_count),
                            a_tier(round(uniform(-1.1, (3.79 if choice([True, False]) else 5.49)), 2),season_count=season_count),
                            b_tier(round(uniform(-1.2, (4.79 if choice([True, False, False]) else 6.49)), 2),season_count=season_count),
                            (b_tier(round(uniform(-1.5, 6)), season_count=season_count) if choice([True, True, False]) else a_tier(round(uniform(0, 2.89),2), season_count=season_count,fixed=choice(['C%', 'I*', 'Pp']))),
                            (c_tier(round(uniform(-1.3, (4.79 if choice([True,False]) else 6.19)),2), season_count=season_count) if choice([True, True, False]) else slasher(round(uniform(0, 2.59),2), season_count=season_count)),
                            (c_tier(round(uniform(0, 3.79),2), season_count=season_count) if choice([True, True, False]) else b_tier(round(uniform(0, 1.99), 2), season_count=season_count,fixed='U-'))]

        self.team_coach = fixed_coach if fixed_coach else Coach(region)
        self.fired_coach_this_season = False

        #grade_players(self.players)
        self.players.sort(key= lambda p : p.grade_dict["Rank"])
        all_lineups = list(generate_lineups_six_to_four(self.players,self.team_coach)) if region != "OneLeague" else self.players
        self.lineups = all_lineups
        #OneLeague teams have 15 players and only play one lineup

        # this lineups object is a LIST OF LISTS

        team_sql = """ 
                        INSERT INTO Team(team_name, region_of_origin, season_of_origin, coach_id)
                        VALUES (?, ?, ?, ?)
                """
        team_params = (self.name, self.region, self.season_origin, self.team_coach.coach_id)
        self.team_id = QUERY(team_sql, params=team_params, is_select=False)
        # QUERY is set to return the primary key assigned to a created value

        for player in self.players:
            player.team = self.name
        self.wins = 0
        self.losses = 0
        #the two below values hold wins and losses for total, 15-lineup regular season series. they are not used for
        # computing standings
        self.match_wins = 0
        self.match_losses = 0
        self.match_draws = 0

        self.lineup_wins = [0] * 7
        self.lineup_losses = [0] * 7

        self.points  = -1

        self.trophies = 0
        self.seed = -1
        self.previous_seed = -1
        self.region_seed = "None"
        self.history = {key: "" for key in range(50)}
        #self.seed_dict = {'RegionRegular' : -1, 'RegionPlayoffs' : -1, 'UniPlayIn' : -1, 'UniGroup' : -1, 'UniRegular' : -1}
        self.group = "None"
        self.played_region = {key: "" for key in range(50)} # dictionary of the leagues a team played in. keys
                                                            # are season_count, vals a string assigned in  league_season

        self.margin = 0
        self.accolades = {'Regional-Playoffs' : 0, 'Regional-Champ' : 0, 'Last-Stand' : 0, 'Pre-Qualifying' : 0,
                          'Universal-Qualifying' : 0, 'Universal-League' : 0, 'Universal-Playoffs' : 0, 'Uni-Playoff-Wins' : 0, 'Universal-Champ' : 0
                          , 'Slashers' : 0, 'Undead' : 0, 'Reflectors' : 0
                          , 'Clutch Players' : 0, 'Inconsistent Players' : 0, 'Playoff Performers' : 0, 'Exploders' : 0,
                          'Splitters' : 0, 'Flashers' : 0, 'Toxic Players' : 0, 'Vampires' : 0, 'Healers' : 0}
        #self.generate_player_names()

        #0 means no second round pick, 1 means group 1 (missed regional playoffs) and 2 means group 2 (came from region
        # and made PQ or further)
        self.second_pick = 0
        self.third_pick = 0

        self.qualifying_group = 0

    def change_coach(self,new_coach):
        self.team_coach = new_coach
        self.lineups = generate_lineups_six_to_four(self.players,new_coach) if self.region != "OneLeague" else self.players



        new_coach.team_id = self.team_id
        query = """
        UPDATE Coach
        SET team_id = ?
        WHERE coach_id = ?;

        """
        params = (self.team_id, new_coach.coach_id)
        QUERY(query, params=params, is_select=False)

        query = """
        UPDATE Team
        SET coach_id = ?
        WHERE team_id = ?
        
        """
        params = (new_coach.coach_id, self.team_id)
        QUERY(query, params=params, is_select=False)

    def reset_lineups(self):
        self.lineups = generate_lineups_six_to_four(self.players, self.team_coach)


    def make_mine(self,name):
        self.mine = True
        if self.region != "Labyrinth":
            self.name = f"**{name}**" if "**" not in name else name
        else:
            self.name = f"#{name}#"

    def print_team_name(self, season_count):
        if self.mine:
            with open('my_teams', 'a') as m:
                m.write(f"S{season_count}_{self.name}\n")
        with open('history', 'a') as h:
            h.write(f"S{season_count}_{self.name} (xWAR: {self.get_team_xWAR()})\n")

    def get_weighted_stat(self,stat_to_get):
        players = sorted(self.players, key=lambda p : p.xWAR, reverse=True)
        if stat_to_get == "Power":
            stat_list = [player.power for player in players]
        elif stat_to_get == "DPS":
            stat_list = [player.dps for player in players]
        elif stat_to_get == "Critical %":
            stat_list = [player.crit_pct for player in players]
        elif stat_to_get == "Mitigated %":
            stat_list = [player.mit_pct for player in players]
        elif stat_to_get == "Defense %":
            stat_list = [player.defense_pct for player in players]
        elif stat_to_get == "Defense Absolute":
            stat_list = [player.defense_abs for player in players]
        elif stat_to_get == "Critical X":
            stat_list = [player.crit_x for player in players]
        elif stat_to_get == "Health":
            stat_list = [player.max_health for player in players]
        elif stat_to_get == "Spawn Time":
            stat_list = [player.spawn_time for player in players]
        else:
            stat_list = [player.mit_pct for player in players]


        total_stat = (stat_list[0] * 6) + (stat_list[1] * 6) + (stat_list[2] * 5) + (stat_list[3] * 5) + (stat_list[4] * 4) + (stat_list[5] * 4)
        return round((total_stat / 30), 2)

    def get_team_xWAR(self):
        return sum(player.xWAR for player in self.players)
        #list for the amount of time which each slot plays for each coach lineup modifier,
        # and therefore what their xWAR should be multiplied by in the final calculation
        #slot_mult_dict = { 'NC' : [9,7,6,6,4,4] ,
        #                   '1C' : [8,8,7,5,4,4],
        #                   '2C' : [9,6,7,7,3,4],
        #                   '3C' : [8,8,7,6,3,4],
        #                   '4C' : [8,8,6,7,4,3],
        #                   '5C' : [7,9,6,7,4,3]}

        #return round(((sum([player.xWAR * slot_mult_dict[self.team_coach.lineup_modifier][player.slot] for player in sorted(self.players,key=lambda x: x.slot)])) / 6), 2)


    def print_team_info(self,test=False):

        if not test:
            print(Fore.RED + Back.CYAN + Style.BRIGHT + f"{self.full_name.upper()}" + Style.RESET_ALL)
            print(Fore.RED + Back.CYAN + Style.BRIGHT + f"Wins: {self.wins} ({round((self.wins/(self.wins+self.losses)*100),2)}%)"
                  + Style.RESET_ALL)
            print(Fore.RED + Back.CYAN + Style.BRIGHT + f"Losses: {self.losses}" + Style.RESET_ALL)
        for player in self.players:
            print(str(player))

    def print_history(self, season_count):

        if self.mine:
            with open('my_teams', 'a') as h:
                if season_count != 1:
                    for s in range(1, season_count + 1):
                        h.write(f"Season {s}: {self.history[s]}\n")
                else:
                    h.write(f"Season 1: {self.history[1]}\n")
                h.write('--------------\n\n')
        with open('history', 'a') as h:
            if season_count != 1:
                for s in range(1, season_count + 1):
                    h.write(f"Season {s}: {self.history[s]}\n")
            else:
                h.write(f"Season 1: {self.history[1]}\n")
            h.write('--------------\n\n')

    def print_accolades(self):
        self.accolades['Slashers'] = len([p for p in self.players if p.trait_tag == '$l'])
        self.accolades['Undead'] = len([p for p in self.players if p.trait_tag == 'U-'])
        self.accolades['Reflectors'] = len([p for p in self.players if p.trait_tag == 'R#'])
        self.accolades['Clutch Players'] = len([p for p in self.players if p.trait_tag == 'C%'])
        self.accolades['Inconsistent Players'] = len([p for p in self.players if p.trait_tag == 'I*'])
        self.accolades['Playoff Performers'] = len([p for p in self.players if p.trait_tag == 'Pp'])
        self.accolades['Exploders'] = len([p for p in self.players if p.trait_tag == 'X+'])
        self.accolades['Splitters'] = len([p for p in self.players if p.trait_tag == 'Sp'])
        self.accolades['Flashers'] = len([p for p in self.players if p.trait_tag == 'Fl'])
        self.accolades['Toxic Players'] = len([p for p in self.players if p.trait_tag == 'Tx'])
        self.accolades['Vampires'] = len([p for p in self.players if p.trait_tag == 'V.'])
        self.accolades['Healers'] = len([p for p in self.players if p.trait_tag == 'Hn'])

        if self.mine:
            with open('my_teams', 'a') as h:
                h.write(f"Coach: {str(self.team_coach)}\n")
                h.write(str(self.captain))
                if self.living_captain[0] + self.living_captain[1] > 0:
                    h.write(f"Captain alive for {100 * round((self.living_captain[0] / (self.living_captain[0] + self.living_captain[1])), 4)}% of ticks\n")
                    self.living_captain = [0, 0]
                i = 0
                for key in self.accolades.keys():
                    h.write(f"{key}: {self.accolades[key]}")
                    if i <= len(self.accolades.keys())-1:
                        h.write(", ")
                    i += 1
                    if i % 4 == 0:
                        h.write('\n')
                h.write('\n')

        with open('history', 'a') as h:
            h.write(f"Coach: {str(self.team_coach)}\n")
            h.write(str(self.captain))
            if self.living_captain[0] + self.living_captain[1] > 0:
                h.write(f"Captain alive for {100 * round((self.living_captain[0] / (self.living_captain[0] + self.living_captain[1])), 4)}% of ticks\n")
                self.living_captain = [0, 0]
            i = 0
            for key in self.accolades.keys():
                h.write(f"{key}: {self.accolades[key]}")
                if i <= len(self.accolades.keys()) - 1:
                    h.write(", ")
                i+=1
                if i%4 == 0:
                    h.write('\n')
            h.write('\n')

    def most_kills_on_team(self):
        max_kills = 0
        index = 0
        max_index = 0
        for player in self.players:
            if player.kills > max_kills:
                max_kills = player.kills
                max_index = index
            index += 1
        return self.players[max_index]

    def sort_players_by_tier(self):
        players = self.players
        tier_order = {'S': 4, 'A': 3, 'B': 2, 'C': 1}  # Map tier characters to numerical values
        sorted_players = sorted(players, key=lambda p: (tier_order[p.tier], p.power), reverse=True)
        return sorted_players

    def print_roster(self,finale=False,first=False): #first is used for when it prints all of my team lineups to the terminal in blue
        if self.mine:
            if first:
                with open('my_rosters', 'a') as f:
                    f.write(f"{self.name.upper()} ROSTER\n\n")
                    i = 0
                    for player in self.players:
                        f.write(f"({i})\n")
                        i += 1
                        f.write(str(player))
                    f.write('\n----------------------\n\n')
            else:
                print(f"{self.name.upper()} ROSTER\n")
                i = 0
                for player in self.players:
                    print(f"({i})")
                    i += 1
                    print(str(player))
                print('\n----------------------\n')
        else:
            if not finale:
                with open('rosters', 'a', buffering=1) as f:
                    f.write(f"{self.name.upper()} ROSTER\n\n")
                    i = 0
                    for player in self.players:
                        f.write(f"({i})\n")
                        i += 1
                        f.write(str(player))
                    f.write('\n----------------------\n\n')
            else:
                with open('rosters', 'w', buffering=1) as f:
                    f.write(f"{self.name.upper()} ROSTER\n\n")
                    i = 0
                    for player in self.players:
                        f.write(f"({i})\n")
                        i += 1
                        f.write(str(player))
                    f.write('\n----------------------\n\n')


    def trade(self, other):
        rec_index = input("Enter the index of the player being received.")
        trad_index = input("Enter the index of the player being traded.")


common_increments = {  # when a slot is to be amped, the amounts are chosen from this dict
    "Damage": 2,
    "Power": 1,
    "Critical %": 0.005,
    "Critical X": 0.5,
    "Health": 7.5,
    "Defense %": 0.004,
}  # attack speed, spawn time, defense absolute excluded
common_decrements = {  # slot negative effects are chosen from here
    "Damage": -1,
    "Critical %": -0.003,
    "Critical X": -0.25,
    "Health": -4,
    "Defense %": -0.0025,
}  # a player can have the same slot increased and decreased

epic_increments = {  # when a slot is to be amped, the amounts are chosen from this dict
    "Damage": 3,
    "Power": 1,
    "Critical %": 0.0075,
    "Critical X": 0.75,
    "Health": 10,
    "Defense %": 0.006,
}  # attack speed, spawn time, defense absolute excluded
epic_decrements = {  # slot negative effects are chosen from here
    "Damage": -1,
    "Critical %": -0.0025,
    "Critical X": -0.2,
    "Health": -3,
    "Defense %": -0.002,
}  # a player can have the same slot increased and decreased


def increment_trait(player, factor):
    #factor between 1 and 6
    if player.trait_tag == 'C%':
        player.trait_multiplier += (math.ceil(factor/2) / 75) #0.013, 0.0267, or 0.04
        print(f"{player.name}'s {player.trait_tag} mult increased by {(math.ceil(factor/2) / 75):.4f} to {player.trait_multiplier:.3f}!")
    elif player.trait_tag == 'I*':
        player.trait_multiplier += (math.ceil(factor / 2) / 200) #0.005, 0.01, 0.015
        print(f"{player.name}'s {player.trait_tag} mult increased by {(math.ceil(factor / 2) / 200):.4f} to {player.trait_multiplier:.4f}!")
    elif player.trait_tag == 'Pp':
        player.trait_multiplier += factor/100 #1-6
        print(
            f"{player.name}'s {player.trait_tag} mult increased by {factor/100} to {player.trait_multiplier:.4f}!")
    elif player.trait_tag == 'X+':
        player.trait_multiplier[0] += factor / 100 #1-6
        print(
            f"{player.name}'s {player.trait_tag} mult increased by {factor/100} to {player.trait_multiplier[0]:.3f}!")
    elif player.trait_tag == 'U-':
        player.trait_multiplier += (math.ceil(factor / 2) / 150) #0.0067, 0.013, 0.02
        print(
            f"{player.name}'s {player.trait_tag} mult increased by {(math.ceil(factor / 2) / 150):.4f} to {player.trait_multiplier:.4f}!")
    elif player.trait_tag == 'R#':
        player.trait_multiplier += factor / 320 #0.003125, 0.00625, 0.009375, 0.0125, 0.015625, 0.01875
        print(
            f"{player.name}'s {player.trait_tag} mult increased by {factor / 320:.6f} to {player.trait_multiplier:.4f}!")
    elif player.trait_tag == 'Tx':
        player.trait_multiplier[1][0] += math.ceil(factor/3) #1 or 2
        print(
            f"{player.name}'s Toxin damage increased by {math.ceil(factor/3):.4f} to {player.trait_multiplier[1][0]}!")
    elif player.trait_tag == 'Hn':
        player.trait_multiplier[0] -= 1
        player.trait_multiplier[1] += 6 * (math.ceil(factor/3)) #6 or 12
        print(
            f"{player.name}'s {player.trait_tag} time -1 to {player.trait_multiplier[0]} and heal amount increased by {6 * (math.ceil(factor/3))} to {player.trait_multiplier[1]}!")
    elif player.trait_tag == 'Fl':
        player.trait_multiplier[0] += (math.ceil(factor / 2) / 200)  # 0.005, 0.01, 0.015
        print(
            f"{player.name}'s {player.trait_tag} mult increased by {(math.ceil(factor / 2) / 200):.4f} to {player.trait_multiplier[0]:.4f}!")
    elif player.trait_tag == 'V.':
        player.trait_multiplier += (0.01 + (math.ceil(factor / 2) / 50))  # 0.03, 0.05, or 0.07
        print(
            f"{player.name}'s {player.trait_tag} mult increased by {(0.01 + (math.ceil(factor / 2) / 50)):.4f} to {player.trait_multiplier:.4f}!")
    elif player.trait_tag == 'Sp':
        player.trait_multiplier += (math.ceil(factor / 2) / 225)  # 0.0044, 0.0088, 0.013
        print(
            f"{player.name}'s {player.trait_tag} mult increased by {(math.ceil(factor / 2) / 225):.4f} to {player.trait_multiplier:.4f}!")
    else:
        add_trait_roll = randint(1,10)
        if add_trait_roll <= factor:
            tag, mult = additional_trait_roll(tier=player.tier, fixed='NotNone')
            player.trait_tag = tag
            player.trait_multiplier = mult
            print(f"{player.name} given {tag} with a mult of {mult}!")
            player.name = f"{tag}{remove_tag_from_name(player.name)}"

perk_option_strings = {
    "Rare" : ["'C' to amp the captain by an attribute of choice", "'T' to give one (1) random player a random trait",
              "'I' to run increment_trait(1 or 2) on three (3) players", "'B' to ensure one (1) player will breakout next season",
              "'P' to give all players +1 power"],

    "Epic" : ["'A' to increment power and one other stat for all players", "'T' to grant a random player a trait which synergizes with the coach",
              "'I' to increment all player trait mults and roll for traits for non-trait players", "'B' to ensure two (2) players will breakout next season",
              "'C' to pick a new captain from five (5) options"],

    "Legendary" : ["'C' to gain FIFTEEN (15) random common perks", "'I' to increment traits for all players with a factor of 5 or 6"]


}


def choose_perks(team):
    # user has two choices: amp a specific stat on a specific player, OR roll for a perk
    # if the user rolls, there is a 70% chance of a random stat being amped on a random player, a 22.5% chance for a rare perk, and a 7.5% chance for an epic perk
    option_str = ""

    translated_stats = {'Damage': 'atk_dmg', 'Power': 'power', 'Critical %': 'crit_pct', 'Critical X': 'crit_x',
                        'Health': 'max_health',
                        'Defense %': 'defense_pct'}
    perk_choice = timed_input(f"\n{team.name}: Press Y to roll for a rare or epic perk, press any other key to gain two \nor three random common perks AND increment_trait(1) on 1 random player OR pick a new captain.\n")
    if perk_choice == 'Y' or perk_choice == 'y':
        rarity_roll = uniform(0, 1)
        if rarity_roll <= 0.475: #COMMON (47.5%)
            slot_amp = randint(0, 5)
            attr_amp = choice(["Damage", "Power", "Critical %", "Critical X", "Health", "Defense %"])
            setattr(team.players[slot_amp], translated_stats[attr_amp],
                    (getattr(team.players[slot_amp], translated_stats[attr_amp]) + common_increments[attr_amp]))
            print(f"Slot {slot_amp} ({team.players[slot_amp].name}) {attr_amp} +{common_increments[attr_amp]}")
        elif rarity_roll <= 0.775: #RARE (30%)
            available_rare = list(range(len(perk_option_strings["Rare"])))
            for i in range(2):
                available_rare_index = choice(available_rare)
                option_str += perk_option_strings["Rare"][available_rare_index]
                if i != 1:
                    option_str += " or "
                available_rare.remove(available_rare_index)

            slot_choice = input(
                f"You've rolled for a rare perk! Type {option_str}\n")
            if slot_choice in ['C', 'c']:
                capt_choice = input("Damage Taken, Critical X, Damage X, or Health?\n")
                if capt_choice == "Damage Taken":
                    team.captain.damage_taken -= 0.0075
                    print(f"Captain damage taken % decreased by 0.0075 to {team.captain.damage_taken:.4f}")
                elif capt_choice == "Critical X":
                    team.captain.crit_x_bonus += 0.1
                    print(f"Captain critical bonus increased by 0.1 to {team.captain.crit_x_bonus:.3f}")
                elif capt_choice == "Damage X":
                    team.captain.atk_dmg_bonus += 0.04
                    print(f"Captain damage bonus increased by 0.04 to {team.captain.atk_dmg_bonus:.3f}")
                elif capt_choice == "Health":
                    team.captain.max_health += 3
                    print(f"Captain health increased by 3 to {team.captain.max_health}")
            elif slot_choice in ['T', 't']:
                trait_given = False
                for pl in team.players:
                    if pl.trait_tag == "None":
                        tag, mult = additional_trait_roll(tier=pl.tier,fixed='NotNone')
                        pl.trait_tag = tag
                        pl.trait_multiplier = mult
                        print(f"{pl.name} given {tag} with a mult of {mult}!")
                        pl.name = f"{tag}{remove_tag_from_name(pl.name)}"
                        trait_given = True
                if not trait_given:
                    print("All players have traits.")
                    for i in [0, 2, 4]:
                        increment_trait(team.players[i], factor=choice([1, 2]))
            elif slot_choice in ['B', 'b']:
                breakout_player = choice(team.players)
                breakout_player.breakout = True
                print(f"{breakout_player.name} will breakout next season!")
            elif slot_choice in ['P', 'p']:
                for pl in team.players:
                    pl.power += 1
                print("All players Power +1")

            else:
                for i in [1,3,5]:
                    increment_trait(team.players[i], factor=choice([1,2,3]))
        elif rarity_roll <= 0.925: #EPIC (15%)
            available_epic = list(range(len(perk_option_strings["Epic"])))
            for i in range(3):
                available_epic_index = choice(available_epic)
                option_str += perk_option_strings["Epic"][available_epic_index]
                if i == 0:
                    option_str += ", "
                if i == 1:
                    option_str += ", or\n"
                available_epic.remove(available_epic_index)

            slot_choice = input(
                f"You've rolled for an EPIC perk! Press {option_str}\n")
            if slot_choice in ['A', 'a']:
                attr_choice = input("What attribute would you like to amplify? (Damage, Power, Critical %, Critical X, Health, or Defense %)\n")
                if attr_choice not in ["Damage", "Power", "Critical %", "Critical X", "Health", "Defense %"]:
                    attr_choice = choice(["Damage", "Power", "Critical %", "Critical X", "Health", "Defense %"])
                for pl in team.players:
                    setattr(pl, translated_stats[attr_choice],
                            (getattr(pl, translated_stats[attr_choice]) + epic_increments[attr_choice]))
                    pl.power += 1 #power can be incremented twice to give +2 to all players
                print(f"All players {attr_choice} +{epic_increments[attr_choice]}")
                print("All players Power +1")
            elif slot_choice in ['T', 't']:
                trait_given = False
                for pl in team.players:
                    if pl.trait_tag == "None" and not trait_given:
                        tag, mult = additional_trait_roll(tier=pl.tier, fixed=team.team_coach.trait_effect[0])
                        pl.trait_tag = tag
                        pl.trait_multiplier = mult
                        print(f"{pl.name} given {tag} with a mult of {mult}!")
                        pl.name = f"{tag}{remove_tag_from_name(pl.name)}"
                        trait_given = True
                if not trait_given:
                    print("All players have traits.")
                    pl = choice(team.players)
                    tag, mult = additional_trait_roll(tier=pl.tier, fixed=team.team_coach.trait_effect[0])
                    pl.trait_tag = tag
                    pl.trait_multiplier = mult
                    print(f"{pl.name} randomly chosen and given {tag} with a mult of {mult}!")
                    pl.name = f"{tag}{remove_tag_from_name(pl.name)}"
                    for i in range(6):
                        increment_trait(team.players[i], factor=choice([1, 2, 2, 3]))
            elif slot_choice in ['C', 'c']:
                new_cap_1 = Captain()
                new_cap_2 = Captain()
                new_cap_3 = Captain()
                new_cap_4 = Captain()
                new_cap_5 = Captain()
                print(f"Current captain: {str(team.captain)}")
                print(f"Option 'A': {str(new_cap_1)}")
                print(f"Option 'B': {str(new_cap_2)}")
                print(f"Option 'C': {str(new_cap_3)}")
                print(f"Option 'D': {str(new_cap_4)}")
                print(f"Option 'E': {str(new_cap_5)}")
                new_capt_choice = input("Press one of 'A' through 'E' for a new captain, or 'N' to keep the current captain.\n")
                if new_capt_choice in ["A", "a"]:
                    team.captain = new_cap_1
                elif new_capt_choice in ["B", "b"]:
                    team.captain = new_cap_2
                elif new_capt_choice in ["C", "c"]:
                    team.captain = new_cap_3
                elif new_capt_choice in ["D", "d"]:
                    team.captain = new_cap_4
                elif new_capt_choice in ["E", "e"]:
                    team.captain = new_cap_5
            elif slot_choice in ['B', 'b']:
                available_breakout = [0,1,2,3,4,5]
                for _ in range(2):
                    breakout_index = choice(available_breakout)
                    team.players[breakout_index].breakout = True
                    print(f"{team.players[breakout_index].name} will breakout next season!")
                    available_breakout.remove(breakout_index)

            else:
                for i in range(6):
                    increment_trait(team.players[i], factor=choice([1,2,2,2,3,3,4]))
        else: #LEGENDARY (7.5%)
            available_legendary = list(range(len(perk_option_strings["Legendary"])))
            for i in range(2):
                available_legendary_index = choice(available_legendary)
                option_str += perk_option_strings["Legendary"][available_legendary_index]
                if i == 0:
                    option_str += ", "
                available_legendary.remove(available_legendary_index)
            slot_choice = input(
                f"You've rolled for an LEGENDARY perk! Press {option_str}\n")
            if slot_choice in ['C', 'c']:
                for _ in range(15):
                    slot_amp = randint(0, 5)
                    attr_amp = choice(["Damage", "Power", "Critical %", "Critical X", "Health", "Defense %"])
                    setattr(team.players[slot_amp], translated_stats[attr_amp],
                            (getattr(team.players[slot_amp], translated_stats[attr_amp]) + common_increments[attr_amp]))
                    print(f"Slot {slot_amp} ({team.players[slot_amp].name}) {attr_amp} +{common_increments[attr_amp]}")
            else:
                for i in range(6):
                    increment_trait(team.players[i], factor=choice([5,6]))



    else:
        no_roll_choice = input("Press 'P' to buff players, 'C' for new captain:\n")
        if no_roll_choice in ["P", "p"]:
            for _ in range(choice([2,2,2,2,3,3,3])):
                slot_amp = randint(0, 5)
                attr_amp = choice(["Damage", "Power", "Critical %", "Critical X", "Health", "Defense %"])
                setattr(team.players[slot_amp], translated_stats[attr_amp],
                        (getattr(team.players[slot_amp], translated_stats[attr_amp]) + common_increments[attr_amp]))
                print(f"Slot {slot_amp} ({team.players[slot_amp].name}) {attr_amp} +{common_increments[attr_amp]}")
            increment_trait(choice(team.players), factor=1)
        else:
            new_cap_1 = Captain()
            new_cap_2 = Captain()
            print(f"Current captain: {str(team.captain)}")
            print(f"Option 'A': {str(new_cap_1)}")
            print(f"Option 'B': {str(new_cap_2)}")
            new_capt_choice = input("Press 'A' or 'B' for a new captain, or 'N' to keep the current captain.\n")
            if new_capt_choice in ["A", "a"]:
                team.captain = new_cap_1
            elif new_capt_choice in ["B", "b"]:
                team.captain = new_cap_2




