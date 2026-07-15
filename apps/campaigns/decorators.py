"""
Decorators used to validate user permissions to access campaigns.
"""

from functools import wraps
from django.http import HttpResponseNotFound

from apps.campaigns.models import Campaign, CampaignMembership


def members_only(*campaign_id_params):
    """
    Decorator that checks if the user is a member of specified campaigns.

    Usage:
        @members_only('campaign_id')  # Gets campaign_id from URL kwargs
        @members_only('campaign_id', 'other_campaign_id')  # Multiple campaigns

    The decorator will look for campaign IDs in the URL keyword arguments.
    """

    def decorator(view):
        @wraps(view)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseNotFound()

            campaign_ids = []
            for param in campaign_id_params:
                campaign_id = kwargs.get(param)
                if campaign_id is None:
                    return HttpResponseNotFound()

                # Validate that campaign_id is a positive integer
                try:
                    campaign_id = int(campaign_id)
                    if campaign_id <= 0:
                        return HttpResponseNotFound()
                except (ValueError, TypeError):
                    return HttpResponseNotFound()

                campaign_ids.append(campaign_id)

            # Check membership for all campaigns
            for campaign_id in campaign_ids:
                # Check if campaign exists
                try:
                    campaign = Campaign.objects.get(id=campaign_id)
                except Campaign.DoesNotExist:
                    return HttpResponseNotFound()

                # Check if user is a member
                if not CampaignMembership.objects.filter(
                    campaign_id=campaign_id, user=request.user.profile
                ).exists():
                    return HttpResponseNotFound()

            return view(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def gm_members_only(*campaign_id_params):
    """
    Decorator that checks if the user is a GM of specified campaigns.

    Usage:
        @gm_members_only('campaign_id')
        @gm_members_only('campaign_id', 'other_campaign_id')
    """

    def decorator(view):
        @wraps(view)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseNotFound()

            campaign_ids = []
            for param in campaign_id_params:
                campaign_id = kwargs.get(param)
                if campaign_id is None:
                    return HttpResponseNotFound()

                # Validate that campaign_id is a positive integer
                try:
                    campaign_id = int(campaign_id)
                    if campaign_id <= 0:
                        return HttpResponseNotFound()
                except (ValueError, TypeError):
                    return HttpResponseNotFound()

                campaign_ids.append(campaign_id)

            # Check GM membership for all campaigns
            for campaign_id in campaign_ids:
                # Check if campaign exists
                if not Campaign.objects.filter(id=campaign_id).exists():
                    return HttpResponseNotFound()

                # Check if user is a GM
                if not CampaignMembership.objects.filter(
                    campaign_id=campaign_id,
                    user=request.user.profile,
                    role=CampaignMembership.CampaignRoles.GM,
                ).exists():
                    return HttpResponseNotFound()

            return view(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def members_only_pass_campaign_and_membership(*campaign_id_params):
    """
    Same as members_only but passes the campaign and membership objects to the view.

    Usage (single campaign):
        @members_only_pass_campaign_and_membership('campaign_id')
        def view(request, campaign_id, campaign, membership):
            # campaign and membership are already fetched and validated
            # membership.user is request.user.profile
            # membership.campaign is the campaign

    Usage (multiple campaigns):
        @members_only_pass_campaign_and_membership('campaign_id', 'other_id')
        def view(request, campaign_id, other_id, campaigns, memberships):
            # campaigns is a list of Campaign objects
            # memberships is a list of CampaignMembership objects
            # They are in the same order as the URL parameters
    """

    def decorator(view):
        @wraps(view)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseNotFound()

            campaign_ids = []
            for param in campaign_id_params:
                campaign_id = kwargs.get(param)
                if campaign_id is None:
                    return HttpResponseNotFound()

                # Validate that campaign_id is a positive integer
                try:
                    campaign_id = int(campaign_id)
                    if campaign_id <= 0:
                        return HttpResponseNotFound()
                except (ValueError, TypeError):
                    return HttpResponseNotFound()

                campaign_ids.append(campaign_id)

            campaigns = []
            campaign_memberships = []
            for campaign_id in campaign_ids:
                try:
                    campaign = Campaign.objects.get(id=campaign_id)
                except Campaign.DoesNotExist:
                    return HttpResponseNotFound()

                try:
                    campaign_membership = CampaignMembership.objects.get(
                        campaign_id=campaign_id, user=request.user.profile
                    )
                except CampaignMembership.DoesNotExist:
                    return HttpResponseNotFound()

                campaigns.append(campaign)
                campaign_memberships.append(campaign_membership)

            # Pass the campaign(s) to the view
            if len(campaigns) == 1:
                kwargs["campaign"] = campaigns[0]
            else:
                kwargs["campaigns"] = campaigns

            if len(campaign_memberships) == 1:
                kwargs["membership"] = campaign_memberships[0]
            else:
                kwargs["memberships"] = campaign_memberships

            return view(request, *args, **kwargs)

        return _wrapped_view

    return decorator
