from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError, transaction
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
                category=self.object.category,
                edition=self.object.category.edition
            ).select_related("selected_option", "voting").first()
        return context


class CastVoteView(LoginRequiredMixin, View):
    def post(self, request, voting_id, option_id):
        voting = get_object_or_404(
            Voting.objects.select_related("category", "category__edition"),
            pk=voting_id
        )
        category = voting.category
        edition = category.edition

        if not edition.is_active:
            messages.error(request, "Esta edición del festival no se encuentra activa.")
            return redirect("voting:voting_detail", voting_id=voting.id)

        if not category.is_active:
            messages.error(request, "Esta categoría no se encuentra habilitada para participar.")
            return redirect("voting:voting_detail", voting_id=voting.id)

        if not voting.is_currently_open:
            messages.error(request, "Esta votación no se encuentra abierta para participar.")
            return redirect("voting:voting_detail", voting_id=voting.id)

        option = get_object_or_404(Option, pk=option_id, voting=voting, is_active=True)

        if Vote.objects.filter(user=request.user, category=category, edition=edition).exists():
            messages.warning(
                request,
                f"Ya has emitido tu voto en la categoría '{category.name}' para la edición {edition.year}. Solo se permite un voto por categoría."
            )
            return redirect("voting:voting_detail", voting_id=voting.id)

        ip = request.META.get("HTTP_X_FORWARDED_FOR")
        if ip:
            ip = ip.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")

        try:
            with transaction.atomic():
                Vote.objects.create(
                    user=request.user,
                    edition=edition,
                    category=category,
                    voting=voting,
                    selected_option=option,
                    ip_address=ip or "127.0.0.1"
                )
        except IntegrityError:
            messages.warning(
                request,
                f"Ya has emitido tu voto en la categoría '{category.name}' para la edición {edition.year}."
            )
            return redirect("voting:voting_detail", voting_id=voting.id)

        messages.success(request, f"¡Tu voto por '{option.candidate_name}' ha sido registrado exitosamente!")
        return redirect("voting:voting_detail", voting_id=voting.id)
