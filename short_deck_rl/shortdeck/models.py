from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum

# Define the avatar choices
AVATAR_CHOICES = (
    ('avatar1.webp', 'Dog'),
    ('avatar2.webp', 'cheetah'),
    ('avatar3.webp', 'Goat'),
    ('avatar4.webp', 'raccoon'),
    ('avatar5.webp', 'panda'),
    ('avatar6.webp', 'fox'),
    ('avatar7.webp', 'owl'),
    ('avatar8.webp', 'kitten'),
    ('avatar9.webp', 'monkey'),
    ('avatar10.webp', 'moose'),
)

#User profile mdoel stores the user prfile informatioon in the database, one-one relationship with user model.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=100, blank=True)
    avatar = models.CharField(max_length=100, choices=AVATAR_CHOICES, default='avatar1.webp')
    location = models.CharField(max_length=100, blank=True) 
    
    #method to get the avatar image url
    def get_avatar_url(self):
        return f'/static/images/avatars/{self.avatar}'
    
    # method ot get the experience of the player
    def get_experience_level(self):
        hands_played_count = HandsPlayed.objects.filter(user=self.user).count()
        if hands_played_count < 100:
            return 'Novice'
        elif hands_played_count < 500:
            return 'Advanced Beginner'
        elif hands_played_count < 1500:
            return 'Intermediate'
        elif hands_played_count < 3000:
            return 'Advanced'
        else:
            return 'Expert'
    def get_experience_percentage(self):
        hands_played_count = HandsPlayed.objects.filter(user=self.user).count()
        max_hands_for_expert = 1000
        return min(hands_played_count / max_hands_for_expert * 100, 100)
    
# The game model tracks the general game information
class Game(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    total_winnings = models.IntegerField(default=0)
    hands_won = models.IntegerField(default=0)
    hands_lost = models.IntegerField(default=0)
    
# The handsplayed model tracks all the hand information which is linked ot a game
class HandsPlayed(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='hands_played') 
    hand_id = models.CharField(max_length=255)  
    cards = models.CharField(max_length=255) 
    game_actions = models.ManyToManyField('GameAction', related_name='hands_played')
    ai_cards = models.CharField(max_length=255)  
    community_cards = models.CharField(max_length=1000)  
    won = models.BooleanField(null=True)
    completed = models.BooleanField(default=False)
    small_blind = models.IntegerField(default=0)  
    big_blind = models.IntegerField(default=0)
    is_user_big_blind = models.BooleanField(default=False)

# The game actions model tracks the actions taken within each hand 
class GameAction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='actions')
    action_type = models.CharField(max_length=255)
    amount = models.IntegerField()
    stage = models.CharField(max_length=255)
    is_voluntary = models.BooleanField(default=True)
    ai_action = models.BooleanField(default=False)
    hand = models.ForeignKey(HandsPlayed, on_delete=models.CASCADE, null=True, blank=True)

# The decsion data model tracks the AI's decison data that calcualted by the CFR alogrithm
class DecisionData(models.Model):
    game_action = models.ForeignKey(GameAction, on_delete=models.CASCADE, related_name='decision_data')
    info_set_key = models.TextField()
    strategy = models.JSONField()
    action_taken = models.CharField(max_length=10)
    probabilities = models.JSONField()
    bucket_value = models.IntegerField(null=True, default=None)
    player_hand = models.CharField(max_length=255, null=True) 

# The hand strength model holds all the hand combinations used ot mkae the hand strength grid
class HandStrength(models.Model):
    cards = models.CharField(max_length=255, unique=True)
    bucket_value = models.IntegerField()
    hand_strength = models.IntegerField()
    