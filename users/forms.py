from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        # default UserCreationForm Meta fields:
        #  username, password --> +age, +email
        #fields = UserCreationForm.Meta.fields + ('age',)
        fields = ('username', 'email', 'age',) # a good PEP


class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = CustomUser
        #fields = UserChangeForm.Meta.fields
        fields = ('username', 'email', 'age',)