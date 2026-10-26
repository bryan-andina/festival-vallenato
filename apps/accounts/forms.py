from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

User = get_user_model()


class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Ingresa tu nombre"
        })
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Ingresa tu apellido"
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "nombre@ejemplo.com"
        })
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Elige un nombre de usuario"
        })
        for field_name in ["password1", "password2"]:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    "class": "form-control",
                    "placeholder": "Contraseña segura"
                })

    def clean_email(self):
        email = self.cleaned_data.get("email").strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya existe un usuario registrado con este correo electrónico.")
        return email


class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Ingresa tu usuario"
        })
        self.fields["password"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Ingresa tu contraseña"
        })
