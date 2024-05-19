import os
# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'short_deck_rl.settings')
import django
django.setup()
import random
import time
import os
import dill
from copy import deepcopy
from . import cards
from .cards import PokerGame, PokerPlayer
from . import node_manager
from . import dillAI
from . import shared
from .models import DecisionData, HandStrength
import json
import numpy as np

# Abstraction function used for the CFR algoriuthm
def bucketing(hand, communityCards=[]):
    # Define the card values, Ace is represented as 14 and is the highest vlaue
    card_values = {
        6: 6, 7: 7, 8: 8, 
        9: 9, 10: 10, 11: 11, 12: 12, 13: 13, 14: 14
    }
    # Assign the cards from the hand into two variables
    card1, card2 = hand
    
    # Map the card values using the assgined values to get their ranks.
    rank1, rank2 = card_values[card1.value], card_values[card2.value]
    
    # Pre flop less than 3
    if len(communityCards) < 3:
        # Initial strength is the sum of the ranks of the two cards.
        strength = rank1 + rank2

        # Pairs: If both cards have the same value (E.G: 9 spades & 9 hearts) = +8 points 
        if rank1 == rank2:
            strength += 8
            
        # Top Pairs: Jacks to Ace pairs = +10 points
        if rank1 == rank2 and rank1 >= 10:
            strength += 10
            
        # Suited: Cards of the same suit = +3 points
        if card1.suit == card2.suit:
            strength += 3

        # Connectors: cards which are adjacent / close in value = adjacent (E.G: 8 & 9) +3 points / 1 gap (E.G:  7 & 9) +1 point
        if abs(rank1 - rank2) == 1:
            strength += 2
        elif abs(rank1 - rank2) == 2:
            strength += 1
        
        # Additional condition for different, unsuited cards both 10 or above
        if card1.suit != card2.suit and rank1 != rank2 and rank1 >= 10 and rank2 >= 10:
            strength += 2
            
        # Additional Bonus for Ace-6 and Ace-7 as they are bottom end connectors
        if (rank1 == 14 and rank2 == 6) or (rank1 == 6 and rank2 == 14):
            strength += 2 
            
        elif (rank1 == 14 and rank2 == 7) or (rank1 == 7 and rank2 == 14):
            strength += 1  
    
        return strength
    
    else:
        # post-flop mor ethan 3 cards dealt, calculate the hand value considering the community cards.
        values = PokerPlayer.calculate_hand_value(hand, communityCards)
        # Round values into three groups, low, med, high
        roundedValues = [values[0]]
        # Categorise the value into buckets based on values
        for val in values:
            if val >= 6 and val <= 9:
                roundedValues.append(1)

            elif val >= 10 and val <= 12:
                roundedValues.append(2)

            elif val >= 13:
                roundedValues.append(3)
            
        return tuple(roundedValues)

# Used to find the strength of the hand using the bucketing function, and categorise the hand into one of the buckets
def hand_rankings(bucket_value):
    strength = bucket_value
    # Based on strength, they're hand is assgined a rank
    if strength > 29: return 35
    elif strength > 25: return 28
    elif strength > 23: return 25
    elif strength > 20: return 22
    else: return 17

# Converts the actions into a history string.
def history_str(history):
    symbols = {"Check": "X", "Fold": "F", "Raise": "R", "Call": "C", "Round": "_"}
    return ''.join(map(lambda action: symbols[action], history))

# Returns true if round is over
def is_terminal(history, players):
    if len(history) == 0:
        return False
    elif history[-1] == "Fold":
        return True
    if round_completed(history) and len(players[0].communityCards) == 5:
        return True

# Will return true when round is over
def round_completed(history):
    # The sequences that indicate the end of a betting round.
    end_sequences = {tuple(sequence) for sequence in [["Call", "Check"], ["Check", "Check"], ["Raise", "Call"]]}
    # Check if the last two actions match any of the end sequences.
    return tuple(history[-2:]) in end_sequences

# Calcuate the total p[ayout for all the players
def calculate_payoff(players):
    return sum([p.bet for p in players])


def CFR(deck,history,players,reachProbs,currentPlayer,sets,limit):
    # Create a deep copy of the game history to prevent changing the original history
    history = deepcopy(history)
    # Check whether the termial state has been reahced
    if is_terminal(history,players):
        # If the last action was fold then calcualte the payoff
        if history[-1] == "Fold":
            return calculate_payoff(players)
        else:
            communityCards = players[0].communityCards
            # Calculate the hand strength for each player using the community cards.
            hand_strength_player = [PokerPlayer.calculate_hand_value(player.hand, communityCards) for player in players]
            # find the winner based on the calculated hand value
            winners = PokerGame.getWinningHands(hand_strength_player)
            # If the game is a draw then return 0 / If the current player wins then return their payoff / otherwise return the negative payoff.
            if len(winners) == 2:
                return 0
            elif winners[0] == currentPlayer:
                return calculate_payoff(players)
            else:
                return -calculate_payoff(players)
            
    # Check if the previous betting round is over
    if round_completed(history):
        history += ["Round"]
        # Deal the flop if there are less than 3 community cards.
        if len(players[0].communityCards) < 3:
            newCards = cards.dealdeck(3,deck)
        # DFeal the turn / river
        else:
            newCards = cards.dealdeck(1,deck)
        # Update community cards for all players
        for player in players:
            player.communityCards += newCards
       

    #if bet limit reached, ban raising
    if history[len(history) - limit : len(history)] == ["Raise"]*limit:
        actions = ["Call","Fold"]
    #prevents index error
    elif len(history) == 0:
        actions = ["Call","Fold","Raise"]
    #necessary response actions, fold removed when check is possible
    elif history[-1] == "Raise":
        actions = ["Call","Fold","Raise"]
    elif history[-1] == "Check" or history[-1] == "Call" or history[-1]=="Round":
        actions = ["Check","Raise"]
        
    # Before entering the strategy computation in CFR, determine if it's pre-flop or post-flop
    if len(players[0].communityCards) < 3:
        # Pre-flop: Use bucketing to get the preliminary bucket value based on hand strength
        pre_flop_bucket_value = bucketing(players[currentPlayer].hand, players[0].communityCards)
        # Then use the hand_rankings function to adjust the bucket value based on the hand's rank
        bucket_value = hand_rankings(pre_flop_bucket_value)
    else:
        # Post-flop: Use the original bucketing function, which already considers community cards
        bucket_value = bucketing(players[currentPlayer].hand, players[0].communityCards)

    # Calculate the opponent's index , their posotion
    opponent = (currentPlayer + 1) % 2

    ## Retrieve the information set for the current game state and available actions.
    info_set_key = (history_str(history), bucket_value)
        
    info_set = sets.getNode(info_set_key, actions)
    # Get the current strategy from the information set.
    strategy = info_set.get_strategy(reachProbs[currentPlayer])
    
    # Initialise regrets for each action.
    newRegrets = [0 for i in range(len(actions))]

    for i in range(len(actions)):
        #gets each action and its probability of being chosen
        actionProb = strategy[i]
        action = actions[i]
        #modifies current player's reach probability
        newReachProbs = reachProbs.copy()
        newReachProbs[currentPlayer] *= actionProb
        
        # Simulate the game state after taking the action.
        player = deepcopy(players)
        if action == "Raise":
            player[currentPlayer].bet = player[opponent].bet + 20 
        elif action == "Call":
            player[currentPlayer].bet = player[opponent].bet

        d = deepcopy(deck)

        # Recursively call CFR for the new game state.
        newRegrets[i] = -CFR(d, history + [action], player, newReachProbs, opponent, sets, limit)

    #value is regrets weighted by action probability
    nodeValue = 0
    # Calculate the expected utility of the node.
    for i in range(len(strategy)):
        nodeValue += strategy[i] * newRegrets[i]

    # Update cumulative regrets for each action in the information set.
    for i in range(len(strategy)):
        regret = reachProbs[opponent] * (newRegrets[i] - nodeValue)
        info_set.update_regret(i, regret)

    return nodeValue

# Function used to train the agent, the betting limit is 4
def train(sets,num_iterations, limit=4):
    for i in range(num_iterations):
        #creates fresh player list and deck
        playerList = cards.PokerPlayer.getPlayerList(2,300)
        deck = cards.Cards.shortDeck()
        history = []
        #gives both players their cards
        for player in playerList:
            player.hand = cards.dealdeck(2,deck)
        #sets first player as small blind, second as big
        playerList[0].bet = 10
        playerList[1].bet = 20
        #performs 1 iteration of training
        value = CFR(deck,history,playerList,[1,1],0,sets,limit)
    return value


# Used to create the hand stregnth table which ll the possible hand combinations, needed for creating the grid for the hand review
def generate_and_store_hand_strengths():
    card_ranks = ['6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    suits = ['hearts', 'diamonds', 'clubs', 'spades']
    combinations = []
    for rank1 in card_ranks:
        for suit1 in suits:
            for rank2 in card_ranks:
                for suit2 in suits:
                    if rank1 == rank2 and suit1 == suit2:
                        continue
                    # Mapping for converting rank characters to numeric values
                    rank_to_value = {'6': 6, '7': 7, '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}

                    # Correctly formatted hand for bucketing function
                    formatted_hand = [
                        {'value': rank_to_value[rank1], 'suit': suit1},
                        {'value': rank_to_value[rank2], 'suit': suit2}
                    ]

                    # Calculate the bucket value and hand strength
                    bucket_value = bucketing(formatted_hand, [])
                    hand_strength = hand_rankings(bucket_value)

                    # Store in the database
                    HandStrength.objects.update_or_create(
                         cards=json.dumps(formatted_hand),
                         defaults={'bucket_value': bucket_value, 'hand_strength': hand_strength}
                     )
                    combinations.append(formatted_hand)

    return {'status': 'Completed', 'combinations': len(combinations)}

# Function also used for creatig the grid
def map_value_to_rank(value):
    value_to_rank = {14: 'A', 13: 'K', 12: 'Q', 11: 'J', 10: 'T', 9: '9', 8: '8', 7: '7', 6: '6'}
    return value_to_rank[value]

# Funciton ot generate the hand strength grid
def generate_hand_strengths_grid():
    # Initialise an empty grid. Using None as a placeholder for now.
    grid_size = 9  # From 6 to Ace
    grid = np.empty((grid_size, grid_size), dtype=object)
    
    # Retrieve all hand combinations from the database
    hand_combinations = HandStrength.objects.all()
    
    # Convert card ranks to numbers for indexing
    rank_to_index = {'A': 0, 'K': 1, 'Q': 2, 'J': 3, 'T': 4, '9': 5, '8': 6, '7': 7, '6': 8}
    
    for combo in hand_combinations:
        cards_list = json.loads(combo.cards)
        
        rank1 = map_value_to_rank(cards_list[0]['value'])
        rank2 = map_value_to_rank(cards_list[1]['value'])
        is_suited = cards_list[0]['suit'] == cards_list[1]['suit']
        
        i, j = rank_to_index[rank1], rank_to_index[rank2]
        grid_value = {'bucket_value': combo.bucket_value, 'category': combo.hand_strength}
        
        if is_suited:
            grid[min(i, j)][max(i, j)] = grid_value
        else:
            grid[max(i, j)][min(i, j)] = grid_value

    # The grid now has the largest values at the top left and decreases towards the bottom right.
    return grid


if __name__ == "__main__":
    """
    saveDir = 'training3/'
    dillAI.new_training_file(saveDir)
    info = node_manager.NodeManager()  # Initializing a new NodeManager instance here.
    itrs = 0  # Starting iteration count from zero for a new session.
    mins = float(input("Train for how many mins?\n"))
    print("Processing...")
    dillAI.train_time(info, mins, itrs, saveDir=saveDir, saveInterval=1000)
    """
    
    # Continue existing training
    pickle_file_path = 'training4'
    node_manager, start_itr = shared.retrieve_save(pickle_file_path)
    additional_training_minutes = 10
    save_directory = "training4"
    save_interval = 100
    dillAI.train_time(node_manager, additional_training_minutes, start_itr, limit=4, saveDir=save_directory, saveInterval=save_interval)
    print("Training continued successfully.")