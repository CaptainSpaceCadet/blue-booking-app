from django.contrib.auth.decorators import login_required
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
    HttpResponseServerError,
)
from django.shortcuts import render, redirect
from django.views.generic import ListView
from django_htmx.http import HttpResponseClientRefresh

from apps.accounts.models import UserProfile
from apps.campaigns import services
from apps.campaigns.forms import CreateCampaignForm
from apps.campaigns.models import Campaign
from apps.campaigns.services import create_campaign


class CampaignListView(ListView):
    model = Campaign

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Campaign.objects.filter(members=user.profile)
        return Campaign.objects.none()

    template_name = "campaigns/_campaign_list.html"


@login_required
def create_campaign(request):
    """
    Creating a new campaign via HTMX. Non-HTMX requests are redirected to the dashboard.

    This view handles both GET and POST requests for the campaign creation workflow.
    It expects HTMX requests and returns partial HTML responses for HTMX swaps.

    It renders the form via campaigns/_create_campaign_form.html. Campaign creation is delegated to services.create_campaign().

    - **GET**: Returns an empty campaign creation form.
    - **POST**: Validates the form data and creates a new campaign if valid, returning a HttpResponse.
        - If the form is invalid, return the campaign creation form with the errors.
        - If the form is valid and a campaign is created successfully, return a HttpResponse.
            - The HttpResponse triggers a 'campaignCreated' event to refresh campaign elements such as #campaign-list.
        - If the form is valid but a campaign is not created successfully, return a sanitized HttpResponseServerError.
            - This case would likely only occur due to non-standard errors, or foul play.

    :param request: HttpRequest
    :return:
        - Rendered campaign form partial
        - HttpResponse with HX-Trigger on success
        - HttpResponseServerError on service failure
        - HttpResponseBadRequest for unsupported methods

    :raises Http400: Bad request, occurs if the method is not GET or POST.
    :raises Http500: Internal server error, occurs if an error is raised in the service layer while creating the campaign. It is sanitized to prevent information leakage.

    **Security Notes**:
        - Only accessible to authenticated users via @login_required
        - Service layer exceptions are caught and sanitized to prevent information leakage
        - Non-HTMX requests are redirected to the dashboard
    """

    # If the request is standard html redirect to the dashboard
    if not request.htmx:
        return redirect("dashboard")

    # Handle GET Requests
    if request.method == "GET":
        # Return empty form
        form = CreateCampaignForm(user_profile=request.user.profile)
        return render(request, "campaigns/_create_campaign_form.html", {"form": form})

    # Handle POST Requests
    if request.method == "POST":
        # Submit form
        form = CreateCampaignForm(request.POST, user_profile=request.user.profile)

        if not form.is_valid():
            # On invalid input, return the form with the appropriate errors
            return render(
                request, "campaigns/_create_campaign_form.html", {"form": form}
            )

        try:
            services.create_campaign(
                request.user.profile,
                form.cleaned_data.get("title"),
                form.cleaned_data.get("description"),
            )

            response = HttpResponse("Campaign created successfully!")
            response["HX-Trigger"] = "campaignCreated"
            return response
        except Exception as e:
            print("Error creating campaign: ", e)
            return HttpResponseServerError("Something went wrong! Please try again!")

    # Fallback for other methods
    return HttpResponseBadRequest(
        "Request methods to the create campaign endpoint must be GET or POST"
    )
