from Players import PlayerSeason, QUERY


def season_wipe(teams, season_count=-1, end_of_full_season=False):
    for team in teams:
        team.wins = 0
        team.losses = 0
        team.match_wins = 0
        team.match_losses = 0
        team.match_draws = 0
        team.trophies = 0
        team.seed = -1
        team.margin = 0

        team.team_coach.coach_record = {"Match Wins": 0, "Match Losses": 0, "Game Wins": 0, "Game Losses": 0}

        for i in range(len(team.lineup_losses)):
            team.lineup_wins[i] = 0
            team.lineup_losses[i] = 0


        if end_of_full_season:
            for slot, player in enumerate(sorted(team.players, key=lambda p: p.xWAR, reverse=True)):

                temp_season_object = PlayerSeason(player, season_count)
                non_overkill_effect = temp_season_object.effect - temp_season_object.overkill
                overkill_pct = round((temp_season_object.overkill / temp_season_object.effect), 4)


                if player.trait_tag[0] == "R#":
                    primary_trait_stat_1 = f"Damage Reflected Per Game: {temp_season_object.reflected:.3f}"
                    primary_trait_stat_2 = f"Total Hits Reflected Per Game: {temp_season_object.reflect_count:.3f}"
                elif player.trait_tag[0] == "X+":
                    primary_trait_stat_1 = f"Explosion Damage Per Game: {temp_season_object.explosion_dmg:.3f}"
                    primary_trait_stat_2 = f"Kills via Explosion Per Game: {temp_season_object.explosion_kills:.3f}"
                elif player.trait_tag[0] == "Hn":
                    primary_trait_stat_1 = f"Team Healing Per Game: {temp_season_object.team_heal:.3f}"
                    primary_trait_stat_2 = "N/A"
                elif player.trait_tag[0] == "Sp":
                    primary_trait_stat_1 = f"Extra Attacks Per Game: {temp_season_object.extra_attacks:.3f}"
                    primary_trait_stat_2 = "N/A"
                elif player.trait_tag[0] == "Fl":
                    primary_trait_stat_1 = f"Attacks Prevented via Stun Per Game: {temp_season_object.attacks_stunned:.3f}"
                    primary_trait_stat_2 = "N/A"
                else:
                    primary_trait_stat_1 = "N/A"
                    primary_trait_stat_2 = "N/A"


                if player.trait_tag[1] == "U-":
                    secondary_trait_stat_1 = f"Health Healed Per Game: {temp_season_object.healed:.3f}"
                    secondary_trait_stat_2 = f"Revives Per Game: {temp_season_object.revived:.3f}"
                elif player.trait_tag[1] == "V.":
                    secondary_trait_stat_1 = f"Vampire Self-heal Per Game: {temp_season_object.vamp_heal:.3f}"
                    secondary_trait_stat_2 = "N/A"
                elif player.trait_tag[1] == "Tx":
                    secondary_trait_stat_1 = f"Toxin Damage Per Game: {temp_season_object.toxin_dmg:.3f}"
                    secondary_trait_stat_2 = "N/A"
                else:
                    secondary_trait_stat_1 = "N/A"
                    secondary_trait_stat_2 = "N/A"



                player_season_params = ( player.player_id, season_count,
                                         team.team_id, team.team_seasons[season_count].team_season_id,
                                         player.amp, player.tier,
                                         player.games_played["This-Season"], player.games_played["Matches"],
                                         round((player.games_played["This-Season"] / player.games_played["Matches"]), 3),
                                         player.xWAR, player.trait_tag[0], player.trait_tag[1],
                                         player.name, player.season_of_origin, player.power, player.atk_dmg, player.atk_spd,
                                         player.crit_pct, player.crit_x, player.mit_pct, player.defense_abs, player.defense_pct,
                                         player.max_health, player.spawn_time, player.age, temp_season_object.kills,
                                         temp_season_object.deaths, temp_season_object.ticks_alive, temp_season_object.ticks_dead,
                                         temp_season_object.crit_kills, temp_season_object.damage, temp_season_object.mitigated,
                                         temp_season_object.d_pct_blocked, temp_season_object.d_abs_blocked, temp_season_object.total_attacks,
                                         temp_season_object.effect, temp_season_object.overkill, non_overkill_effect, overkill_pct,
                                         primary_trait_stat_1, primary_trait_stat_2, secondary_trait_stat_1, secondary_trait_stat_2 )

                player_season_sql = """
                INSERT INTO PlayerSeason(
                player_id, season_count, team_id, team_season_id, amp, tier, games, matches, games_per_match, xWAR, primary_trait, secondary_trait, player_name, season_of_origin,
                power, atk_dmg, atk_spd, crit_pct, crit_x, mit_pct, defense_abs, defense_pct, health, spawn_time, age,
                kills, deaths, ticks_alive, ticks_dead, crit_kills, damage, mitigated, defense_pct_blocked, defense_abs_blocked,
                attacks, total_effect, overkill_effect, non_overkill_effect, overkill_effect_pct,
                primary_trait_stat_1, primary_trait_stat_2, secondary_trait_stat_1, secondary_trait_stat_2)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                player_season_id = QUERY(player_season_sql, params=player_season_params, is_select=False)

                team_season_params = (player_season_id, team.team_seasons[season_count].team_season_id)

                team_season_sql = f"""
                                    UPDATE TeamSeason
                                    SET
                                    slot_{slot}_season_id = ?
                                    WHERE team_season_id = ?
                                    """
                QUERY(team_season_sql, params=team_season_params, is_select=False)





                player.kills = 0
                player.crit_kills = 0
                player.deaths = 0
                player.crit_data = {'Hit' : 0.0, 'Miss' : 0.0, 'Ratio' : 0.0, 'Parry' : 0.0, 'P_Miss' : 0, "P_Ratio" : 0.0, "Mitigated" : 0.0}
                player.kill_streak = {'Current' : 0, 'Peak' : 0}
                player.damage_data = {'Tesseract': 0.0, 'Total-Attacks': 0, 'Total-Damage': 0.0, 'Total-Delayed-Damage': 0.0,
                                    'Total-Delayed-X': 0.0, 'Delayed-Count': 0, 'Avg-Delayed-X': 0.0,'D% Blocked' : 0.0, "DAbs Blocked" : 0.0,
                                    'Avg-Delayed-Damage': 0.0, 'Overkill': 0.0, 'Overkill-Count': 0, 'Revived' : 0, 'Healed' : 0,
                                      'Reflected' : 0.0, 'Crit-Reflects' : 0, 'Reflect-Kills' : 0, 'Reflect-Count' : 0, 'Explosion' : 0, 'Explosion-Kills' : 0,
                                      'Toxin' : 0, 'Toxin Kills' : 0, 'Attacks Stunned' : 0, 'Vampire Healed' : 0, 'Extra Attacks' : 0, 'Team Healed' : 0,
                                      'Ticks Alive' : 0, 'Ticks Dead' : 0}
                total_games = player.games_played['All'] + player.games_played['This-Season']
                player.games_played = {'This-Season' : 0, 'All': total_games, 'Playoffs': 0, 'Matches' : 0}
                player.game_wins = 0
                player.game_losses = 0
                player.team_wins = 0
                player.team_losses = 0
                for key in player.damage_data.keys():
                    player.damage_data[key] = 0

    return teams