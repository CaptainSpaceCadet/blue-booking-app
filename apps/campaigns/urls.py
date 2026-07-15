from django.urls import path
from apps.campaigns import views

app_name = "campaigns"

urlpatterns = [
    path("campaign-list/", views.CampaignListView.as_view(), name="campaign-list"),
    path("create-campaign/", views.create_campaign, name="create-campaign"),
]
