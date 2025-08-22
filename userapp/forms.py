from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm,  UserChangeForm
from .models import CustomUser
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
import re

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    phone = forms.CharField()

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email.endswith("@gmail.com"):
            raise forms.ValidationError("Please use a valid Gmail address.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if not re.match(r"^98\d{8}$", phone):
            raise forms.ValidationError("Phone number must start with 98 and be exactly 10 digits.")
        return phone

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if not re.match(r"^[A-Za-z ]+$", username):
            raise forms.ValidationError("Name must contain only letters and spaces.")
        return username


class LoginForm(AuthenticationForm):
    pass


class ProfileUpdateForm(UserChangeForm):
    password = None  # Remove password field from the form
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone', 'profile_pic']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make username not editable (if desired)
        self.fields['username'].disabled = True
