from django.http import (
    HttpResponseServerError,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    HttpResponse,
)
from django.shortcuts import render, redirect
import json

from apps.campaigns.decorators import (
    members_only_pass_campaign_and_membership,
    members_only,
)
from apps.campaigns.models import Campaign, CampaignMembership
from apps.personas import services
from apps.personas.forms import CreatePersonaForm, EditPersonaForm
from apps.personas.models import Persona

# Ok the button triggers form to be created at the end of the persona list and itself to be disabled
# This form when successfully submitted returns the created persona and triggers [type]>PersonaCreated
# This events results in the button being un-disabled


# region Create Persona
@members_only("campaign_id")
def cancel_create_persona(request, campaign_id: int, persona_type: str):
    """
    Handles the cancellation of the persona creation process. Supports standard
    HTML redirects for non-HTMX requests and serves appropriate responses for
    GET or invalid HTTP methods. This function is intended for use with
    campaign-related views and requires user authentication via the specified
    decorator.

    :param request: The HTTP request object.
    :type request: HttpRequest
    :param campaign_id: The unique identifier of the campaign.
    :type campaign_id: int

    :return: An HTTP response based on the request type and method.
    """
    # If the request is standard html redirect to the dashboard
    if not request.htmx:
        return redirect("campaigns:campaign-page", id=campaign_id)

    # Handle GET Requests
    if request.method == "GET":
        # Return empty template
        response = render(request, "core/_blank.html")
        response["HX-Trigger"] = f"cancelCreate{ persona_type.capitalize() }Persona"
        # response["HX-Trigger"] = json.dumps(
        #     {"cancelCreateNpcPersona": {"target": "body"}}
        # )
        return response

    # Fallback for other methods
    return HttpResponseBadRequest(
        "Request methods to the cancel create campaign endpoint must be GET."
    )


@members_only_pass_campaign_and_membership("campaign_id")
def create_persona(
    request,
    campaign_id: int,
    persona_type: str,
    campaign: Campaign,
    membership: CampaignMembership,
):
    """
    Creating a new persona via HTMX. Non-HTMX requests are redirected to the campaign page.

    This view handles both GET and POST requests for the persona creation workflow.
    It expects HTMX requests and returns partial HTML responses for HTMX swaps as well as HTMX triggers.

    It renders the form via personas/_create_persona_form.html. Persona creation is delegated to services.create_persona().

    - **GET**: Returns an empty persona creation form.
    - **POST**: Validates the form data.
        - If the form is invalid, return the persona creation form with the errors.
        - If the form is valid and a persona is created successfully, return a the rendered persona as a partial and set the trigger to "{{persona_type}}PersonaCreated".
        - If the form is valid but a campaign is not created successfully, return a sanitized HttpResponseServerError.
            - This case would likely only occur due to non-standard errors, or foul play.

    :param request: HttpRequest
    :param campaign_id: The id of the campaign
    :param persona_type: The type of persona being created, either "character" or "npc
    :param campaign: Populated by @members_only_pass_campaign_and_membership
    :param membership: Populated by @members_only_pass_campaign_and_membership
    :return: The persona creation form partial

    :raises Http400: Bad request, occurs if the method is not GET or POST.
    :raises Http500: Internal server error, occurs if an error is raised in the service layer while creating the persona. It is sanitized to prevent information leakage.

    **Security Notes**:
        - Only accessible to authenticated users via @members_only_pass_campaign_and_membership
        - Service layer exceptions are caught and sanitized to prevent information leakage
        - Non-HTMX requests are redirected to the campaign page
    """

    # If the request is standard html redirect to the dashboard
    if not request.htmx:
        return redirect("campaign-page", campaign_id=campaign_id)

    # Handle GET Requests
    if request.method == "GET":
        # Return empty form
        form = CreatePersonaForm(campaign_membership=membership)
        return render(
            request,
            "personas/_create_persona_form.html",
            {"campaign": campaign, "form": form, "persona_type": persona_type},
        )

    # Handle POST Requests
    if request.method == "POST":
        # Submit form
        form = CreatePersonaForm(request.POST, campaign_membership=membership)

        if not form.is_valid():
            # On invalid input, return the form with the appropriate errors
            return render(
                request,
                "personas/_create_persona_form.html",
                {"campaign": campaign, "persona_type": persona_type, "form": form},
            )

        try:
            # Get Persona Type
            if persona_type.lower() == "character":
                types = Persona.PersonaType.CHARACTER
            elif persona_type.lower() == "npc":
                types = Persona.PersonaType.NPC
            else:
                raise ValueError("Invalid persona type")

            # Create Persona
            persona = services.create_persona(
                creator=membership,
                persona_type=types,
                name=form.cleaned_data["name"],
                description=form.cleaned_data["description"],
            )

            response = render(
                request,
                "personas/_persona.html",
                {"campaign": campaign, "persona": persona, "open": True},
            )
            response["HX-Trigger"] = f"{persona_type.lower()}PersonaCreated"
            # response["HX-Target"] = "body"
            # response["HX-Trigger"] = json.dumps(
            #     {"cancelCreateNpcPersona": {"target": "body"}}
            # )
            return response
        except Exception as e:
            print("Error creating persona: ", e)
            return HttpResponseServerError("Something went wrong! Please try again!")

    # Fallback for other methods
    return HttpResponseBadRequest(
        "Request methods to the create campaign endpoint must be GET or POST"
    )


# endregion


# region Edit Persona
@members_only_pass_campaign_and_membership("campaign_id")
def cancel_edit_persona(
    request,
    campaign_id: int,
    persona_id: int,
    campaign: Campaign,
    membership: CampaignMembership,
):
    """
    Handles the cancellation of the persona edit process. Supports standard
    HTML redirects for non-HTMX requests and serves appropriate responses for
    GET or invalid HTTP methods. This function is intended for use with
    campaign-related views and requires user authentication via the specified
    decorator.

    :param persona_id:
    :param request: The HTTP request object.
    :type request: HttpRequest
    :param campaign_id: The unique identifier of the campaign.
    :type campaign_id: int

    :return: An HTTP response based on the request type and method.
    """
    # If the request is standard html redirect to the dashboard
    if not request.htmx:
        return redirect("campaign-page", id=campaign_id)

    # Get the persona
    try:
        persona = Persona.objects.get(id=persona_id, member=membership)
    except Persona.DoesNotExist:
        return HttpResponseNotFound()

    # Handle GET Requests
    if request.method == "GET":
        # Return the original persona
        response = render(
            request,
            "personas/_persona.html",
            {"campaign": campaign, "persona": persona},
        )
        response["HX-Trigger"] = (
            f"cancelEdit{persona.type.lower()}Persona"  # maybe this should include the persona_type...
        )
        return response

    # Fallback for other methods
    return HttpResponseBadRequest(
        "Request methods to the cancel create campaign endpoint must be GET."
    )


@members_only_pass_campaign_and_membership("campaign_id")
def edit_persona(
    request,
    campaign_id: int,
    persona_id: int,
    campaign: Campaign,
    membership: CampaignMembership,
):
    """
    Edit a persona via HTMX. Non-HTMX requests are redirected to the campaign page.

    This view handles both GET and POST requests for the persona creation workflow.
    It expects HTMX requests and returns partial HTML responses for HTMX swaps as well as HTMX triggers.

    It renders the form via personas/_create_persona_form.html. Persona creation is delegated to services.create_persona().

    - **GET**: Returns an empty persona creation form.
    - **POST**: Validates the form data.
        - If the form is invalid, return the persona creation form with the errors.
        - If the form is valid and a persona is created successfully, return a the rendered persona as a partial and set the trigger to "{{persona_type}}PersonaCreated".
        - If the form is valid but a campaign is not created successfully, return a sanitized HttpResponseServerError.
            - This case would likely only occur due to non-standard errors, or foul play.

    :param persona_id:
    :param request: HttpRequest
    :param campaign_id: The id of the campaign
    :param persona_type: The type of persona being created, either "character" or "npc
    :param campaign: Populated by @members_only_pass_campaign_and_membership
    :param membership: Populated by @members_only_pass_campaign_and_membership
    :return: The persona creation form partial

    :raises Http400: Bad request, occurs if the method is not GET or POST.
    :raises Http500: Internal server error, occurs if an error is raised in the service layer while creating the persona. It is sanitized to prevent information leakage.

    **Security Notes**:
        - Only accessible to authenticated users via @members_only_pass_campaign_and_membership
        - Service layer exceptions are caught and sanitized to prevent information leakage
        - Non-HTMX requests are redirected to the campaign page
    """

    print(f"DEBUG: id = {campaign_id}")  # ← Add this
    print(f"DEBUG: persona_id = {persona_id}")
    print(f"DEBUG: campaign.id = {campaign.id}")

    # If the request is standard html redirect to the dashboard
    if not request.htmx:
        return redirect("campaign-page", id=campaign_id)

    # Fallback for other methods
    if not request.method == "GET" and not request.method == "POST":
        return HttpResponseBadRequest(
            "Request methods to the edit campaign endpoint must be GET or POST"
        )

    # Get the persona
    try:
        persona = Persona.objects.get(id=persona_id)
    except Persona.DoesNotExist:
        return HttpResponseNotFound()

    # If the persona is not owned by the user, return a HttpResponseNotFound
    if persona.member != membership:
        return HttpResponseNotFound()

    # Handle GET Requests
    if request.method == "GET":
        # Return empty form
        form = EditPersonaForm(
            initial={
                "name": persona.name,
                "description": persona.description,
            }
        )

        return render(
            request,
            "personas/_edit_persona_form.html",
            {"campaign": campaign, "form": form, "persona": persona},
        )

    # Handle POST Requests
    if request.method == "POST":
        # Submit form
        form = EditPersonaForm(request.POST)

        if not form.is_valid():
            # On invalid input, return the form with the appropriate errors
            return render(
                request,
                "personas/_edit_persona_form.html",
                {"campaign": campaign, "form": form, "persona": persona},
            )

        try:
            # Edit Persona
            persona = services.edit_persona_details(
                editor=membership,
                persona=persona,
                name=form.cleaned_data["name"],
                description=form.cleaned_data["description"],
            )

            response = render(
                request,
                "personas/_persona.html",
                {"campaign": campaign, "persona": persona},
            )
            response["HX-Trigger"] = f"{persona.type.lower()}PersonaEdited"
            return response
        except Exception as e:
            print("Error editing persona: ", e)
            return HttpResponseServerError("Something went wrong! Please try again!")


# endregion

# region Retire Persona


@members_only_pass_campaign_and_membership("campaign_id")
def retire_persona(request, campaign_id: int, persona_id: int, campaign, membership):
    """
    Handles the retirement of a persona associated with a specific campaign. The function is restricted
    to the DELETE request methods and is decorated to ensure membership and campaign access is
    granted before execution. For valid DELETE requests, it searches for the persona linked to the
    current campaign and membership and attempts to retire it. On success, it triggers an HX action
    response. Handles key error scenarios for persona retrieval and retirement.

    :param request: The HTTP request object used to manage the request/response cycle.
    :param campaign_id: The unique identifier for the campaign the persona belongs to.
    :param persona_id: The unique identifier for the persona to be retired.
    :param campaign: The campaign instance tied to the operation.
    :param membership: The membership instance of the current user for the campaign.
    :return: A response object appropriate to the success or failure of the operation.
    """
    if not request.htmx:
        return redirect("campaign-page", campaign=campaign)

    if request.method == "DELETE":
        try:
            persona = Persona.objects.get(id=persona_id, member=membership)
        except Persona.DoesNotExist:
            return HttpResponseNotFound()

        try:
            if membership.role == CampaignMembership.CampaignRoles.GM:
                # Set the status to retired, but don't transfer it to another GM
                persona.status = Persona.PersonaStatus.RETIRED
                persona.save()
            else:
                # Transfer the persona to the first GM of the campaign
                entrustee_membership = CampaignMembership.objects.filter(
                    campaign=campaign, role=CampaignMembership.CampaignRoles.GM
                ).earliest("created_at")
                services.retire_persona(
                    owner=membership, persona=persona, entrustee=entrustee_membership
                )
        except Exception as e:
            print("Error retiring persona: ", e)
            return HttpResponseServerError("Something went wrong! Please try again!")

        response = render(request, "core/_blank.html")
        response["HX-Trigger"] = f"retire{persona.type.lower()}Persona"
        return response

    # Fallback for other methods
    return HttpResponseBadRequest(
        "Request methods to the retire persona endpoint must be DELETE."
    )


# endregion


@members_only_pass_campaign_and_membership("campaign_id")
def persona_list(
    request,
    campaign_id: int,
    persona_type: str,
    persona_status: str,
    campaign: Campaign,
    membership: CampaignMembership,
):
    """
    Handles requests to retrieve and display a list of personas associated with a specific
    campaign and persona type. The response adapts based on whether the request is a standard
    HTML request or an HTMX request. Only GET requests are supported for this endpoint, while
    other HTTP methods result in a 400 Bad Request response.

    :param persona_status: The status of the persona to filter by. Acceptable values are "active" or "retired". Case-insensitive.
    :param request: The HTTP request object, containing metadata about the request made by
        the client.
    :param campaign_id: The ID of the campaign to which the request is associated.
    :param persona_type: The type of persona to retrieve. Acceptable values are "character"
        or "npc". Case-insensitive.
    :param campaign: The campaign instance corresponding to the specified campaign ID.
    :param membership: The membership instance that validates user association with the campaign.
    :return: An HTTP response containing the persona list rendered as HTML in the case of GET
        requests. For non-GET requests, it returns a 400 Bad Request response. In case of server
        errors during GET processing, a 500 Internal Server Error response is returned.
    """
    # If the request is standard html redirect to the campaign page
    if not request.htmx:
        return redirect("campaign-page", id=campaign_id)

    # Handle GET Requests
    if request.method == "GET":
        # Return the list
        try:
            # Get Persona Type
            if persona_type.lower() == "character":
                type = Persona.PersonaType.CHARACTER
            elif persona_type.lower() == "npc":
                type = Persona.PersonaType.NPC
            elif persona_type.lower() == "member":
                type = "member"
            else:
                raise ValueError("Invalid persona type")

            # Get Persona Status
            if persona_status.lower() == "active":
                status = Persona.PersonaStatus.ACTIVE
            elif persona_status.lower() == "retired":
                status = Persona.PersonaStatus.RETIRED
            else:
                raise ValueError("Invalid persona status")

            if type == "member":
                personas = Persona.objects.filter(
                    member=membership, type__in=["gm", "player"], status=status
                ).order_by("-created_at")
            else:
                personas = Persona.objects.filter(
                    member=membership, type=type, status=status
                ).order_by("-created_at")

            return render(
                request,
                "personas/_persona_list.html",
                {
                    "campaign": campaign,
                    "persona_type": persona_type,
                    "persona_status": persona_status,
                    "personas": personas,
                },
            )
        except Exception as e:
            print("Error creating persona: ", e)
            return HttpResponseServerError("Something went wrong! Please try again!")

    # Fallback for other methods
    return HttpResponseBadRequest(
        "Request methods to the persona list endpoint must be GET."
    )


@members_only_pass_campaign_and_membership("campaign_id")
def personas_page_content(
    request,
    campaign_id: int,
    campaign: Campaign,
    membership: CampaignMembership,
):
    # If the request is standard html redirect to the campaign page
    if not request.htmx:
        return redirect("campaign-page", id=campaign_id)

    if request.method == "GET":
        return render(
            request,
            "personas/_personas_page_content.html",
            {"campaign": campaign, "membership": membership},
        )

    # Fallback for other methods
    return HttpResponseBadRequest(
        "Request methods to the personas page content endpoint must be GET."
    )


@members_only_pass_campaign_and_membership("campaign_id")
def personas_page(
    request,
    campaign_id: int,
    campaign: Campaign,
    membership: CampaignMembership,
):
    """
    Returns the personas page HTML page. The personas page acts shows the list of personas that the player has access to..

    This view handles only GET requests. It expects HTML requests and returns full HTML pages that inherit from 'base.html'.

        It renders the page via "personas/personas-page.html" template.

        - **GET**: Returns the campaign page HTML page

        :param request: HttpRequest
        :param campaign_id: The id of the campaign
        :param membership: Populated by @members_only_pass_campaign_and_membership
        :param campaign: Populated by @members_only_pass_campaign_and_membership
        :return: The campaign HTML page

        :raises Http400: Bad request, occurs if the method is not GET request, or it is a HTMX request.
        :raises Http404: Not found, occurs if the campaign does not exist or the user doesn't have permission to access it.

        **Security Notes**:
            - Http404 is raised by @members_only decorator
            - Http404 is given in cases where the user doesn't have permission to access a campaign and when the campaign doesn't exist to prevent information leakage.
    """

    if request.htmx:
        return HttpResponseBadRequest(
            "Requests to the campaign-page endpoint must not be HTMX requests."
        )

    if request.method != "GET":
        return HttpResponseBadRequest(
            "Requests to the campaign-page endpoint must be GET requests."
        )

    return render(
        request,
        "personas/personas_page.html",
        {"campaign": campaign, "campaign_id": campaign.id},
    )
