**How do I play CONTROL?**

Create and open your Codespace by signing into GitHub, clicking on the green Code button in the top right, going to Codespace, and then starting a Codespace on main.
Go to the Terminal; after the $ sign, type 'pip install -r requirements.txt' (without quotes).
Open the file control_main_true.py
Click the three lines in the top left
Click run without debugging
Watch it unfold in front of you!
Useful documents to look at while the simulation runs: my_team_results (shows in-season results for your teams),
history (shows team xWAR, accolades, season results, and draft choices for all teams in the last 5 seasons),
my_teams (shows full history for all seasons for your teams)
Most of the statistics are kept in the ControlDataBase.db SQLite database, so you can look at your own copy of that for data regarding
player seasons, team seasons, coaches, captains, and more.

**What are players, teams, captains, coaches, etc.?**

Each **team** is made up of six normal players, one captain, and one coach. The goal for each team, of course, is to score the most
points. Players score points every tick they are alive, as well as for killing other players (more on this later).
A **tick** is a unit of time in the game. Each game is made up of 72 ticks.

A **player** object is a collection of ten statistics:
Power (x points scored for each tick alive) - integer
Attack Speed (player attacks every x ticks) - integer
Attack Damage (x damage dealt to a random living player with each attack) - float
Critical Chance (x chance to land a critical hit with a given attack) - float
Critical Multiplier (base damage multiplied by x for each critical hit) - float
Health (x damage can be taken before death) - float
Spawn Time (player returns with full health x ticks after dying) - integer
Mitigation Chance (x chance to take no damage from an incoming attack) - float
Defense % (reduces all incoming attack damage by x%) - float
Defense Absolute (reduces all incoming attack damage by x) - integer
Players can also have one of twelve primary and/or secondary special traits (one, or both, or neither), but I will get into that later.

A **captain** object takes a cut of all incoming damage and boosts the team while alive. Unlike players, they do not respawn after death.
They are made of five statistics:
Damage Taken (x% of all incoming damage is taken by the captain)
Max Health (x damage can be taken before death)
Attack Damage Bonus (all player attack damage multiplied by x while alive)
Critical Damage Bonus (all player critical attack damage multiplied by x while alive)
Power Bonus (all player power incremented by x while alive)

Finally, **coach** objects boost certain players and traits for the entire game. They have four attributes.
Lineup Modifier (changes the order or makeup of lineups within each match, more later)
Slots/Attributes Amplified (amplifies one offensive and one defensve statistic for one, two, or three players on the team)
Trait Amplified (amplifies special trait effects for all players having a given trait)

**How does a match work?**

Each team has six unique lineups of four players each. There is a default lineup setup which has the best players (determined by xWAR, more later) play the most and the worst players play the least, and the lineups are in order from best to worst, but this can be modified by the coach's lineup modifier attribute.

Each **game** goes through the following loop 72 times:
Each team is awareded points equal to the combined Power of their living players.
If enough ticks have passed for a dead player to respawn, they are added to the list of living players.
A coin is flipped to determine which team will attack first.
Each living player's attack countdown variable, which starts upon their spawn equal to their attack speed, is reduced by 1.
The attacking team iterates through each of its living player, and if the player's attack_countdown variable equals 0, that player attacks
a random living player on the other team. The attacking player's attack countdown resets to their attack speed.
If the attack is lethal, the attacking team is awarded points equal to 3 times the absolute value of the dead player's health, which will obviously be negative. This means that attacks which do excessive damage beyond the receiving player's health are rewarded more points. This is called Overkill.
The other team then iterates through all of their living players, and the ones whose attack countdowns equal 0 attack the other team with Overkil applying to lethal attacks.
Repeat.

There are some other things that happen throughout a game that have to do with traits, but I will get to that later.

Each **match** is made up of between four and seven games. Remember, each team has six players, but those players are sorted into six lineups of four each, and individual games are played by those lineups.
In the regular season (the round robin phase to determine the playoff bracket), a match ends when either a team has won four games, or both teams have won three. In the former case, the winning team is awarded with one win and three points in the standings. In the latter case, both teams are awarded with one draw and one point in the standings.
In the playoffs (more on this in the season format section), when both teams have won three games, the match goes to a tiebreaker where all six players on both teams enter one game. Tiebreakers are still 72 ticks long and function the same way as normal games, just with more players.

Now, finally, let's get to what's actually showing on the screen.

**What in the world am I watching on my screen?**

The simulation starts with a league of 26 teams called the Universal League.

The teams play against one another once each, and are ranked based on their performance in the regular season.

Each match is made up of a maximum of 7 games played. Each team has 7 unique

Region_{TeamName}: Game Record (match record) + [0N(game record of 0N lineup), 1N(game record of 1N lineup),...7N(game record of 7N lineup)] [[total point differential]] where the specific records of the team's lineups are green

After the round robin, the teams prepare for the 8-team playoffs with a play-in. In the playoffs, output is given for an individual series of matches between two teams, played to a set limit with a semi-flexible* margin of victory.

In a series, teams use all of their lineups, and a match is won once one team wins 5 games. If, after using the first 8 lineups (0-7N), both teams are tied at 4, they use the 8N lineup, which is a copy of the 0N lineup of the team's best players. (See lineups for more) The format of playoff series output is as follows:

Winning_Team(seed) defeat Losing_Team by a score of X-Y [0N(w-l), 1N(w-l)...7N(w-l)] (P of Q [K%] reached a tiebreak, and N of M [L%] were 5-0 sweeps.)

Where X, Y, w, l, P, Q, K, N, M, and L are placeholder variables and a tiebreak refers to a match in which the 8N lineup was played

The output in red shows the victorious and losing teams, and the score in matches.

The output in blue shows the score bewteen each of the teams' lineups, and lineups where the losing team won more games are surrounded by **. Then, a sum of the total games won by the winning and losing teams. Notably, in rare cases, the winning team wins fewer total games.

In white, after the game summary, it shows the number of matches which were won in the first 5 games (called "sweeps"), and the number of matches which necessitated the use of the 8N lineup (called tiebreakers).

Using this new format, the 7th ranked team plays the 8th ranked team, and the winner advances to the playoffs. The 9th and 10th ranked teams play, and the loser is eliminated. The loser of the 7/8 game plays the winner of the 9/10 game, the winner advances to the playoffs and the loser is eliminated.

The playoffs are an 8-team, double elimination tournament. In the finals of each bracket, the output of a binomial test is shown to examine if the result of the playoff series was "pure chance".**

Following the first iteration of the Universal League, the simulation pauses and shows you the names of your three teams.

Then, the simulation jumps into each of the 8 Regional Leagues, which follow an identical format to the first iteration of the Universal League.

If one of your teams is in any of the regional leagues, the simulation will show the result of their season.

After each of the Regional Leagues, the simulation moves towards three stages of qualifying for the next Uni. League

Teams ranked 6th through 8th (soon to be 6th through 8th) in each Regional go to the Last Stand Tournament where they are put into random groups of 3 teams, where each group contains one 6 seed, one 7 seed, and one 8 seed and teams from the same region cannot be grouped. They play each other 80 times each, and the top two advance to the next stage.

The Pre-Qualifying Tournament is made up of the 16 teams which advanced from the Last Stand as well as the 32 teams who finished 2nd through 5th in each Regional.

This follows a Swiss Format, where teams are randomly matched up initially, and then split into groups based on their win-loss record. Teams advance after reaching 3 wins and are eliminated after reaching 3 losses.

Finally, the Universal Qualifying Tournament (with 38 teams in its first iteration and 48 afterwards) split comprised of:

The 6 worst Universal League teams
The 24 teams (out of 48) which advanced from the Pre-Qualifying Tournament
Champions (1st place) of each Regional League
They are split into two groups of 24 (19 in first iteration), each group with an even proportion of Regional Champions, Pre-Qualifying Teams, and Universal League dropouts.

Each team plays every other team within their group 7 times and are ranked based on game wins/losses. The top 5 secure a spot in the next Universal League, ranks 12th and below are eliminated, and ranks 6th through 11th enter the Universal Play-In. (tired of play ins and playoffs yet?)

After the play-in, 6 more teams enter the next Universal League, on top of the 20 who remained in the league from last season and the 10 from the group stages.

After Universal Qualifying concludes, the simulation moves to the whole point of it all: the 36-team Universal League

Each team plays one another 9 times, ranked on game record, before entering two phases of the Universal Playoffs

First, the much shorter Relegation Tournament. Teams ranked 15-30th enter a double elimination tournament;

the winner and runner-up of the tournament advance to the real playoffs as the 15 and 16 seeds respectively, and the teams who finish 21st-30th are relegated to playing in next season's Universal Qualifying, while 17th-20th secure their spot in next seasons Universal League.

The top 16 teams enter the single elimination playoffs, after which the season will conclude.

The terminal will show the teams who were promoted (including those who came from Regional Leagues but will be playing in next season's Qualifying instead of their own Regional League) and those who were Relegated

Relegated teams, those who were in the previous Universal League season and finished 12th and below Universal Qualifying, are assigned to a random Regional League.

The simulation also shows the result of the full season for all of your teams, whose names are surrounded by **.

The code moves straight to the next season, but several things happen behind the scenes.

The result of each team's season is written to 'history.txt', accessible in the codespace.

Each team drafts one, two, or three new players according to the Draft Protocol***, where each draft class and the team's own players are ranked by xWAR****.

Players get better or worse depending on their age, Tier*****, and RNG. (See Blessings, Lottery, etc.)

The simulation continues! You can change the number of seasons through the SEASONS variable in main(). Have fun!

How do CONTROL games and matches actually work behind the scenes?

CONTROL is a game fundamentally based on random number generation (RNG). Teams have 6 players, each with the following statistics: Power, Attack Damage, Attack Speed, Critical Chance, Critical Multiplier, Max Health, and Spawn Time.
Individual games are played between lineups of 4 players. Each team has 8 main lineups, the 8 best unique 4-man lineups from their roster, plus a 9th for tiebreaker situtations.
The process of an individual game is invisible, but here is roughly how it goes. (full code in Games.py)
Each team is randomly assigned "+" or "-" which determines their impact on the TESSERACT.
Games take 38 "ticks", each tick goes through every living player and does a number of things
The TESSERACT, the value around which the result of the game is determined, is adjusted by the player's Power. Positive for the + team, Negative for the - team.
If the tick is a multiple of the player's attack speed(which can be anywhere between 6 and 15), they attack a random enemy player, decreasing their health by an amount equal to their attack damage. There is also a chance, based on their critical chance, for a critical hit.
If the player dies, an amount equal to 3x the excess damage is applied to the TESSERACT. This is called "Overkill" and is tracked in stats.
All players which are not alive have their countdown incremented by one; once it hits a value equal to their "Spawn Time" statistic, they respawn.
FOOTNOTES

*Semi-flexible margin of victory: each play-in, playoff, or tournament series has an initial margin of victory that one team must cross. If Team A hits the limit of 50 wins, but the score is 50-49, the series goes on, but only for so long. After a certain amount of games, determined by a function within the best_of function in Games.py, the margin of victory will decrease. This is done so that series between very close teams do not drag on, and after a while one team is able to win by a very slim margin of victory. To preserve the accuracy of playoff series, this does not happen very often, but a failsafe is triggered in emergencies.

**Returned chance is the p-value of a binomial test testing if there is a significant difference between the winrate of the winning team and 0.50. When the winning team dominates, it returns 0 or an absurdly low number. Function is called series_test() within stat_functions.py

***Draft Protocol: ...

****xWAR: Calculated in grade_players() in leagues.py (xWAR coefficients were calculated by a personal experiment, will summarize soon

*****Tier: Players are created by functions s_tier(), a_tier(), b_tier() and c_tier(), which generate random statistics in ranges different for each Tier. Functions in Player_Creator.py
