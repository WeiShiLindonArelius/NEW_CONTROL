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
Power (integer between 50 and 59 inclusive) - team scores x points scored for each tick alive  
Attack Speed (integer between 6 and 9 inclusive) - player attacks every x ticks  
Attack Damage (float between 49 and 63 inclusive) - x damage dealt to a random living player with each attack  
Critical Chance (float between 0.05 and 0.075 inclusive) - 100x% chance to land a critical hit with a given attack  
Critical Multiplier (float between 6 and 9 inclusive) - base damage multiplied by x for each critical hit  
Health (float between 190 and 240 inclusive) - x damage can be taken before death  
Spawn Time (integer between 6 and 8 inclusive) - player returns with full health x ticks after dying  
Mitigation Chance (float between 0.0175 and 0.0899 inclusive) - 100x% chance to take no damage from an incoming attack  
Defense % (float between 0.025 and 0.075 inclusive) - reduces all incoming attack damage by 100x%  
Defense Absolute (integer between 2 and 8 inclusive) - reduces all incoming attack damage by x  
Players can also have one of twelve primary and/or secondary special traits (one, or both, or neither), but I will get into that later.  
  
A **captain** object takes a cut of all incoming damage and boosts the team while alive. Unlike players, they do not respawn after death.  
They are made of five statistics:  
Damage Taken (float between 0.0925 and 0.1125 inclusive) - 100x% of all incoming attack damage is absorbed by the captain  
Max Health (integer between 90 and 101 inclusive) - x damage can be taken before death  
Attack Damage Bonus (float between 1.1 and 1.25 inclusive) - all player attack damage multiplied by x while alive  
Critical Damage Bonus (float between 1.25 and 1.5 inclusive) - all player critical attack damage multiplied by x while alive  
Power Bonus (float between 0.25 and 0.7 inclusive) - all player power incremented by x while alive  
  
Finally, **coach** objects boost certain players and traits for the entire game. They have four attributes.  
Lineup Modifier - changes the order or makeup of lineups within each match (see text file lineup_mod_key)  
Slots/Attributes Amplified - amplifies one offensive and one defensve statistic for one, two, or three players on the team (more later)  
Trait Amplified - amplifies special trait effects for all players having a given trait  

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

Region_{TeamName}: Match Record (game record) + [0N(game record of 0N lineup), 1N(game record of 1N lineup),...5N(game record of 5N lineup)] [[total point differential]] where the specific records of the team's lineups are green.  

The names of the teams are color-coded to show the result of their season. In the first Universal League, the top 20 teams remain in the Universal League and the other six are relegated to the qualifying round at the end of the season. 

After the first iteration of the Universal League, which is really just to get things started and determine the worst of the original Universal teams, we go into the regional leagues.

Regional leagues contain 22 teams. They play a 1-round round robin, and the top 12 teams make the double elimination playoffs. The playoffs comprise of long series of matches, where a team must beat their opponent a certain number of times by a certain amount. Once the number of matches played exceeds 2.5 times the original victory threshold, the necessary margin of victory decreases as the teams continue to play. After a number of matches equal to the original margin of victory are played, that margin decreases by 1. The margin cannot be decreased by more than 40%. The required margin and threshold increase as the playoffs progress.  

To give an example, Team 1 is playing Team 2 and the threshold is 50 matches with a required margin of victory of 10. If the score reaches 65-60 (125 total games), the required margin of victory would decrease by 1. Should neither team break through and get ahead by the required margin of victory, it would lock at 6 and go on infinitely until one team is ahead by 6.  

Playoff series are printed as follows: Winning_Team(seed) defeat Losing_Team(seed) by a score of W-L [0N(w-l), 1N(w-l)...5N(w-l)] (X of Y [P%] reached a tiebreak, and N of M [L%] were 4-0 sweeps.)  
Where X, Y, P, N, M, and L are placeholder variables.

Following the end of a region's playoffs, teams are ranked based on where they were eliminated. Within the pools with multiple teams, the ranks are decided by original seed going into the playoffs.  
Knocked out in Round 1 Loser Bracket: 9th, 10th, 11th, 12th  
Knocked out in Round 2 Loser Bracket: 7th, 8th  
Knocked out in Round 3 Loser Bracket: 5th, 6th  
Lost the Loser Bracket Finals: 4th  
Lost the Winner Bracket Loser VS Loser Bracket Champ Match: 3rd  
Lost the Grand Finals: 2nd  
Won the Grand Finals: 1st  

8 regions go through this process, each named after regions in a fantasy world in books I've written: Darkwing, Shining Core, Diamond Sea, Web of Nations, Ice Wall, Candyland, Hell's Circle, Steel Heart  

After each region is done, we move on to the qualifying rounds where teams in the top 8 of their respective regions have a chance to make it to the Universal League.

The first qualifying round is the Last Stand, made up of teams which placed 5th through 8th in their regions. Teams are sorted into eight groups of four. Each group has one 5th place finisher, one 6th place finisher, one 7th place finisher, and one 8th place finisher. The groups are random with the only restriction being that two teams from the same region can never be in the same group. Each team plays each other team in their group 15 times, and the top two of each group move onto the next stage.  

The next stage is the Pre-Qualifying, made up of teams which advanced from the Last Stand and those which finished 2nd through 4th in their regions. Teams are sorted into four groups of ten. Each group has one 2nd place finisher, one 3rd place finisher, one 4th place finisher, and two random teams that advanced from the Last Stand. The groups are random beyond that with the only other restriction being that no more than two teams from the same region can be in the same group.  

Finally, the Universal Qualifying. In season 1, with only three teams being demoted from the original 26-team Universal League, teams are split into two groups of 19. Each group has three teams demoted from the Universal League, four random 1st place regional finishers, and 12 random teams which advanced from the Pre-Qualifying. The Universal demotees are split to ensure fairness: 26th, 24th, and 21st go to Group One, and 25th, 23rd, and 22nd go to Group Two. The same principle applies in later seasons when 16 teams are demoted from the Universal League to Universal Qualifying. The teams advancing from Pre-Qualifying are split up in a similar manner.  

The top six teams of each Universal Qualifying group automatically advance to the 36-team Universal League, joining the 20 original teams that were not demoted. The 7th place finisher of each group plays the 10th place finisher of the other group starting with a 6-0 lead, and the 8th place finisher of each group plays the 9th place finisher of the other group starting with a 3-0 lead, and the winners of these four play-in series advance to the Universal League.  

From season 1 on out, the Universal League contains 36 teams. The premier league of this game is by far the longest, with six whole rounds of round robin play before the playoffs. Teams finishing 1st through 8th make the single elimination playoff bracket, and teams finishing 9th through 16th will remain in the Universal League the following season. Teams finishing 17th through 24th must play a relegation series for their spot in next season's Universal League. 17th place plays 24th place, 18th plays 23rd, 19th plays 22nd, and 20th plays 21st. The teams with the higher seed are given a head start equal to the regular season point differential between them and their opponent. After this, the playoff teams play a simple single elimination bracket with extremely long series to ensure the best team wins.  

When the Universal League is over and a team is crowned a champion, a lot happens between seasons before we go back to the regional leagues.  

Firstly, players change between seasons. The formula is pretty complicated, so I won't go into it here, but the gist is that players generally get slightly better up until their 5th season in the league, after which they get slightly and then significantly worse before being forced to retire after their 10th season. Anomalies are built in, so sometimes a player will get significantly better or worse out of nowhere, but this happens less than 5% of the time. Captains also change in a similar way.  

More importantly, teams are allowed to get rid of some of their players and replace them with new ones, either freshly created or from another team which got rid of them first. There are several different drafts, each one being different in its makeup of players and eligible teams. The teams which participate in each draft are as follows: 

Universal Draft: 20 teams which will start in the Universal League the following season, going from 20th to 1st  
Regional Drafts: teams which started the season in a regional league and did not make it to the Universal League. Each region has a separate draft.  
Void Draft: 16 teams demoted from the Universal League which will start the following season in Universal Qualifying and the 32 teams which are eliminated in the Universal Qualifying stage (20 in season 1). Starts with the worst universal qualifying teams and ends with the 21st place Universal League team.  
Second Round Draft: random order made up of an indeterminate number of teams - 1 in 3 chance for team eliminated in Universal Qualifying, 2 in 3 for team eliminated in Universal Play-In (7th-10th), and roughly 1 in 2 for a team which missed the regional playoffs.  
Third Round Draft: semi-random order made up of an indeterminate number of teams - chance for regional teams ranking 5th to 22nd ranging from 8% to 30% based on finishing seed followed by all teams which finished 21st to 36th in the Universal League  
Free Agent Draft: all teams who started in a regional league and did not play in the Universal League at an point during the season. Unlike the others, this draft class is made of all players below age 10 which were cut from a team.  

It should be noted that, while Captains are not treated like players in any other sense, they can be drafted if it is the best option for a team.  

But that raises the question: what exactly determines a good draft pick from a bad one? That brings us to the most important and coolest part of this entire code: **xWAR**.

**What is xWAR?**

xWAR, standing for Expected Wins Against Replacement, is a comprehensive player/captain metric which represents the percentage of games a team would win with this player in the lineup over and against a replacement-level player with all average stats. It was inspired by baseball's Wins Against Replacement stat, which tracks performance over the course of a player's season or career and estimates how many wins their team gained by having them instead of a replacement-level player. xWAR, though, doesn't use performance stats, it estimates it directly from the ten statistics making up a player object. Here's how I did it:  

Take a random player, put him in a random team. The team plays 100 matches against 50 random opponents, and the % winrate of games (not matches) in which the selected player was in the lineup is stored as a variable. We then put a replacement-level player with no traits and all average stats into the same lineup, they play the same 100 matches against the same 50 opponents, and their % winrate is stored as another variable. Subtract the test player's winrate from the replacement-level player winrate, and we get a single instance of rWAR (Real Wins Against Replacement). However, some players are much better in certain team systems than others, so I do this five separate times for every player I test, then I enter the average rWAR along with the player's traits and stats into a database. I did this literally 2000 times, which took several days, before moving on.  

I then took this massive dataset and trained a LightGBM model on it, with the features being the player's traits and stats, and the target being rWAR. Rather than picking random parameters for the model, I decided to use an Optuna test to run 100 trials with 100 different sets of parameters for the model and return the parameters of the model with the best R^2 value. I then trained the model on the dataset with the best parameters the Optuna test could find and imported the model to the project. Every time a player is created, and every time their stats change at the end of a season, I tell the model to predict their rWAR, and the value it returns is saved as the player's xWAR, which should represent the % game winrate a team will gain by having this player over a replacement-level player.  

This is critical to the whole game. As mentioned earlier, teams set their lineups so that the best players play the most and the worst players play the least, and this statistic determines who those players are. (Note that there is one limitation: the most that one player can play is 5/6 lineups)  

It also determines which players to draft and which ones to get rid of, which brings me to the next interesting thing: the xWAR cap, which is exactly what it sounds like: no team can draft a player which would bring them above 130 xWAR. While this very rarely is even in play, it forces teams close to the cap to either pick a player which is worse than the best remaining in the draft class or terminate a player which is better than their worst player. This is to prevent teams from dominating for too long, but again, with the way that the drafts are setup, this is rarely a problem.  

**What else is there to know?**

The above will explain just about everything. Once you go to a document like history or my_teams, you will see the process much more clearly and things will start to click into place. Keep in mind that teams with ** or !- in their name are "yours", so root for them to win!  

The last semi-important thing that I have not explained are player names and traits. A player name has four portions: their trait tags (if applicable), their tier (S, A, B, or C, which determines the range in which their statistics can fall upon creation), an amp (amplifies different stats for different tiers; see Player_Creator.py for details), and a regular human name.  

Traits, as mentioned above, are special abilities that certain players have. Players can have a primary trait, secondary trait, both, or neither. Each trait has a "multiplier", which is admittedly poorly named, which determines specific things for each trait as you will see below. The possibilities, and their respective tags which show in the name, are as follows:  

**Primary Traits**

Splitter (Sp): 30-35% chance to attack the next tick after attacking  
Exploder (X+): Upon death, deals 40-60 damage to all enemies  
Healer (Hn): Every 11-13 ticks, heals the team for a total of 36-54 health divided equally among living players  
Flasher (Fl): Upon attacking, has a 7.5-11.5% chance to prevent the affected enemy from attacking for 10-11 ticks  
Reflector (R#): Upon mitigating damage, the damage is dealt back to the enemy. If an enemy attack is NOT mitigated, there is an additional 5-10% chance to mitigate the damage and reflect it back to the enemy.  

**Secondary Traits**

Playoff Performer (Pp): minimum +2 power in the playoffs, 30-50% chance to gain an additional +2-+5  
Clutch (C%): 1.1-1.3x power and attack damage after the 52nd tick, or after the 40th tick if the game is within 100 points  
Inconsistent (I*): At the beginning of each game, 5-15% chance to have power and attack damage multiplied by 1.05-1.25 (random, not based on trait multiplier), same chance to have power and attack damage multiplied by 0.7 to 0.9 (also random)  
Toxic (Tx): Upon attacking, has a 25-33% chance to apply Toxin to the enemy. Toxin damages the enemy for 10-13 damage every tick for 6-8 ticks.  
Undead (U-): Upon death, has a 25-35% chance to revive with 56%-78% health (2.25 * trait multiplier)  
Vampire (V.): Upon attacking, has a 40-55% chance to heal for 50-70% of damage dealt (random, not based on multiplier)

**Which traits are the best?**

After training the xWAR model, I used SHAP analysis to see which traits affected xWAR the most. With the exception of Playoff Performer, which had no impact because none of the test games were playoff games, each one had a very positive impact. Each one is pretty close, though there is a decent gap between Healer and the rest. Here they are ranked by average model output increase:  

1. Healer
2. Exploder
3. Flasher
4. Inconsistent
5. Splitter
6. Clutch
7. Toxic
8. Reflector
9. Vampire
10. Undead

And that's it! If there are any questions, feel free to DM me on Instagram at choward_04 or send a message to my LinkedIn at https://www.linkedin.com/in/carterh/ . Thank you for reading, and I will be sure to update this as I add new things to this ever-growing passion project.
