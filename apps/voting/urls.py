from django.urls import path
from apps.voting.views import EditionListView, CategoryListView, VotingDetailView, CastVoteView

app_name = "voting"

urlpatterns = [
    path("", EditionListView.as_view(), name="edition_list"),
    path("editions/<int:year>/categories/", CategoryListView.as_view(), name="category_list"),
    path("ballot/<int:voting_id>/", VotingDetailView.as_view(), name="voting_detail"),
    path("ballot/<int:voting_id>/vote/<int:option_id>/", CastVoteView.as_view(), name="cast_vote"),
]
