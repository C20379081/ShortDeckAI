import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'short_deck_rl.settings')
import django
django.setup()
import random
from . import shared
import itertools
from itertools import combinations
from .node_manager import Node, NodeManager
from copy import deepcopy
import json
from .models import DecisionData, HandsPlayed
import csv

class Cards:
    def __init__(self, value, suit):
        # Initialise a card with a value and a suit
        self.value = value
        # Assign a name to the card based on its number valeu
        if value == 14: self.name = "A"
        elif value == 13: self.name = "K"
        elif value == 12: self.name = "Q"
        elif value == 11: self.name = "J"
        # Use the numeric value for number cards, below jack
        else: self.name=str(value)

        self.suit = suit
        
    # Represnts the ShortDeck deck of cards (2 to 5 removed), this function is used to get the deck of cards  
    def shortDeck():
        deck = []
        suits = ["hearts", "diamonds", "clubs", "spades"]
        # Create cards for each suit, from 6 to Ace (14).
        for suit in suits:
            for num in range(6,15):
                deck.append(Cards(num,suit))
        return deck
    
    # Serialise the card into a JSON serialisable dictionary
    def to_json(self):
        return {
            'value': self.value,
            'suit': self.suit,
        }
        
    # Create a Cards object from a dictionary.
    @staticmethod
    def from_json(json_data):
        # Deserialise the JSON data back into a Cards object
        return Cards(json_data['value'], json_data['suit'])
    
def dealdeck(num, deck):
    # Selects random cards from the deck
    hand = random.sample(deck, num)
    # Removes the selected cards from the deck
    for card in hand:
        deck.remove(card)
    return hand

# Deals 2 cards to each player, which removes them from the deck
def deal(deck,playerList):
    for player in playerList:
        # Checks if the hand is over or not, if not deal cards
        if not player.hand_over:
            player.hand += dealdeck(2,deck)
            
# AI bot that acts rnadomly for testing the CFR AI agent 
def RandomBot(choices,player):
    choice = random.choices(choices)[0]
    value = 0
    if choice == "Raise":
        value = 20
        return choice, value, None
    else:
        return choice, value, None
    
# Function represneting the CFR agent
def CFRAgent(choices,player):
    # Import required for the agent, get a circular import error if outisde function
    from .CFR import CFR, bucketing, history_str, hand_rankings
    
    #gets attributes from player object
    hand = player.hand
    communityCards = player.communityCards
    history = player.history
    info = player.info

    # Determine the game stage either pre-flop or post-flop
    is_pre_flop = len(communityCards) < 3
    # For pre flop it will be seperated into hand rnaking buckets, post flop it wont
    if is_pre_flop:
        pre_flop_strength = bucketing(hand, communityCards)
        bucket_value = hand_rankings(pre_flop_strength)
    else:
        bucket_value = bucketing(hand, communityCards)
        
    # Create a key for retrieving the corresponding information set
    info_set_key = (history_str(history), bucket_value)
    info_set = info.getNode(info_set_key, choices)
    # Retrieve the average strategy for the current information set
    strategy = info_set.get_average_strategy()
    
    # Used for checking the output for debugging
    print("infosetkey: ",info_set_key)
    print("infoset: ",info_set)
    print("strategy: ",strategy)
    print("choices: ",choices)
    print("bucket value: ",bucket_value)

    # Select an action based on the calculated strategy probabilities
    choice = random.choices(choices,strategy)[0]
    
    amount = 0
    if choice == "Raise":
        amount = 20
    
    probabilities = {action: prob for action, prob in zip(choices, strategy)}

    # Retrun values used for the decison data, analysing the AI's decision
    return choice, amount,{
        'info_set_key': str(info_set_key),
        'strategy': strategy,
        'probabilities': probabilities,
        'action_taken': choice,
        'bucket_value': pre_flop_strength if is_pre_flop else None,
        'player_hand': hand
    }

# Was used for chekcing the user decisons but it doesnt work correclty so it's removed
def UserStrategyRecommendation(player, info, choices, history):
    from .CFR import CFR, bucketing, history_str
    
    is_pre_flop = len(player.communityCards) < 3
    if is_pre_flop:
        bucket_value = bucketing(player.hand, player.communityCards)
    else:
        bucket_value= bucketing(player.hand, player.communityCards)

    # Create a key for retrieving the corresponding information set
    info_set_key = (history_str(history), bucket_value)
    info_set = info.getNode(info_set_key, choices)
    # Retrieve the average strategy for the current information set
    strategy = info_set.get_average_strategy()
    
    probabilities = {action: prob for action, prob in zip(choices, strategy)}

    # return vlaues for user decision data
    response = {
        "strategy": strategy,
        "probabilities": probabilities,
        "bucket_value": bucket_value if is_pre_flop else None,
    }
    return response

# Method to represnet the actions of the poker player
class PokerPlayer:
    
    HAND_RANKINGS = {
        "High Card": 1,
        "One Pair": 2,
        "Two Pair": 3,
        "Three of a Kind": 4,
        "Straight": 5,
        "Flush": 7,
        "Full House": 6,
        "Four of a Kind": 8,
        "Straight Flush": 9
    } 
     
    def __init__(self, chips=2000):
        self.chips = chips  # The player's total chips
        self.current_bet = 0  # The current bet of the player
        self.hand = []  # The Players hand
        self.is_folded = False  # Boolean whether they've folded
        self.is_all_in = False  # Boolean for all in (bet all their chips)
        self.hand_strength = None  # Signinfies hand strength
        self.communityCards = [] # Community cards dealt, visible to all players
        self.hand_over = False # Indicates if the hand is over
        self.history =[] # The player's action history
        self.info = None # Placeholder for storing player-specific information, possibly for strategy use.
        self.choices = []
        
    # Resets player attributes for a new hand and returns used cards to the deck.
    def reset_for_new_hand(self, deck):
        deck += self.hand
        self.hand = []
        self.communityCards = []
        self.current_bet = 0
        self.is_folded = False
        self.is_all_in = False
        self.hand_strength = None
        self.history = []
    
    # Generate a list of PokerPlayer objects.
    def getPlayerList(n,chips):
        playerList = []
        for i in range(n):
            playerList.append(PokerPlayer(chips))
        return playerList
    
    # Player folds and does not participate in the rest of the round
    def fold(self):
        self.is_folded = True
        self.current_bet = 0
    
    # Player matches the largest bet
    def call(self, largestBet, pot):
        # Condition where the bet is larger than the available chips so have to go all in to call
        if largestBet-self.current_bet > self.chips:
            self.current_bet += self.chips
            pot += self.chips
            self.all_in = True
        # Normal call condition players bet is equal to the largest bet
        else:
            # Find how much more they need to add to their current bet to match, dedcut from chips, add it to the pot and update player's current bet
            bet_differnce = largestBet - self.current_bet
            self.chips -= bet_differnce
            pot += bet_differnce
            self.current_bet = largestBet
        return pot
        
    def raise_bet(self, pot, largestBet, amount):
        # Error checking for the raise option
        if amount <= largestBet:
            raise ValueError("Raise amount must be greater than the current largest bet.")
        if amount > self.chips:
            raise ValueError("Raise amount cannot exceed player's available chips.")
        
        # Proceed with raise logic, similar logic as call
        bet_difference = amount - self.current_bet
        self.chips -= bet_difference
        self.current_bet += bet_difference
        pot += bet_difference
        largestBet = amount
        
        return pot, largestBet

    # Player bets all their chips
    def all_in(self):
            self.raise_bet(self.current_bet, self.chips)
            self.is_all_in = True
            
    # Evaluates the best hand from a player's cards and community cards.
    @staticmethod
    def calculate_hand_value(hand, community_cards):
        # Initialise a placeholder for the best hand found, Used to store hand ranking and tie-breaking information.
        best_hand = [0,0,0,0,0,0]
        # Generate all possible 5-card combinations from the 7 available cards (2 hole cards + 5 community cards) = 21 combinations
        for hand in combinations(hand+community_cards,5):
            # For each combination, evaluate the hand to get its ranking
            current_hand_ranking = PokerPlayer.evaluate_hand(list(hand))[0]

            # Prepare a list to compare the current combination's ranking against the best found so far
            compare = [best_hand, current_hand_ranking]

            # Determine which hand is better based on the game's hand ranking logic
            bestIndex = PokerGame.getWinningHands(compare)[0]

            # Update the best hand if the current hand is better
            best_hand = compare[bestIndex]
 
        return best_hand
            

    @staticmethod
    def evaluate_hand(hand):
        # Sort the hand by card value in descending order for easier evaluation
        hand = sorted(hand, key=lambda card: card.value, reverse=True)
        is_flush = all(card.suit == hand[0].suit for card in hand)
        
        # Check for straight, including Ace as low
        is_straight, straight_high_card = PokerPlayer.check_straight(hand)

        # Count occurrences of each card value
        value_counts = {card.value: sum(card.value == x.value for x in hand) for card in hand}
        value_count_pairs = sorted(value_counts.items(), key=lambda x: (-x[1], -x[0]))

        # Initialize rankings and msg
        rankings = [0, 0, 0, 0, 0, 0]
        msg = ""
            
        # Straight FLush
        if is_flush and is_straight:
            rankings[0] = 9
            msg = "Straight Flush"
            
        # Four of a kind
        elif value_count_pairs[0][1] == 4:
            rankings[0] = 8
            rankings[1] = value_count_pairs[0][0] 
            msg = "Four of a Kind"
            
        # Flush
        elif is_flush:
            rankings[0] = 7
            # High card values for flush
            for i, card in enumerate(hand):
                rankings[i + 1] = card.value
            msg = "Flush"
           
        # Full House 
        elif value_count_pairs[0][1] == 3 and value_count_pairs[1][1] == 2:
            rankings[0] = 6
            rankings[1] = value_count_pairs[0][0]  # Three of a kind value
            rankings[2] = value_count_pairs[1][0]  # Pair value
            msg = "Full House"
            
        # Striaght
        elif is_straight:
            rankings[0] = 5
            msg = "Straight"
            
        # Three of a kind 
        elif value_count_pairs[0][1] == 3:
            rankings[0] = 4
            threeOkind = value_count_pairs[0][0] 
            rankings[1] = threeOkind
            extraCard = [i for i in hand if i.value != threeOkind]
            rankings[2] = extraCard[-1].value
            rankings[3] = extraCard[-2].value
            msg = "Three of a Kind"
            
        # Two pair
        elif value_count_pairs[0][1] == 2 and value_count_pairs[1][1] == 2:
            rankings[0] = 3
            rankings[1] = value_count_pairs[0][0]  # Higher pair value
            rankings[2] = value_count_pairs[1][0]  # Lower pair value
            rankings[3] = [i for i in hand if not i.value in value_count_pairs][0].value
            msg = "Two Pair"
            
        # One pair
        elif value_count_pairs[0][1] == 2:
            rankings[0] = 2
            rankings[1] = value_count_pairs[0][0] 
            extraCard = [i for i in hand if not i.value in value_count_pairs]
            rankings[2] = extraCard[-1].value
            rankings[3] = extraCard[-2].value
            rankings[4] = extraCard[-3].value
            msg = "One Pair"
            
        # High card    
        else:
            rankings[0] = 1
            for i, card in enumerate(hand):
                rankings[i + 1] = card.value
            msg = "High Card"
        return rankings, msg
    
    #Check for a straight in the hand, considering Ace as both high and low.
    @staticmethod
    def check_straight(hand):
        # Extract the values from the hand and sort them, removing duplicates
        values = sorted(set(card.value for card in hand), reverse=True)

        # The Ace can be high (14) or low (5), so check both conditions
        straight = False
        high_card = None
        
        # Check for the special case of a low Ace straight first (A-6-7-8-9)
        if set([14, 6, 7, 8, 9]).issubset(set(values)):
            return True, 5  # Return True with '5' as the highest card in the A-6-7-8-9 straight

        # Check for normal straights
        for i in range(len(values) - 4):
            if values[i] - values[i + 4] == 4:
                straight = True
                high_card = values[i]
                break
            # Check sequences of 5 for a straight, allowing for internal sequence breaks
            sequential = True
            for j in range(4):
                if values[i + j] - 1 != values[i + j + 1]:
                    sequential = False
                    break
            if sequential:
                straight = True
                high_card = values[i]
                break

        return straight, high_card
        
class PokerGame:
    def __init__(self, players):
        self.players = players
        self.deck = Cards.shortDeck()
        self.community_cards = []
        self.pot = 0
        self.current_round = 'pre-flop'
        self.history = []
          
    # Check to see if there is a winner, returns (True, winning_player), otherwise returns (False, None)
    def check_game_won(self, player_list):
        active_players = [player for player in player_list if not player.is_folded and not player.hand_over]
        if len(active_players) == 1:
            # Only one player remaining, they are the winner
            return True, active_players[0]
        else:
            # More than one player still in the game
            return False, None


    @staticmethod
    def getWinningHands(rank_list, compare_num=0, to_compare=None):
        if to_compare is None:
            to_compare = list(range(len(rank_list)))

        # Initialise the highest rank and the list of potential winners.
        highest_rank = -1
        potential_winners = []

        # Iterate over each hand that is still in contention.
        for hand_index in to_compare[:]: 
            hand_rank = rank_list[hand_index][compare_num]
            
            # Check if the current hand has the highest rank found so far.
            if hand_rank > highest_rank:
                # If a new highest rank is found, update the list of winners.
                highest_rank = hand_rank
                potential_winners = [hand_index]
            elif hand_rank == highest_rank:
                # If the current hand has a rank equal to the highest, add it to the list of winners.
                potential_winners.append(hand_index)

        # only include the potential winners.
        to_compare[:] = potential_winners

        # Determine if a set of winners has been found.
        if len(potential_winners) == 1 or highest_rank == 0 or compare_num == 5:
            return potential_winners
        else:
            # if there's still a tie call again
            return PokerGame.getWinningHands(rank_list, compare_num + 1, to_compare)
