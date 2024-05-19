from django import forms
from .models import UserProfile, AVATAR_CHOICES
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User

# This class is a form for the UserProfile model 
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['nickname', 'avatar' , 'location']
        widgets = {
            'avatar': forms.Select(choices=AVATAR_CHOICES)
        }
        
 # This form is for the User model fields
class UserForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

# This ofrm handles the players actions
class PlayerActionForm(forms.Form):
    CHOICES = [
        ('fold', 'Fold'),
        ('call', 'Call'),
        ('raise', 'Raise'),
        ('bet', 'Bet'),
    ]
    action = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect)
    bet_amount = forms.IntegerField(required=False)
    
# forms class used to chnage the user passowrd in the user model
class PasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(label="Current Password", widget=forms.PasswordInput)
    new_password1 = forms.CharField(label="New Password", widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="Confirm New Password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('old_password', 'new_password1', 'new_password2')