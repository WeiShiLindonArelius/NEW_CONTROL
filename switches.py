#this file contains a bunch of booleans to toggle game options

activate_perks = False #For running long simulations with no player input, perks are pointless and throw noise in the mix

pick_perks = False

make_coach_decisions = False

jackson_playing = True #8 teams for True, 4 for False

use_saved = False #there is an issue with teams being added into regional leagues twice
#in the case that crashed it most recently, I found that new teams are being created after season 2 when
#there are seemingly more than enough relegated teams to fill the spots
#Also, the Universal League's numbers go down every season, and I found a team winning a relegation match and then
#appearing in the Hell's Circle league the next season, which shouldn't happen even if they lost and were relegated
#The team which they beat was relegated correctly and appeared in Universal Qualifying the following season

#I HAVE DECIDED TO ABANDON PICKLE ENTIRELY, AS THERE SEEMS TO BE A DIFFERENT ERROR EVERY TIME AND IT IS JUST NOT WORKING
#WHEN I PICK THIS UP AGAIN, I SHOULD INTEGRATE EVERYTHING INTO THE SQLITE DATABASE AND LOAD IT FROM THERE


NO_SQL = True

game_length = 6

SEASONS = 250

cup_frequency = 500 #cup will happen every X seasons

caps = [130] * SEASONS