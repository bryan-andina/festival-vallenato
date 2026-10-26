from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from apps.accounts.forms import UserRegistrationForm, UserLoginForm


class UserRegistrationView(CreateView):
    form_class = UserRegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("voting:edition_list")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(
            self.request,
            f"Welcome to the Vallenato Legend Festival platform, {user.first_name or user.username}! Your registration was successful."
        )
        return redirect(self.success_url)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)


class UserLoginView(LoginView):
    form_class = UserLoginForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        messages.info(
            self.request,
            f"Hello, {self.request.user.first_name or self.request.user.username}! You are now logged in."
        )
        return reverse_lazy("voting:edition_list")


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("voting:edition_list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "You have been successfully logged out. See you soon!")
        return super().dispatch(request, *args, **kwargs)
