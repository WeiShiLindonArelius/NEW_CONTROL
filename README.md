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
Most of the statistics are kept in the ControlDataBase.db SQLite database, so you can look at your own copy of that for data regarding player seasons, team seasons, coaches, captains, and more.

**What are players, teams, captains, coaches, etc.?**

Each **team** is made up of six normal players, one captain, and one coach. The goal for each team, of course, is to score the most points. Players score points every tick they are alive, as well as for killing other players (more on this later).  
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
Damage Taken (x% of all incoming damage is absorbed by the captain)  
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
The attacking team iterates through each of its living player, and if the player's attack_countdown variable equals 0, that player attacks a random living player on the other team. The attacking player's attack countdown resets to their attack speed.  
If the attack is lethal, the attacking team is awarded points equal to 3 times the absolute value of the dead player's health, which will obviously be negative. This means that attacks which do excessive damage beyond the receiving player's health are rewarded more points. This is called Overkill.  
The other team then iterates through all of their living players, and the ones whose attack countdowns equal 0 attack the other team with Overkil applying to lethal attacks.  
Repeat.  
  
There are some other things that happen throughout a game that have to do with traits, but I will get to that later.  
  
Each **match** is made up of between four and seven games. Remember, each team has six players, but those players are sorted into six lineups of four each, and individual games are played by those lineups.  
In the regular season (the round robin phase to determine the playoff bracket), a match ends when either a team has won four games, or both teams have won three. In the former case, the winning team is awarded with one win and three points in the standings. In the latter case, both teams are awarded with one draw and one point in the standings.  
In the playoffs (more on this in the season format section), when both teams have won three games, the match goes to a tiebreaker where all six players on both teams enter one game. Tiebreakers are still 72 ticks long and function the same way as normal games, just with more players.  
  
Now, finally, let's get to what's actually showing on the screen.  
  
**What in the world am I watching on my screen?**

The simulation starts with a league of 26 teams called the Universal League. This is the highest tier of play that all teams are trying to get to.

The teams play against one another once each, and are ranked based on their performance. As mentioned before, wins earn three points, draws earn one point, and losses earn zero. The standings of their season show in the following format:

Region_{TeamName}: Game Record (match record) + [0N(game record of 0N lineup), 1N(game record of 1N lineup),...5N(game record of 7N lineup)] [[total point differential]] where the specific records of the team's lineups are green

Winning_Team(seed) defeat Losing_Team by a score of X-Y [0N(w-l), 1N(w-l)...7N(w-l)] (P of Q [K%] reached a tiebreak, and N of M [L%] were 5-0 sweeps.)

Where X, Y, w, l, P, Q, K, N, M, and L are placeholder variables and a tiebreak refers to a match in which the 8N lineup was played
