import math

from Games import game, no_op, blockPrint, enablePrint, best_of
import random
from colorama import Fore
from load_pickle import season_wipe
from Teams import generate_lineups_six_to_four, Coach

def ordinal_string(n: int) -> str:
    if 10 <= n % 100 < 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"

def print_standings(TEAMS,universal=False,round_no=-1,print_region_seed=False,cyan_seeds=None, yellow_seeds=None, red_seeds=None):
    #qualifying_seed will print the team name of the teams in the top {value} in cyan

    #for regional, 1-6 should be Cyan, 7-10 should be Yellow, and everyone else is red
    #for universal, 1-14 should be Cyan, 15-30 should be Yellow, and everyone else is red
    region_seed_str = ''
    enablePrint()
    if round_no == -1:
        print(Fore.GREEN + f"FINAL STANDINGS" + Fore.RESET)
    else:
        print(Fore.GREEN + f"ROUND {round_no} STANDINGS" + Fore.RESET)

    idx = 0
    TEAMS.sort(key=lambda x: (x.points, x.wins, x.margin), reverse=True)
    for team in TEAMS:
        temp_lineup_record = f"\t[0N({team.lineup_wins[0]}-{team.lineup_losses[0]}), " \
                             f"1N({team.lineup_wins[1]}-{team.lineup_losses[1]}), " \
                             f"2N({team.lineup_wins[2]}-{team.lineup_losses[2]}), " \
                             f"3N({team.lineup_wins[3]}-{team.lineup_losses[3]}), " \
                             f"4N({team.lineup_wins[4]}-{team.lineup_losses[4]}), " \
                             f"5N({team.lineup_wins[5]}-{team.lineup_losses[5]}), " \

        idx += 1
        team.seed = idx
        if team.previous_seed != -1:
            if team.previous_seed > team.seed:
                previous_seed_str = f" [↑{team.previous_seed-team.seed}]"
            elif team.previous_seed < team.seed:
                previous_seed_str = f" [↓{team.seed - team.previous_seed}]"
            else:
                previous_seed_str = " [-]"
        else:
            previous_seed_str = ''

        if team.margin <= 0:
            sign = ''
        else:
            sign = '+'
        if print_region_seed:
            region_seed_str = f"({team.region_seed})"

        if cyan_seeds and red_seeds:
            if (idx-1) in cyan_seeds:
                print(f"{idx}.{previous_seed_str} " + Fore.CYAN + f"{team.name}" + Fore.RESET + f"{region_seed_str}: {team.match_wins}-{team.match_losses}-{team.match_draws} ({team.points} points)"
                      + Fore.GREEN + f" ({team.wins}-{team.losses} game record){temp_lineup_record}" + Fore.RESET + f" [[{sign}{round(team.margin,2)}]]")
            elif yellow_seeds and (idx-1) in yellow_seeds:
                print(f"{idx}.{previous_seed_str} " + Fore.YELLOW + f"{team.name}" + Fore.RESET + f"{region_seed_str}: {team.match_wins}-{team.match_losses}-{team.match_draws} ({team.points} points)"
                      + Fore.GREEN + f" ({team.wins}-{team.losses} game record){temp_lineup_record}" + Fore.RESET + f" [[{sign}{round(team.margin,2)}]]")
            elif (idx-1) in red_seeds:
                print(f"{idx}.{previous_seed_str} " + Fore.RED + f"{team.name}" + Fore.RESET + f"{region_seed_str}: {team.match_wins}-{team.match_losses}-{team.match_draws} ({team.points} points)"
                      + Fore.GREEN + f" ({team.wins}-{team.losses} game record){temp_lineup_record}" + Fore.RESET + f" [[{sign}{round(team.margin,2)}]]")
            else:
                print(f"{idx}.{previous_seed_str} {team.name}{region_seed_str}: {team.match_wins}-{team.match_losses}-{team.match_draws} ({team.points} points)"
                      + Fore.GREEN + f" ({team.wins}-{team.losses} game record){temp_lineup_record}" + Fore.RESET + f" [[{sign}{round(team.margin,2)}]]")
        else:
            print(f"{idx}.{previous_seed_str} {team.name}{region_seed_str}: {team.match_wins}-{team.match_losses}-{team.match_draws} ({team.points} points)"
                      + Fore.GREEN + f" ({team.wins}-{team.losses} game record){temp_lineup_record}" + Fore.RESET + f" [[{sign}{round(team.margin,2)}]]")

def alter_lineup(team):
    def move_player(old, new, swap_team):
        swap_team.players[old], swap_team.players[new] = swap_team.players[new], swap_team.players[old]

    print(Fore.BLUE + f"{team.name} are {ordinal_string(team.seed)} in the league, with a record of {team.wins}-{team.losses}.\n"
                      f"Here is the current order of your players ({team.name}):" + Fore.RESET)
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
    user_coach_choice = ""
    if not team.fired_coach_this_season:
        while user_coach_choice not in ['Y', 'y', 'N', 'n']:
            user_coach_choice = input(
                f"Coach: {str(team.team_coach)}; would you like to FIRE them and generate a random coach? Y for YES, N for NO.")
        if user_coach_choice in ['Y', 'y']:
            new_coach = Coach(team.region)
            team.change_coach(new_coach)
            team.fired_coach_this_season = True
            print(f"New Coach: {str(team.team_coach)}")

    team.lineups = generate_lineups_six_to_four(team.players, team.team_coach)

def round_robin(TEAMS,r,qualify_range,amp=4,alt_qualify_range = None, is_test=False,franchise_mode=False,
                print_region_seed=False,cyan_seeds=None, yellow_seeds=None, red_seeds=None, is_universal=False):

    for team in TEAMS:
        team.previous_seed = -1
    franchise_functions = franchise_mode #prints standing by round
    if is_test:
        for team in TEAMS:
            team.wins = team.losses = 0
    SIZE = len(TEAMS)
    if r % 1 != 0:
        half_round=True
        r-=0.5
    else:
        half_round=False

    r=int(r)
    for k in range(r):
        for i in range(SIZE):
            for j in range(i + 1, SIZE):
                team1 = TEAMS[i]
                team2 = TEAMS[j]
                game(team1, team2,amp,playoffs=None)
        if franchise_functions and ((k != r-1 or half_round) and not (r>6 and k%2==0)):
            for team in TEAMS:
                team.points = (3*team.match_wins) + team.match_draws
            TEAMS.sort(key=lambda x: (x.points, x.wins, x.margin), reverse=True)
            print_standings(TEAMS,round_no=k+1,print_region_seed=print_region_seed)
            i = 0
            for team in TEAMS:
                team.previous_seed = i+1
                i+=1
                #if team.mine:
                #    alter_lineup(team)
        if k == r-1: #end of last round
            if half_round:
                division1 = []
                division2 = []

                # split the teams into two divisions of 11

                for x in range(1, 22):
                    if x % 2 == 0:
                        division1.append(TEAMS[x])
                    else:
                        division2.append(TEAMS[x])

                for a in range(len(division1)):
                    for b in range(a + 1, len(division1)):
                        tm1 = division1[a]
                        tm2 = division1[b]
                        game(tm1, tm2, amp, playoffs=None)

                for a in range(len(division2)):
                    for b in range(a + 1, len(division2)):
                        tm1 = division2[a]
                        tm2 = division2[b]
                        game(tm1, tm2, amp, playoffs=None)

            for team in TEAMS:
                team.points = (3*team.match_wins) + team.match_draws

                team.team_coach.coach_record["Game Wins"] += team.wins
                team.team_coach.coach_record["Game Losses"] += team.losses
                team.team_coach.coach_record["Match Wins"] += team.match_wins
                team.team_coach.coach_record["Match Losses"] += team.match_losses
            TEAMS.sort(key=lambda x: (x.points, x.wins, x.margin), reverse=True)
            print_standings(TEAMS,print_region_seed=print_region_seed,cyan_seeds=cyan_seeds, yellow_seeds=yellow_seeds, red_seeds=red_seeds)

    if qualify_range == 1:
        return TEAMS[0]
    else:
        bebop = []
        bebop2 = []
        for q in range(qualify_range):
            bubba = TEAMS[q]
            bebop.append(bubba)
        if alt_qualify_range:
            if is_universal:
                for q in range(16,24):
                    bubba2 = TEAMS[q]
                    bebop2.append(bubba2)
            else:
                for q in range(qualify_range, qualify_range+alt_qualify_range):
                    bubba2 = TEAMS[q]
                    bebop2.append(bubba2)
            return bebop, bebop2
        else:
            return bebop

def chain(teams):
    size = len(teams)
    winner = best_of(teams[size], teams[size-1], 100, win_by=10)
    for i in range(size):
        winner = best_of(winner, teams[size-i], 100+i, win_by=10)
    return winner