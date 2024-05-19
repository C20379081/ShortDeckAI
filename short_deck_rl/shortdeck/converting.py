from . import cards
from .cards import Cards
from django.conf import settings
import json

# Used so the corresponding card can be assigned an image which is then displayed
def cardImageURL(card):
    # Extract suit and name directly from the Cards instance
    suit_name = card.suit.lower()
    
    # Convert value to corresponding name
    if card.value == 14:
        card_name = "A"
    elif card.value == 13:
        card_name = "K"
    elif card.value == 12:
        card_name = "Q"
    elif card.value == 11:
        card_name = "J"
    else:
        card_name = str(card.value)

    return f"/static/images/ShortDeckCards/{card_name}{suit_name}.webp"

# Used to show the back of the card when players not meant ot see them
def back_card_URL():
    return f"/static/images/ShortDeckCards/BackCard.webp"

# Used to shwo the button image
def button_posistion_URL():
    return f"/static/images/Button/button.webp"

# Used to turn the card objects into a JSON string so they can be stored for the session
def serialise_cards(cards):
    card_dicts = [card.to_json() for card in cards]
    # Convert list of card dictionaries to a JSON string
    return json.dumps(card_dicts)  

# Used to turn the JSON string back into the card  object once retirved from the session
def deserialise_cards(serialised_cards_str):
    if isinstance(serialised_cards_str, str):
        card_dicts = json.loads(serialised_cards_str)
        return [Cards.from_json(card_dict) for card_dict in card_dicts]
    else:
        # Handle the case where the data is already in the expected format
        return [Cards.from_dict(card_dict) for card_dict in serialised_cards_str]
