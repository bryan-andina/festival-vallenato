from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, DetailView
from apps.voting.models import Edition, Category, Voting, Option, Vote


class EditionListView(ListView):
    model = Edition
    template_name = "voting/edition_list.html"
    context_object_name = "editions"

    def get_queryset(self):
        return Edition.objects.filter(is_active=True).prefetch_related("categories")


class CategoryListView(ListView):
    model = Category
    template_name = "voting/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        self.edition = get_object_or_404(
            Edition,
            year=self.kwargs.get("year"),
            is_active=True
        )
        return Category.objects.filter(
            edition=self.edition,
            is_active=True
        ).prefetch_related("votings")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["edition"] = self.edition
        return context


class VotingDetailView(DetailView):
    model = Voting
    template_name = "voting/voting_detail.html"
    context_object_name = "voting"
    pk_url_kwarg = "voting_id"

    def get_queryset(self):
        return Voting.objects.select_related(
            "category", "category__edition"
        ).prefetch_related("options")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["options"] = self.object.options.filter(is_active=True)
        if self.request.user.is_authenticated:
            context["user_vote"] = Vote.objects.filter(
                user=self.request.user,
                voting=self.object
            ).select_related("selected_option").first()
        return context


class CastVoteView(LoginRequiredMixin, View):
    def post(self, request, voting_id, option_id):
        voting = get_object_or_404(Voting, pk=voting_id)
        option = get_object_or_404(Option, pk=option_id, voting=voting, is_active=True)

        if not voting.is_currently_open:
            messages.error(request, "Esta votación no se encuentra abierta para participar.")
            return redirect("voting:voting_detail", voting_id=voting.id)

        if Vote.objects.filter(user=request.user, voting=voting).exists():
            messages.warning(request, f"Ya has emitido tu voto en '{voting.title}'. Solo se permite un voto por usuario.")
            return redirect("voting:voting_detail", voting_id=voting.id)

        ip = request.META.get("HTTP_X_FORWARDED_FOR")
        if ip:
            ip = ip.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")

        Vote.objects.create(
            user=request.user,
            voting=voting,
            selected_option=option,
            ip_address=ip or "127.0.0.1"
        )
        messages.success(request, f"¡Tu voto por '{option.candidate_name}' ha sido registrado exitosamente!")
        return redirect("voting:voting_detail", voting_id=voting.id)
