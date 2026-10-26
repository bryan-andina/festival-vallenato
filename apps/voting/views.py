from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView
from apps.voting.models import Edition, Category, Voting


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
        return context
