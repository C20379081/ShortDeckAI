import os
# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'short_deck_rl.settings')
import django
django.setup()
import pycountry
from . import cards, converting
from .cards import Cards, PokerPlayer, PokerGame
from .forms import UserProfileForm, UserForm
from .forms import PlayerActionForm
from .models import UserProfile, GameAction, HandsPlayed, Game, DecisionData, HandStrength
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from copy import deepcopy
from . import CFR
from . import shared
import uuid
import time
from django.utils import timezone
from django.db.models import Sum
from collections import defaultdict
import logging
import json
from django.http import JsonResponse
import numpy as np
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from collections import Counter
from django.contrib.auth import logout
from django.db.models.functions import TruncWeek, TruncDay
from django.contrib import messages
from django.db.models import Sum
from django.contrib.auth.forms import PasswordChangeForm
from django.core.serializers.json import DjangoJSONEncoder



#Method to handle the game logic 
def shortdeck(request):
    context = {}
    bigBlind = 10
    limit = 4
    if "newHand" not in request.session or request.session["newHand"]: 
        playerList = cards.PokerPlayer.getPlayerList(2,500)
        # Retrieve the deck from the cards class
        deck = Cards.shortDeck()
        
        # Deal the players cards and the community cards and serialsie / save to the session
        playerCards = cards.dealdeck(2, deck)
        playerList[0].hand = playerCards
        request.session["playerCards"] = converting.serialise_cards(playerCards)
        request.session["deck"] = converting.serialise_cards(deck)

        #Get the curretn game id
        current_game_id = request.session.get("current_game_id")
        current_game = Game.objects.get(id=current_game_id)
        
        # tracks player's current earnings/losses
        if "balance" not in request.session:
            request.session["balance"] = 0
            balance = 0
        else:
            balance = request.session["balance"]
            
        # track player's chips initialised as 1000 at the start of a game
        if "chips" not in request.session:
            request.session["chips"] = 1000
            chips = 1000
        else:
            chips = request.session["chips"]
        
        # The player will go first hwen a new game is started.
        if "buttonPos" not in request.session:
            buttonPos = 0
            request.session["buttonPos"] = 0
        #retrieve button position passed from prior round
        else:
            buttonPos = request.session["buttonPos"]
            
        #sets button player as active and small blind/big blind bets
        activePlayer = buttonPos
        
        # Deduct blinds from balance and chips and mkae the players bet the blinds.
        if activePlayer == 0:
            # Player is on the button, so they post the small blind, the AI posts the big blind
            playerList[(activePlayer + 1) % 2].bet = bigBlind
            playerList[activePlayer].bet = int(bigBlind / 2)
            balance -= int(bigBlind / 2)  
            chips -= int(bigBlind / 2)
            
        else:
            # Player is not on the button, so they post the big blind, the AI is the small blind
            playerList[activePlayer].bet = bigBlind
            playerList[(activePlayer + 1) % 2].bet = int(bigBlind / 2)
            balance -= bigBlind 
            chips -= bigBlind

        #save blanace and chips ot the session
        request.session["balance"] = balance 
        request.session["chips"] = chips 
        
        #stores bets in session and updates player list
        request.session["AIBet"] = playerList[1].bet
        request.session["playerBet"] = playerList[0].bet
        playerBet = playerList[0].bet
        AIBet = playerList[1].bet
        
        # Initialise pot
        pot = 0 
        pot += bigBlind
        pot += int(bigBlind / 2) 
        request.session["pot"] = pot

        # Logging the hands informaiton into the handplayed model
        hand_instance = HandsPlayed.objects.create(
            user=request.user,
            hand_id=generate_hand_id(),
            cards=converting.serialise_cards(playerList[0].hand),
            ai_cards = converting.serialise_cards(playerList[1].hand),
            community_cards = converting.serialise_cards(playerList[0].communityCards),
            game = current_game,
            won=None,
            completed=False,
            small_blind=int(bigBlind / 2),
            big_blind=bigBlind,
            is_user_big_blind=(buttonPos == 1),
        )
        # Store the hand instance ID in the session
        request.session['current_hand_instance_id'] = hand_instance.id  
    
        # Get the game_id and caculate the game stats to beshwon in the poker game
        current_game_id = request.session.get("current_game_id")
        if current_game_id:
            vpip, pfr, af = calculate_game_stats(request.user, current_game_id)
            request.session["vpip"] = vpip
            request.session["pfr"] = pfr
            request.session["af"] = af
        
        # Deal AI's cards
        AI_cards = cards.dealdeck(2, deck)
        playerList[1].hand = AI_cards
        request.session["AI_cards"] = converting.serialise_cards(AI_cards)
        request.session["deck"] = converting.serialise_cards(deck)
            
        # Initialise communityCards as an empty list
        communityCards = [] 
        for p in playerList:
            p.communityCards = deepcopy(communityCards)
        request.session["communityCards"] = converting.serialise_cards(communityCards)
        
        history = []
        request.session["history"] = history

        # Used to keep trakc of how many hands thye've played
        if "hands" not in request.session:
            request.session["hands"] = 0
            hands = 0
        else:
            hands = request.session["hands"]
    
        # action log set to empty
        request.session["actionLog"] = []
        actionLog = []

        request.session["newHand"] = False
    else:
        #retrieves session variables
        deck = converting.deserialise_cards(request.session["deck"])
        playerCards = converting.deserialise_cards(request.session["playerCards"])
        AI_cards = converting.deserialise_cards(request.session["AI_cards"])
        communityCards = converting.deserialise_cards(request.session["communityCards"])
        playerBet = request.session["playerBet"]
        AIBet = request.session["AIBet"]
        buttonPos = request.session["buttonPos"]
        history = request.session["history"]
        activePlayer = request.session["activePlayer"]
        balance = request.session["balance"]
        chips = request.session["chips"]
        hands = request.session["hands"]
        actionLog = request.session["actionLog"]
        pot = request.session["pot"]
        hand_instance_id = request.session['current_hand_instance_id']
        current_game_id = request.session.get("current_game_id")
        newHand = request.session.get("newHand")
        actions = request.session["formChoices"]
        
        #puts variables into playerList
        playerList = cards.PokerPlayer.getPlayerList(2,500)
        playerList[0].bet = playerBet
        playerList[0].hand = playerCards
        
        playerList[1].bet = AIBet
        playerList[1].hand = AI_cards
    
        for p in playerList:
            p.communityCards = deepcopy(communityCards)
            
    # gets the user profile if present 
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = None  
        
    # This is where the AI is set, the file is passed into the retrieve_save method
    playerList[1].AI = cards.CFRAgent
    AIinfo, trainingItrs = shared.retrieve_save("training7000")
    playerList[1].info = AIinfo
      
    # not being used anymore, was there when claculted players decison using AI knowledge  
    AIinfo_User, trainingItrs_User = shared.retrieve_save("training3000")
    playerList[0].info = AIinfo_User

    # Gets the users choice
    context = {}
    endRound = False
    if request.method == "POST":
        choice = request.POST.get("choice")
        pot = request.session.get("pot", 0)
        
        if choice and choice != "Next Round":
            history.append(choice)
         
        if len(playerList[0].communityCards) == 0:
            stage = 'Pre-flop'
        elif len(playerList[0].communityCards) == 3:
            stage = 'Flop'
        elif len(playerList[0].communityCards) == 4:
            stage = 'Turn'
        elif len(playerList[0].communityCards) == 5:
            stage = 'River'
        
        request.session['stage'] = stage
        # Get the highest bet by either player
        highest_bet = max(playerList[0].bet, playerList[1].bet)
        # Betting limit set to 4 
        betting_limit = 4
        #retrieve history from session
        history = request.session['history']
  
        # Raise action by the user
        if choice == "Raise":
            # The amount to raise on top of matching the current highest bet
            raise_amount = 20 
            request.session.modified = True 
            # Calculate the amount needed to match the opponent's bet, then add the raise amount
            difference = playerList[1].bet - playerList[0].bet
            playerList[0].bet += difference + raise_amount
            # Update the pot with the match amount plus the raise
            raise_total = difference + raise_amount
            pot += raise_total
            # save the pot to the session
            request.session["pot"] = pot
            request.session.modified = True

            balance -= raise_total
            chips -= raise_total
            request.session["balance"] = balance
            request.session["chips"] = chips
            
            stage = request.session['stage']
            
            # Log the game action to the database
            game_action = log_game_action(
                request,
                user=request.user, 
                action_type='Raise', 
                amount=raise_total, 
                stage=stage,  
                is_voluntary=True,
                ai_action=False
            )
            # The action that the user can choice from is determined by the history
            actions = [] 
            if endRound:
                actions = []
            elif history[len(history) - limit : len(history)] == ["Raise"]*limit:
                actions = ["Call","Fold"]
            #prevents index error
            elif len(history) == 0:
                actions = ["Call","Fold","Raise"]
            #necessary response actions, fold removed when check is possible
            elif history[-1] == "Raise":
                actions = ["Call","Fold","Raise"]
                        
            elif history[-1] == "Check" or history[-1] == "Call" or history[-1]=="Round":
                actions = ["Check","Raise"]
            request.session["formChoices"] = actions
            
        # Fold action by the user
        elif choice == "Fold":
            # No change in the pot for a Fold , log action though
            stage = request.session['stage']
            request.session.modified = True 
            game_action = log_game_action(
                request,
                user=request.user,
                action_type='Fold',
                amount=0,  
                stage=stage,
                is_voluntary=True,  
                ai_action=False
            )
            actions = [] 
            if endRound:
                actions = []
            elif history[len(history) - limit : len(history)] == ["Raise"]*limit:
                actions = ["Call","Fold"]
            #prevents index error
            elif len(history) == 0:
                actions = ["Call","Fold","Raise"]
            #necessary response actions, fold removed when check is possible
            elif history[-1] == "Raise":
                actions = ["Call","Fold","Raise"]
                        
            elif history[-1] == "Check" or history[-1] == "Call" or history[-1]=="Round":
                actions = ["Check","Raise"]
            request.session["formChoices"] = actions
            
        #Check action by the user
        elif choice == "Check":
            stage = request.session['stage']
            request.session.modified = True 
            # No change in the pot for a check, but log aciton
            game_action = log_game_action(
                request,
                user=request.user,
                action_type='Check',
                amount=0,  
                stage=stage,  
                is_voluntary=True,
                ai_action=False
            )
            actions = []
            if endRound:
                actions = []
            elif history[len(history) - limit : len(history)] == ["Raise"]*limit:
                actions = ["Call","Fold"]
            #prevents index error
            elif len(history) == 0:
                actions = ["Call","Fold","Raise"]
            #necessary response actions, fold removed when check is possible
            elif history[-1] == "Raise":
                actions = ["Call","Fold","Raise"]
                        
            elif history[-1] == "Check" or history[-1] == "Call" or history[-1]=="Round":
                actions = ["Check","Raise"]
                
            request.session["formChoices"] = actions

        # Call action by the user
        elif choice == "Call":
            stage = request.session['stage']
            request.session.modified = True 
            # Calculate the difference needed to match the opponent's bet.
            difference = playerList[1].bet - playerList[0].bet
            # Update the player's bet to match the opponent's.
            playerList[0].bet += difference
            # Add only this difference to the pot.
            pot += difference
            request.session["pot"] = pot
            request.session.modified = True
            
            balance -= difference
            chips -= difference
            request.session["balance"] = balance
            request.session["chips"] = chips
            # Log the action to the db
            game_action = log_game_action(
                request,
                user=request.user, 
                action_type='Call', 
                amount=difference, 
                stage=stage, 
                is_voluntary=True,
                ai_action=False
            )
            
            actions = [] 
            if endRound:
                actions = []
            elif history[len(history) - limit : len(history)] == ["Raise"]*limit:
                actions = ["Call","Fold"]
            #prevents index error
            elif len(history) == 0:
                actions = ["Call","Fold","Raise"]
            #necessary response actions, fold removed when check is possible
            elif history[-1] == "Raise":
                actions = ["Call","Fold","Raise"]
                        
            elif history[-1] == "Check" or history[-1] == "Call" or history[-1]=="Round":
                actions = ["Check","Raise"]
                
            request.session["formChoices"] = actions
            
        # save the pot to the session 
        request.session["pot"] = pot
        request.session.modified = True
        
    #if history null user is active player unless new round 
    else:
        if history == [] and buttonPos == 1:
            activePlayer = 1
        else:
            activePlayer = 0
            
    
     # if active player is AI, do two iterations
    if activePlayer == 1:
        itrs = 2
    else:
        itrs = 1
        
    payoutFound = False
    buttonMoved = False
    outcome = ""
    # Used to determine the winner and display the cards 
    for i in range(itrs):
        if CFR.is_terminal(history,playerList):
            
            hand_instance_id = request.session.get('current_hand_instance_id')
            hand_instance = HandsPlayed.objects.get(id=hand_instance_id)

            #if last player folded, current player wins the  pot
            if history[-1] == "Fold":
                if not payoutFound:
                    #player wins
                    if activePlayer == 0:
                        # Add pot to players chips and balance
                        balance += pot
                        chips += pot
                        outcome = "AI folds. You win!"
                        # Add the following items to the handsplayed model using hand_instance
                        hand_instance.won = True
                        hand_instance.ai_cards = converting.serialise_cards(playerList[1].hand)
                        hand_instance.community_cards = converting.serialise_cards(communityCards)
                        hand_instance.completed = True
                        hand_instance.save()
                        #end of round
                        endRound=True
                        
                    #AI wins
                    else:
                        outcome = "You folded. You lose."  
                        # Add the following items to the handsplayed model using hand_instance
                        hand_instance.won = False
                        hand_instance.completed = True
                        hand_instance.ai_cards = converting.serialise_cards(playerList[1].hand)
                        hand_instance.community_cards = converting.serialise_cards(communityCards)
                        hand_instance.save()
                        endRound=True
                        
                    hands += 1
                    payoutFound = True
                    
            #go to showdown to determinw who wins the hand
            else:
                communityCards = playerList[0].communityCards
                # Hand types used for displaying hwat the player or AI won with.
                hand_types = {
                    1: "a High Card",
                    2: "One Pair",
                    3: "Two Pair",
                    4: "Three of a Kind",
                    5: "a Straight",
                    6: "a Full House",
                    7: "a Flush",
                    8: "Four of a Kind",
                    9: "a Straight Flush"
                }
                
                #best_hand gets the players best hand.
                best_hand = [PokerPlayer.calculate_hand_value(player.hand,communityCards) for player in playerList]
                winners = PokerGame.getWinningHands(best_hand)
                
                for winner in winners:
                    winner_hand_ranking = best_hand[winner][0]
                    hand_type = hand_types.get(winner_hand_ranking, "Unknown Hand")
                    
                #Check to see who wont he hand and what they won with
                if not payoutFound:
                    #if winners is less than 2 than it cant be a draw
                    if len(winners) < 2:
                        
                        # AI won the hand
                        if winners[0] == 1:
                            outcome = f"AI wins with {hand_type}"
                            # Log informaiton to the database, Handsplayed tbale 
                            hand_instance.won = False
                            hand_instance.completed = True
                            hand_instance.ai_cards = converting.serialise_cards(playerList[1].hand)  
                            hand_instance.community_cards = converting.serialise_cards(communityCards)  
                            hand_instance.save()
                            endRound=True
                            
                        # player won
                        else:
                            outcome = f"You win with {hand_type}"
                            # Add pot to chips and balance
                            balance += pot
                            chips += pot
                            # Log informaiton to the database, Handsplayed tbale
                            hand_instance.won = True
                            hand_instance.completed = True
                            hand_instance.ai_cards = converting.serialise_cards(playerList[1].hand)  
                            hand_instance.community_cards = converting.serialise_cards(communityCards)
                            hand_instance.save()
                            endRound=True
                            
                    # PLayers draw        
                    else:
                        outcome = f"It's a draw. You both have {hand_type}"
                        # Add the players bets to their chips, split the pot
                        balance += playerList[0].bet
                        chips += playerList[0].bet
                                
                        # Add the blinds back to the balance and chips
                        if activePlayer == 0:
                            balance += int(bigBlind / 2)  
                            chips += int(bigBlind / 2)
                        else:
                            balance += bigBlind 
                            chips += bigBlind
                            
                        # Log informaiton to the database, Handsplayed tbale
                        hand_instance.won = None
                        hand_instance.completed = True
                        endRound=True
                        hand_instance.ai_cards = converting.serialise_cards(playerList[1].hand)  
                        hand_instance.community_cards = converting.serialise_cards(communityCards)  
                        hand_instance.save()

                    hands += 1
                    payoutFound = True
                    
                    
            #start new round
            request.session["newHand"] = True
            request.session["balance"] = balance
            request.session["chips"] = chips
            
            # Moves the button when round is over and saves it to the session
            if endRound or history == ["Fold"]:
                if not buttonMoved:
                    buttonPos = (buttonPos + 1) % 2
                    buttonMoved = True       
            request.session["buttonPos"] = buttonPos
            endRound = True
            
        elif CFR.round_completed(history):
            history+=["Round"]
            
            # Pre-flop
            if len(playerList[0].communityCards) == 0:
                stage = "Pre-flop"
                newCards = cards.dealdeck(3, deck)  # Deal the flop
                request.session["deck"] = converting.serialise_cards(deck)
            
            # Flop
            elif len(playerList[0].communityCards) == 3:
                stage = "Flop"
                newCards = cards.dealdeck(1, deck)  # Deal the turn
                request.session["deck"] = converting.serialise_cards(deck)
            
            # Turn
            elif len(playerList[0].communityCards) == 4:
                stage = "Turn"
                newCards = cards.dealdeck(1, deck)  # Deal the river
                request.session["deck"] = converting.serialise_cards(deck)
            
            # River
            elif len(playerList[0].communityCards) == 5:
                stage = "River"
                request.session["deck"] = converting.serialise_cards(deck)
                
            # saves the stage to the ssession
            request.session['stage'] = stage

            #updates the community cards
            for player in playerList:
                player.communityCards += newCards
                
                
            #saves the serialsied and updated cards to session    
            communityCards = player.communityCards
            request.session["communityCards"] = converting.serialise_cards(communityCards)
            request.session["deck"] = converting.serialise_cards(deck)  
        
        #gets the valid actions a player/AI can take
        actions = []
        #if bet limit reached, ban raising
        if endRound:
            actions = []
        elif history[len(history) - limit : len(history)] == ["Raise"]*limit:
            actions = ["Call","Fold"]
        #prevents index error
        elif len(history) == 0:
            actions = ["Call","Fold","Raise"]
        #necessary response actions, fold removed when check is possible
        elif history[-1] == "Raise":
            actions = ["Call","Fold","Raise"]
        elif history[-1] == "Check" or history[-1] == "Call" or history[-1]=="Round":
            actions = ["Check","Raise"]
            
        context["formChoices"] = actions
        request.session["formChoices"] = actions
        
        
        # AI mkaes their actions
        if activePlayer == 1 and len(actions)>0:
            # Retrieve pot from session
            pot = request.session.get("pot", 0)
            playerList[1].history = history
            hand_instance_id = request.session.get('current_hand_instance_id')
            # gets the hand id and saves it as hand_instance
            hand_instance = HandsPlayed.objects.get(id=hand_instance_id)
            action,_,decision_data = playerList[1].AI(actions,playerList[1])    
                    
            # AI chooses raise
            if action == "Raise":
                # Last action is used to track the AI's last move for the animations
                context['last_action'] = 'AI raises'
                raise_amount = 20 
                # Calculate the amount needed to match the opponent's bet, then add the raise amount
                difference = playerList[0].bet - playerList[1].bet
                playerList[1].bet += difference + raise_amount
                # Update the pot with the rasie total
                raise_total = difference + raise_amount
                pot += raise_total
                # Gets the stage from the session
                stage = request.session['stage']
                # Log the AI's actions in the db
                game_action = log_game_action(
                request,
                user=request.user, 
                action_type='Raise', 
                amount=raise_total, 
                stage=stage,
                is_voluntary=True,
                ai_action=True
                )
                decision_data['player_hand'] = converting.serialise_cards(decision_data['player_hand'])
                
                # log the decision data using the game_action instance
                DecisionData.objects.create(
                    game_action=game_action,
                    **decision_data
                )
                
            # AI chooses raise
            elif action == "Call":
                # Last action is used to track the AI's last move for the animations
                context['last_action'] = 'AI calls'
                # Calculate the difference to match the current highest bet.
                difference = playerList[0].bet - playerList[1].bet
                # AI matches the player's bet.
                playerList[1].bet += difference
                # Add the difference to the pot
                pot += difference
            
                # Gets the stage from the session
                stage = request.session['stage']
                
                # Log the AI's actions in the db
                game_action = log_game_action(
                request,
                user=request.user, 
                action_type='Call', 
                amount=difference, 
                stage=stage, 
                is_voluntary=True,
                ai_action=True
                )
                
                decision_data['player_hand'] = converting.serialise_cards(decision_data['player_hand'])
                # log the decision data using the game_action instance
                DecisionData.objects.create(
                    game_action=game_action,
                    **decision_data 
                
                )  
            # AI chooses Fold
            elif action == "Fold":
                # No change in the pot for a Fold
                stage = request.session['stage']
                # Last action is used to track the AI's last move for the animations
                context['last_action'] = 'AI folds'
                # Log the AI's actions in the db
                game_action = log_game_action(
                    request,
                    user=request.user,
                    action_type='Fold',
                    amount=0,  
                    stage=stage,  
                    is_voluntary=True,  
                    ai_action=True
                )
                decision_data['player_hand'] = converting.serialise_cards(decision_data['player_hand'])
                # log the decision data using the game_action instance
                DecisionData.objects.create(
                    game_action=game_action,
                    **decision_data 
                
                )  
            # AI chooses Check
            elif action == "Check":
                stage = request.session['stage']
                 # Last action is used to track the AI's last move for the animations
                context['last_action'] = 'AI checks'
                # No change in the pot for a check
                # Log the AI's actions in the db
                game_action = log_game_action(
                    request,
                    user=request.user,
                    action_type='Check',
                    amount=0, 
                    stage=stage,  
                    is_voluntary=True,  
                    ai_action=True
                )
                decision_data['player_hand'] = converting.serialise_cards(decision_data['player_hand'])
                # log the decision data using the game_action instance
                DecisionData.objects.create(
                    game_action=game_action,
                   **decision_data 
                )  
            # Saves the pot ot the session
            request.session["pot"] = pot
            # Add action to the history
            history.append(action)

            # Add action to action log
            action_description = "AI " + action.lower() + "s"
            actionLog.append(action_description)
            
            # Store only the last action in the context
            context['last_action'] = actionLog[-1] if actionLog else None
        activePlayer = (activePlayer + 1) % 2
    
    # Retreive all card data from session
    deck = converting.deserialise_cards(request.session["deck"])
    playerCards = converting.deserialise_cards(request.session["playerCards"])
    AI_cards = converting.deserialise_cards(request.session["AI_cards"])
    communityCards = converting.deserialise_cards(request.session["communityCards"])

    # display community cards
    for i in range(5):
        if i+1<=len(communityCards):
            context["tableCard"+str(i+1)] = converting.cardImageURL(communityCards[i])
        else:
            context["tableCard"+str(i+1)] = converting.back_card_URL()
    
    #displays player cards
    for i in range(2):
        context["playerCard"+str(i+1)] = converting.cardImageURL(playerCards[i])
        
    #displays AI cards
    for i in range(2):
        if endRound:
            context["AI_cards"+str(i+1)] = converting.cardImageURL(AI_cards[i])
        else:
            context["AI_cards"+str(i+1)] = converting.back_card_URL()
    
    
    playerBet = playerList[0].bet
    AIBet = playerList[1].bet
    request.session["playerBet"] = playerBet
    request.session["AIBet"] = AIBet
    request.session["activePlayer"] = activePlayer
    request.session["hands"] = hands
    request.session["pot"] = pot
    vpip = request.session["vpip"]
    pfr = request.session["pfr"]
    af = request.session["af"] 
    
    # Put all required data inmto context
    context["playerBet"] = playerBet
    context["AIBet"] = AIBet
    context["balance"] = balance
    context["chips"] = chips
    context["hands"] = hands
    context["buttonPos"] = buttonPos
    context["pot"] = pot
    context["outcome"] = outcome
    context["userProfile"] = profile
    context["vpip"] = vpip
    context["pfr"] = pfr
    context["af"] = af

    # Add action log to the session
    request.session["actionLog"] = actionLog
    #log is reversed as log is displayed bottom up
    context["log"] = (actionLog + [outcome])[::-1]
    
    request.session["history"] = history
    
    return render(request, 'myfirst.html', context)

# Used to retrieve the pot from the game session
@login_required
def get_pot(request):
    pot_total = request.session.get('pot', 0)
    print(pot_total)
    return JsonResponse({"pot": pot_total})

#Used to log the game actions taken, it retrieves the current hand id and uses that.    
def log_game_action(request, user, action_type, amount, stage, is_voluntary=True,ai_action=False):
    current_hand_instance_id = request.session.get('current_hand_instance_id')

    if current_hand_instance_id is not None:
        hand_instance = HandsPlayed.objects.get(id=current_hand_instance_id)
        action = GameAction.objects.create(
            user=user,
            action_type=action_type,
            amount=amount,
            stage=stage,
            is_voluntary=is_voluntary,
            hand = hand_instance,
            ai_action = ai_action
        )
        return action

# This method is used to calcuate the game stats that are shown in the poker game. 
def calculate_game_stats(user, game_id):
    hands_played_ids = HandsPlayed.objects.filter(user=user, game_id=game_id).values_list('id', flat=True)
    
    # VPIP - count the number of unique hands where the user has voluntarily put money into the pot pre-flop
    voluntary_actions = GameAction.objects.filter(
        hand_id__in=hands_played_ids,
        user=user,
        is_voluntary=True,
        stage='Pre-flop'
    ).exclude(action_type__in=['post_blind', 'Check', 'Fold']).values_list('hand_id', flat=True).distinct().count()
    
    # Calculate the vpip and round to one decimal place
    total_hands = len(hands_played_ids)
    vpip = (voluntary_actions / total_hands * 100) if total_hands > 0 else 0
    vpip = round(vpip,1)
    
    # PFR - the frequency at whcih the player raises before the flop is dealt
    pfr_actions = GameAction.objects.filter(
        hand_id__in=hands_played_ids,
        action_type='Raise',
        stage='Pre-flop'
    ).distinct().count()
    pfr = (pfr_actions / total_hands * 100) if total_hands > 0 else 0
    pfr = round(pfr,1)
    
    # Aggression Factor - the number of aggresicve actions to passive actions 
    aggressive_actions = GameAction.objects.filter(
        hand_id__in=hands_played_ids,
        action_type__in=['Raise']
    ).count()
    passive_actions = GameAction.objects.filter(
        hand_id__in=hands_played_ids,
        action_type=['Call', 'Check']
    ).count()
    af = (aggressive_actions / passive_actions) if passive_actions > 0 else float('inf')
    af = round(af,2)
    
    return vpip, pfr, af

# Calculate VPIP
def calculate_vpip(user):
    # Retrieve all Hands played by the user
    hands_played_count = HandsPlayed.objects.filter(user=user).count()
    hands_played_ids = HandsPlayed.objects.filter(user=user).values_list('id', flat=True)
    
    # Count the number of unique hands where the user has voluntarily put money into the pot pre-flop
    voluntary_actions = GameAction.objects.filter(
        hand_id__in=hands_played_ids,
        user=user,
        is_voluntary=True,
        stage='Pre-flop'
    ).exclude(action_type__in=['post_blind', 'Check', 'Fold']).values_list('hand_id', flat=True).distinct().count()
    
    # Calculate VPIP
    vpip = (voluntary_actions / hands_played_count) * 100 if hands_played_count > 0 else 0
    vpip_2dp = round(vpip, 1)
    return vpip_2dp

#Calculate PFR
def calculate_pfr(user):
    # Retrieve the count of all hands played by the user
    hands_played_count = HandsPlayed.objects.filter(user=user).count()
    hands_played_ids = HandsPlayed.objects.filter(user=user).values_list('id', flat=True)
    # Count the number of unique hands where the user has raised pre-flop
    pre_flop_raises = GameAction.objects.filter(
        hand_id__in=hands_played_ids,
        user=user,
        action_type='Raise',
        stage='Pre-flop'
    ).values_list('hand_id', flat=True).distinct().count()
    
    # Calculate PFR
    pfr = (pre_flop_raises / hands_played_count) * 100 if hands_played_count > 0 else 0
    pfr_2dp = round(pfr,1)
    return pfr_2dp

# Calculate the AF
def calculate_aggression_factor(user):
    # Retrieve all hands played by the user
    hands_played_ids = HandsPlayed.objects.filter(user=user).values_list('id', flat=True)
    
    # Initialise counts
    aggressive_actions_count = 0
    passive_actions_count = 0

    # Iterate through each unique hand played by the user
    for hand_id in hands_played_ids:
        aggressive_actions = GameAction.objects.filter(
            hand_id=hand_id, user=user, action_type='Raise').count()
        aggressive_actions_count += aggressive_actions

        passive_actions = GameAction.objects.filter(
            hand_id=hand_id, user=user, action_type__in=['Call', 'Check']).count()
        passive_actions_count += passive_actions

    # Calculate Aggression Factor
    aggression_factor = aggressive_actions_count / passive_actions_count if passive_actions_count > 0 else float('inf')
    aggression_factor_2dp = round(aggression_factor, 2)
    return aggression_factor_2dp

#Used ot generate the hand_id for HandsPlayed, timestamp based
def generate_hand_id():
    return str(int(time.time() * 1000))

# Counts the number of hands won
def calculate_hands_won(user, game):
    return HandsPlayed.objects.filter(user=user, game=game, won=True).count()

# Counts the number of hands lost
def calculate_hands_lost(user, game):
    return HandsPlayed.objects.filter(user=user, game=game, won=False).count()

# Creates a new game instance when a new game starts and redirects to shortdeck ot start the game
def start_game(request):
    new_game = Game.objects.create(user=request.user)
    request.session['newHand'] = True

    request.session['current_game_id'] = new_game.id
    return redirect('shortdeck')

# This is called when the game has been selected to end 
def end_game(request):
    current_game_id = request.session.get('current_game_id')
    if current_game_id:
        game = Game.objects.get(id=current_game_id)
        game.end_time = timezone.now()
        balance = request.session.get('balance')
        
        # Calculate total winnings
        game.total_winnings = balance
        # Calculate hands won and lost
        game.hands_won = calculate_hands_won(request.user, game)
        game.hands_lost = calculate_hands_lost(request.user, game)
        game.save()

    # List of session variables to clear, add all the keys you want to remove
    keys_to_clear = ['current_game_id', 'pot', 'playerBet', 'AIBet', 'buttonPos', 'history', 'activePlayer', 'balance', 'hands', 'actionLog', 'newHand', 'deck', 'playerCards', 'AI_cards', 'communityCards', 'current_hand_instance_id','chips']
    for key in keys_to_clear:
        request.session.pop(key, None)
    # Redirect to the homepage
    return redirect('home') 


#Methos handles the user login, checks if the user is valid and directs to homepage
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
            return redirect('home')
    else:
        return redirect('home')

#Allows the users to register 
def register(request):
    countries = [{'code': country.alpha_2, 'name': country.name} for country in pycountry.countries]
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        location = request.POST.get('location', '')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'register.html', {'countries': countries})
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'register.html', {'countries': countries})
        else:
            user = User.objects.create_user(username=username, password=password, email=email, first_name=first_name, last_name=last_name)
            UserProfile.objects.create(user=user, location=location)
            messages.success(request, 'Registration successful.')
            return redirect('login') 
    else:
        return render(request, 'register.html', {'countries': countries})
    
# Method for the homepage / the game dahsboard
def home(request):
    context = {}
    # Check if the user is authenticated
    is_authenticated = request.user.is_authenticated
    new_user = request.GET.get('new_user', 'false') == 'true'
    context = {
        'is_authenticated': is_authenticated,
        'new_user': new_user,
    }
    # If the user is authenticated then show game dahsboard + menu options
    if is_authenticated:
        user = request.user
        # Count the number of hands played by the user
        hands_played_count = HandsPlayed.objects.filter(user=user).count()
        # calculate vpip,pfr and aggression factor 
        vpip = calculate_vpip(user)
        pfr = calculate_pfr(user)
        aggression_factor = calculate_aggression_factor(user)

        # Calculate total winnings
        total_winnings = Game.objects.filter(user=user).aggregate(Sum('total_winnings'))['total_winnings__sum'] or 0
        
        # Group winnings by week / day & prepaer data for the line grpah, the user will be able ot toggle between daily and weekly
        winnings_by_week_qs = Game.objects.filter(user=user, end_time__isnull=False) \
            .annotate(week=TruncWeek('end_time')) \
            .values('week') \
            .annotate(total_winnings=Sum('total_winnings')) \
            .order_by('week')
            
        winnings_by_day_qs = Game.objects.filter(user=user, end_time__isnull=False) \
            .annotate(day=TruncDay('end_time')) \
            .values('day') \
            .annotate(total_winnings=Sum('total_winnings')) \
            .order_by('day')

        winnings_over_time = [
            (win['week'].strftime("%Y-%m-%d"), win['total_winnings'])
            for win in winnings_by_week_qs
        ]
        
        winnings_over_time_daily = [
            (win['day'].strftime("%Y-%m-%d"), win['total_winnings'])
            for win in winnings_by_day_qs
        ]
        winnings_over_time_chart_data = {
            'daily': {
                'labels': [win[0] for win in winnings_over_time_daily],
                'datasets': [{
                    'label': "Daily Winnings",
                    'data': [win[1] for win in winnings_over_time_daily],
                    'fill': False,
                    'borderColor': "rgb(75, 192, 192)",
                    'tension': 0.1
                }]
            },
            'weekly': {
                'labels': [win[0] for win in winnings_over_time],
                'datasets': [{
                    'label': "Weekly Winnings",
                    'data': [win[1] for win in winnings_over_time],
                    'fill': False,
                    'borderColor': "rgb(75, 192, 192)",
                    'tension': 0.1
                }]
            }
        }
        
        # Prepare win ratio
        hands_won = Game.objects.filter(user=user).aggregate(Sum('hands_won'))['hands_won__sum'] or 0
        win_ratio = (hands_won / hands_played_count * 100) if hands_played_count > 0 else 0
        context.update({
            'hands_played_count': hands_played_count,
            'vpip': vpip,
            'pfr': pfr,
            'aggression_factor': aggression_factor,
            'total_winnings': total_winnings,
            'winnings_over_time_chart_data': json.dumps(winnings_over_time_chart_data, cls=DjangoJSONEncoder),
            'win_ratio': win_ratio,
            'pie_chart_data': json.dumps({
                'vpip': {'value': vpip, 'color': 'rgba(255, 99, 132, 0.2)'},
                'pfr': {'value': pfr, 'color': 'rgba(54, 162, 235, 0.2)'},
            }, cls=DjangoJSONEncoder),
        })
    return render(request, 'home.html', context)

# Manage profile method
@login_required
def manage_profile(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)

        if profile_form.is_valid():
            profile_form.save()
            # Redirect to homepage if successful
            return redirect('home')
        else:
            messages.error(request, 'Please try again')
    else:
        profile_form = UserProfileForm(instance=user_profile)

    context = {'profile_form': profile_form}
    return render(request, 'manage_profile.html', context)


# Method to change the password
@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            #authenticate the hashed password
            update_session_auth_hash(request, user)
            return JsonResponse({'success': True})
        else:
            # Collect all form error messages
            errors = form.errors.get_json_data()
            return JsonResponse({'success': False, 'errors': errors})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})

# Logout and will be redirected to home with the login pop up
def logout_view(request):
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('home')

#Method which enbales the user to select from the displayed avatars and save the selected avatar to the db
@login_required
def change_avatar(request):
    user_profile = UserProfile.objects.get(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES)
        if form.is_valid():
            new_avatar = form.cleaned_data['avatar']
            user_profile.avatar = new_avatar
            user_profile.save()
            return redirect('manage_profile')  
    else:
        form = UserProfileForm(initial={'avatar': user_profile.avatar})

    context = {
        'form': form,
        'userProfile': user_profile,
    }
    return render(request, 'change_avatar.html', context)

# this is the method fo rhte hand reivew page which enables the user to view their last hand palyed within the poker game
@login_required
def hand_review(request, hand_id=None):
    current_game = Game.objects.filter(user=request.user).order_by('-start_time').first()
    #retrieve the last hand played 
    hands_query = HandsPlayed.objects.filter(user=request.user, game=current_game, completed=True).order_by('-id')
    
    hand = None
    if hand_id:
        hand = get_object_or_404(hands_query, id=hand_id)
    elif hands_query.exists():
        hand = hands_query.first()
        hand_id = hand.id

    context = {
        "has_hands": hands_query.exists(),
        "current_game": current_game,
    }
    # If the hand exists then show the hand details
    if hand: 
        # Deserialise all the card data
        player_cards = converting.deserialise_cards(hand.cards) if hand.cards else []
        ai_cards = converting.deserialise_cards(hand.ai_cards) if hand.ai_cards else []
        community_cards = converting.deserialise_cards(hand.community_cards) if hand.community_cards else []

        
        #displays all the deserialised card data
        for i in range(2):
            context["playerCard"+str(i+1)] = converting.cardImageURL(player_cards[i])
        
        for k in range(5):
            if k < len(community_cards):
                context["tableCard"+str(k+1)] = converting.cardImageURL(community_cards[k])
            else:
                context["tableCard"+str(k+1)] = converting.back_card_URL()
                    
        for i in range(2):
                context["AI_cards"+str(i+1)] = converting.cardImageURL(ai_cards[i])
                
        actions = GameAction.objects.filter(hand=hand).order_by('id')
        
        # Organise the actions by stage
        actions_by_stage = defaultdict(list)
        for action in GameAction.objects.filter(hand=hand).order_by('id'):
            actions_by_stage[action.stage].append(action)

        context['actions_by_stage'] = dict(actions_by_stage)
        
        context["hand"] = hand
        context["actions"] = actions
            
        #Get the pot using the game actions for that hand plus the blinds
        game_actions_total = GameAction.objects.filter(hand=hand).aggregate(total=Sum('amount'))['total'] or 0
        pot = game_actions_total + hand.big_blind + hand.small_blind
        context["pot"] = pot
        
        # Determine who is the small blind and who is the big blind so the button can be displayed
        if hand.is_user_big_blind:
            context['big_blind_user'] = request.user.username
            context['small_blind_user'] = 'AI'
        else:
            context['small_blind_user'] = request.user.username
            context['big_blind_user'] = 'AI'

        context['small_blind_amount'] = hand.small_blind
        context['big_blind_amount'] = hand.big_blind
        
        # Determine who the winner was and add to view
        if hand.won is not None:
            context["winner"] = "Player" if hand.won else "AI"
        else:
            context["winner"] = "Tied"
        request.session["hand_id"]=hand_id
        request.session["newHand"] = False
    return render(request, 'hand_review.html', context)

# thia is the method for the hand reivew page which enables the user to view all their hands from the previous game, its a menu option.
@login_required
def hand_review_page(request, hand_id=None):
    # retrieve the last game
    last_game = Game.objects.filter(user=request.user).order_by('start_time').last()
    # get all the hands from the last game from the handsplayed model
    hands_query = HandsPlayed.objects.filter(game=last_game, user=request.user, completed=True).order_by('-id')
    hands = hands_query.all()
    has_hands = bool(hands) 
    context = {
        "hands": hands,
        "has_hands": has_hands,
    }
    # Check whether or not a hand was played inthe last game
    if has_hands:
        if hand_id:
            current_hand = get_object_or_404(hands_query, id=hand_id)
            request.session["hand_id"] = current_hand.id 
            hand_id = current_hand.id
        else:
            current_hand = hands_query.first()
            hand_id = current_hand.id
            

        # Prepare the cards for the side cards so they can be displayed down the right hand side
        for hand in hands:
            hand.player_cards_urls = [
                converting.cardImageURL(card) for card in converting.deserialise_cards(hand.cards)
            ] if hand.cards else []
            
            # get the total of the game aactions plus blinds
            game_actions_total = GameAction.objects.filter(hand=hand).aggregate(total=Sum('amount'))['total'] or 0
            pot = game_actions_total + hand.big_blind + hand.small_blind
            
            if hand.won:
                # Player won: Show positive amount as win
                hand.result_amount = f"Player won ${abs(pot)}"
            else:
                # Player lost or hand tied: Show positive amount as loss
                hand.result_amount = f"Player lost ${abs(pot)}"

        context["hands"] = hands
        # get the total of the game aactions plus blinds
        game_actions_total = GameAction.objects.filter(hand=current_hand).aggregate(total=Sum('amount'))['total'] or 0
        pot = game_actions_total + current_hand.big_blind + current_hand.small_blind
        context["pot"] = pot
        
        # deserialise all the cards data
        player_cards = converting.deserialise_cards(current_hand.cards) if current_hand.cards else []
        ai_cards = converting.deserialise_cards(current_hand.ai_cards) if current_hand.ai_cards else []
        community_cards = converting.deserialise_cards(current_hand.community_cards) if current_hand.community_cards else []

        #displays all the cards required for the view
        for i in range(2):
            context["playerCard"+str(i+1)] = converting.cardImageURL(player_cards[i])
        
        for k in range(5):
            if k < len(community_cards):
                context["tableCard"+str(k+1)] = converting.cardImageURL(community_cards[k])
            else:
                context["tableCard"+str(k+1)] = converting.back_card_URL()
                    
        for i in range(2):
                context["AI_cards"+str(i+1)] = converting.cardImageURL(ai_cards[i])
        
        # Organise the actions by stage 
        actions_by_stage = defaultdict(list)
        for action in GameAction.objects.filter(hand=current_hand).order_by('id'):
            actions_by_stage[action.stage].append(action)

        context['actions_by_stage'] = dict(actions_by_stage)
        
        # Determine who the winner was so it can be displayed in the view
        if hand.won is not None:
            context["winner"] = "Player" if current_hand.won else "AI"
        else:
            context["winner"] = "Tied" 
        
        # Determine who is the small blind and who is the big blind
        if current_hand.is_user_big_blind:
            context['big_blind_user'] = request.user.username
            context['small_blind_user'] = 'AI'
        else:
            context['small_blind_user'] = request.user.username
            context['big_blind_user'] = 'AI'

            context['small_blind_amount'] = current_hand.small_blind
            context['big_blind_amount'] = current_hand.big_blind

            request.session["hand_id"]=hand_id
        
    return render(request, 'hand_review_page.html', context)

# This method is where the decision data of each of the AI's actions will be displayed in the hand review view.
def decision_data_view(request, action_id):
    # get the hand its associated with
    hand_id = request.session.get("hand_id")
    decision_data = get_object_or_404(DecisionData.objects.select_related('game_action__hand'), game_action_id=action_id)
    hand = get_object_or_404(HandsPlayed, id=hand_id, user=request.user)
    game_action = get_object_or_404(GameAction, id=decision_data.game_action_id)
    current_stage = game_action.stage

    # Check if the current stage is the Pre-flop
    is_preflop = current_stage == 'Pre-flop'
    
    # Determine the actions which beloing ot the AI
    if game_action.ai_action:
        # For AI's action, use AI's cards
        cards_to_use = hand.ai_cards if hand.ai_cards else []
        
    # Deserialise the selected cards and generate image URLs
    cards = converting.deserialise_cards(cards_to_use)
    card_images = [converting.cardImageURL(card) for card in cards]
    community_cards = converting.deserialise_cards(hand.community_cards)
    
    # If its post-flop
    if not is_preflop:
        # find out the number of community cards to include based on the current stage
        if current_stage == 'Flop':
            community_cards = community_cards[:3]
        elif current_stage == 'Turn':
            community_cards = community_cards[:4]
        elif current_stage == 'River':
            community_cards = community_cards[:5]
            
        # Used to find the value of the hand post flop
        combined_cards = cards + community_cards
        hand_type, involved_cards, pair_category = evaluate_hand_for_decision_data(combined_cards)
        involved_cards_image = [converting.cardImageURL(card) for card in involved_cards]
        
    else:
        # Default values for pre-flop or other stages
        hand_type, involved_cards_images = None, []
        
    # Used to differentiate between the various buckets
    color_legend = {
        'red': 'Very strong hands',
        'purple': 'Strong hands',
        'yellow': 'Good hands',
        'green': 'Moderate hands',
        'blue': 'Weak hands',
    }
    
    # Convert card ranks to numbers for indexing
    rank_to_index = {'A': 0, 'K': 1, 'Q': 2, 'J': 3, 'T': 4, '9': 5, '8': 6, '7': 7, '6': 8}
    ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6']
    row_headers = ranks[::-1] 

    # converts card values to rank symbols
    def map_value_to_rank(value):
        value_to_rank = {14: 'A', 13: 'K', 12: 'Q', 11: 'J', 10: 'T', 9: '9', 8: '8', 7: '7', 6: '6'}
        return value_to_rank.get(value, str(value))

    # Deserialise the player hand stored in decision data
    player_hand = json.loads(decision_data.player_hand)

    # Format the probabilities to the nearest percent
    probabilities = ',  '.join(f"{action}: {round(prob * 100)}%" for action, prob in decision_data.probabilities.items())
    
    # method for the explanaitons of what the probabilites mean 
    def generate_explanations(probabilities):
        # Sort actions by probability in descending order
        sorted_actions = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
        explanations = []
        handled_actions = set()
        for action, prob in sorted_actions:
            prob_percent = round(prob * 100)
            #If a probabilty is above 0.7 then explain what it means
            if prob > 0.7:
                if action == 'Raise' and 'Raise' not in handled_actions:
                    explanation = f"Raise {prob_percent}%: Indicates an aggressive strategy with either a very strong hand or a bluff intended to pressure opponentsinto folding."
                    handled_actions.add('Raise')
                elif action == 'Check' and 'Check' not in handled_actions:
                    explanation = f" Check {prob_percent}%: Suggests a cautious approach, attempting to control the size of the pot and get to showdown cheaper or possibly checking for deception to keep the opponent bluffing."
                    handled_actions.add('Check')
                elif action == 'Call' and 'Call' not in handled_actions:
                    explanation = f"Call {prob_percent}%: Reflects confidence in the hand's value relative to the current pot without escalating the size of the pot further."
                    handled_actions.add('Call')
                elif action == 'Fold' and 'Fold' not in handled_actions:
                    explanation = f"Fold {prob_percent}%: Highly unusual as it would indicate a strategy to exit the game despite having a high probability assigned to folding. This could suggest a very conservative approach or a misinterpretation of the hand's strength."
                    handled_actions.add('Fold')
                if explanation:
                    explanations.append(explanation)
            #If its between 0.5 and 0.7 then display the message
            elif 0.5 <= prob <= 0.7:
                if action not in handled_actions:
                    if action == 'Raise':
                        explanation = f"Raise {prob_percent}%: Reflects an optimistic view of the hand's potential, suggesting a willingness to increase the stakes moderately, betting on the hand's competitiveness."
                    elif action == 'Check':
                        explanation = f"Check {prob_percent}%: Indicates a cautious strategy, preferring to avoid increasing the bet while remaining in the game to see how the hand develops."
                    elif action == 'Call':
                        explanation = f"Call {prob_percent}%: Suggests a somewhat confident stance in the hand's value, opting to match the current bet but not aggressively pushing the stakes higher."
                    elif action == 'Fold':
                        explanation = f"Fold {prob_percent}%: Unusual in this probability range, as it suggests a decision to exit the game despite a moderate chance of success, possibly indicating a risk-averse strategy."
                    explanations.append(explanation)
                    handled_actions.add(action)

        return "\n".join(explanations)
    
    # Generate explanations for included probabilities
    explanations = generate_explanations(decision_data.probabilities)
    # Build the explanatory message including both the formatted probabilities and the dynamic explanations
    explanatory_message = f"""{explanations}"""

    # Generate the grid for the hand strengths
    grid = CFR.generate_hand_strengths_grid()

    # Correctly determine positions for highlighting
    player_positions = [rank_to_index[map_value_to_rank(card['value'])] for card in player_hand]
    is_suited = player_hand[0]['suit'] == player_hand[1]['suit']

    i, j = player_positions
    if is_suited:
        grid[min(i, j)][max(i, j)]['highlight'] = True  
    else:
        grid[max(i, j)][min(i, j)]['highlight'] = True 
        
    
    # displays the grid pre flop
    grid_html = ''
    if is_preflop:
        grid_html = render_to_string('grid_template.html', {
            'grid_data': grid,
            'ranks': ranks,
            'row_headers': row_headers,
        })
    player_hand_string = ' '.join([f"{card['value']}{card['suit']}" for card in player_hand])
    
    data = {
        'info_set_key': decision_data.info_set_key,
        'strategy': decision_data.strategy,
        'action_taken': decision_data.action_taken,
        'probabilities': probabilities.strip('"'),
        'is_preflop': is_preflop,
        'card_images': card_images,
        'player_hand': player_hand_string,
        'explanatory_message': explanatory_message,
    }
    
    # only show if pre-flop
    if is_preflop:
        data.update({
            'bucket_value': decision_data.bucket_value,
            'grid_html': grid_html,
            'color_legend': color_legend,
        })
    # show if post flop    
    else:
        data.update({
            'hand_type': hand_type, 
            'involved_cards_image': involved_cards_image,
            'pair_category': pair_category,
        })
    return JsonResponse(data)

# Used to evaluate the hand for post flop view, it tells the user what the stregnth of the AI is at differnt stages which is the info the AI is learning off
@staticmethod
def evaluate_hand_for_decision_data(hand):
        
    # Deserialise the selected cards and generate image URLs
    cards = sorted(hand, key=lambda card: card.value, reverse=True)
    
    is_flush = all(card.suit == hand[0].suit for card in hand)
    is_straight, straight_high_card = PokerPlayer.check_straight(cards)
    value_counts = Counter([card.value for card in cards])
    value_count_pairs = sorted(value_counts.items(), key=lambda x: (-x[1], -x[0]))

    hand_type = None
    involved_cards = []
    pair_category = None

    # Determine hand type and involved cards
    if is_flush and is_straight:
        hand_type = "Straight Flush"
        involved_cards = [card for card in cards if card.value >= straight_high_card - 4 and card.suit == flush_suit]
    elif value_count_pairs[0][1] == 4:
        hand_type = "Four of a Kind"
        involved_cards = [card for card in cards if card.value == value_count_pairs[0][0]]
    elif is_flush:
        hand_type = "Flush"
        involved_cards = [card for card in cards if card.suit == flush_suit][:5]
    elif value_count_pairs[0][1] == 3 and value_count_pairs[1][1] == 2:
        hand_type = "Full House"
        involved_cards = [card for card in cards if card.value in (value_count_pairs[0][0], value_count_pairs[1][0])]
    elif is_straight:
        hand_type = "Straight"
        involved_cards = [card for card in cards if card.value >= straight_high_card - 4][:5]
    elif value_count_pairs[0][1] == 3:
        hand_type = "Three of a Kind"
        involved_cards = [card for card in cards if card.value == value_count_pairs[0][0]]
    elif value_count_pairs[0][1] == 2 and value_count_pairs[1][1] == 2:
        hand_type = "Two Pair"
        involved_cards = [card for card in cards if card.value in (value_count_pairs[0][0], value_count_pairs[1][0])]
    elif value_count_pairs[0][1] == 2:
        hand_type = "One Pair"
        involved_cards = [card for card in cards if card.value == value_count_pairs[0][0]]
    else:
        hand_type = "High Card"
        involved_cards = cards[:5]
        
    
    pair_categories = []
    # Categorise One Pair and Three of a Kind,  ace and king in top group, 10 to queen in the medium nad rest in the low group
    if hand_type in ["One Pair", "Three of a Kind"]:
        top_pair_value = value_count_pairs[0][0]
        if 13 <= top_pair_value <= 14:
            pair_categories.append("High Pair")
        elif 10 <= top_pair_value <= 12:
            pair_categories.append("Medium Pair")
        else:
            pair_categories.append("Low Pair")

    # categorise 2 pair hands, ace and king in top group, 10 to queen in the medium nad rest in the low group
    elif hand_type == "Two Pair":
        for pair in value_count_pairs[:2]:
            if 13 <= pair[0] <= 14:  
                pair_categories.append("High Pair")
            elif 10 <= pair[0] <= 12:  
                pair_categories.append("Medium Pair")
            else:  
                pair_categories.append("Low Pair")

    return hand_type, involved_cards, pair_categories
