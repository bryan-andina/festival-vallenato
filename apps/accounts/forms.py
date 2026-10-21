"""
Authentication and registration forms adhering to Single Responsibility Principle.
"""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

User = get_user_model()


class UserRegistrationForm(UserCreationForm):
    """
    Form for registering new public voters in the Vallenato Festival platform.
    Requires first name, last name, email and secure password.
    """
    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your first name"
        })
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your last name"
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "name@example.com"
        })
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Choose a unique username"
        })
        for field_name in ["password1", "password2"]:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    "class": "form-control",
                    "placeholder": "Secure password"
                })

    def clean_email(self):
        email = self.cleaned_data.get("email").strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email address is already registered.")
        return email


class UserLoginForm(AuthenticationForm):
    """
    Styled login form for voter authentication.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter your username"
        })
        self.fields["password"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter your password"
        })
