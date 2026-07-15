# tests/test_decorators.py
import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.http import HttpResponse, HttpResponseNotFound
from django.db import connection
from django.test.utils import CaptureQueriesContext
from unittest.mock import Mock, patch

from apps.accounts.models import UserProfile
from apps.campaigns.models import Campaign, CampaignMembership
from apps.campaigns.decorators import (
    members_only,
    gm_members_only,
    members_only_pass_campaign_and_membership,
)

# ============= FIXTURES =============


@pytest.fixture
def factory():
    """RequestFactory fixture for creating mock requests."""
    return RequestFactory()


@pytest.fixture
def user(db):
    """Create a regular user."""
    user = User.objects.create_user(username="testuser", password="testpass123")
    return user


@pytest.fixture
def other_user(db):
    """Create another user for testing non-members."""
    user = User.objects.create_user(username="otheruser", password="testpass123")
    return user


@pytest.fixture
def profile(user):
    """Create a user profile."""
    return UserProfile.objects.create(user=user, display_name="Test User")


@pytest.fixture
def other_profile(other_user):
    """Create another user profile."""
    return UserProfile.objects.create(user=other_user, display_name="Other User")


@pytest.fixture
def campaign1(db):
    """Create a test campaign."""
    return Campaign.objects.create(title="Campaign 1", description="Test campaign 1")


@pytest.fixture
def campaign2(db):
    """Create another test campaign."""
    return Campaign.objects.create(title="Campaign 2", description="Test campaign 2")


@pytest.fixture
def membership1(profile, campaign1):
    """Create a player membership."""
    return CampaignMembership.objects.create(
        user=profile, campaign=campaign1, role=CampaignMembership.CampaignRoles.PLAYER
    )


@pytest.fixture
def membership2(profile, campaign2):
    """Create a GM membership."""
    return CampaignMembership.objects.create(
        user=profile, campaign=campaign2, role=CampaignMembership.CampaignRoles.GM
    )


@pytest.fixture
def authenticated_request(factory, user, profile):
    """Create an authenticated request with a user that has a profile."""

    def _create_request(path="/", **extra):
        request = factory.get(path, **extra)
        request.user = user
        request.user.profile = profile
        return request

    return _create_request


@pytest.fixture
def other_authenticated_request(factory, other_user, other_profile):
    """Create an authenticated request for other_user with a profile."""

    def _create_request(path="/", **extra):
        request = factory.get(path, **extra)
        request.user = other_user
        request.user.profile = other_profile
        return request

    return _create_request


@pytest.fixture
def view_func():
    """A simple view function to decorate."""

    def test_view(request, *args, **kwargs):
        return HttpResponse("Success")

    return test_view


# ============= TESTS FOR members_only DECORATOR =============


@pytest.mark.django_db
class TestMembersOnlyDecorator:
    """Tests for the members_only decorator."""

    def test_allows_authenticated_member(
        self, authenticated_request, view_func, campaign1, membership1
    ):
        """Should allow access when user is a member."""
        request = authenticated_request("/campaign/1/")
        decorated_view = members_only("campaign_id")(view_func)

        response = decorated_view(request, campaign_id=campaign1.id)

        assert response.status_code == 200
        assert response.content == b"Success"

    def test_blocks_authenticated_non_member(
        self, other_authenticated_request, view_func, campaign1, other_profile
    ):  # ✅ Added other_profile to explicitly load it
        """Should return 404 when user is not a member."""
        request = other_authenticated_request("/campaign/1/")
        decorated_view = members_only("campaign_id")(view_func)
        response = decorated_view(request, campaign_id=campaign1.id)

        assert response.status_code == 404
        assert isinstance(response, HttpResponseNotFound)

    def test_blocks_unauthenticated_user(self, factory, view_func, campaign1):
        """Should return 404 when user is not authenticated."""
        request = factory.get("/campaign/1/")
        request.user = Mock(is_authenticated=False)

        decorated_view = members_only("campaign_id")(view_func)
        response = decorated_view(request, campaign_id=campaign1.id)

        assert response.status_code == 404

    def test_blocks_non_existent_campaign(self, authenticated_request, view_func):
        """Should return 404 when campaign doesn't exist."""
        request = authenticated_request("/campaign/999/")
        decorated_view = members_only("campaign_id")(view_func)
        response = decorated_view(request, campaign_id=999)

        assert response.status_code == 404

    def test_blocks_missing_campaign_id_param(self, authenticated_request, view_func):
        """Should return 404 when campaign_id param is missing."""
        request = authenticated_request("/campaign/")
        decorated_view = members_only("campaign_id")(view_func)
        response = decorated_view(request)  # No campaign_id

        assert response.status_code == 404

    def test_allows_multiple_campaigns(
        self,
        authenticated_request,
        view_func,
        campaign1,
        campaign2,
        membership1,
        membership2,
    ):  # ✅ Added membership1 and membership2
        """Should allow access when user is member of all campaigns."""
        request = authenticated_request("/compare/1/2/")
        decorated_view = members_only("campaign_id", "other_id")(view_func)
        response = decorated_view(
            request, campaign_id=campaign1.id, other_id=campaign2.id
        )

        assert response.status_code == 200

    def test_blocks_multiple_campaigns_not_member_all(
        self,
        other_authenticated_request,
        view_func,
        campaign1,
        campaign2,
        other_profile,
    ):  # ✅ Added other_profile
        """Should return 404 when user is not member of all campaigns."""
        request = other_authenticated_request("/compare/1/2/")
        decorated_view = members_only("campaign_id", "other_id")(view_func)
        response = decorated_view(
            request, campaign_id=campaign1.id, other_id=campaign2.id
        )

        assert response.status_code == 404

    def test_allows_with_custom_param_name(
        self, authenticated_request, view_func, campaign1, membership1
    ):
        """Should work with custom parameter names."""
        decorated_view = members_only("pk")(view_func)
        request = authenticated_request("/campaign/1/")
        response = decorated_view(request, pk=campaign1.id)

        assert response.status_code == 200

    def test_decorator_with_no_params(self, authenticated_request, view_func):
        """Should handle being called with no campaign ID params."""
        decorated_view = members_only()(view_func)
        request = authenticated_request("/campaign/")
        response = decorated_view(request)

        assert response.status_code == 200


# ============= TESTS FOR gm_members_only DECORATOR =============


@pytest.mark.django_db
class TestGMMembersOnlyDecorator:
    """Tests for the gm_members_only decorator."""

    def test_allows_gm_member(
        self, authenticated_request, view_func, campaign2, membership2
    ):
        """Should allow access when user is a GM."""
        request = authenticated_request("/campaign/2/settings/")
        decorated_view = gm_members_only("campaign_id")(view_func)
        response = decorated_view(request, campaign_id=campaign2.id)

        assert response.status_code == 200

    def test_blocks_player_member(
        self, authenticated_request, view_func, campaign1, membership1
    ):
        """Should return 404 when user is a player but not GM."""
        request = authenticated_request("/campaign/1/settings/")
        decorated_view = gm_members_only("campaign_id")(view_func)
        response = decorated_view(request, campaign_id=campaign1.id)

        assert response.status_code == 404

    def test_blocks_non_member(
        self, other_authenticated_request, view_func, campaign1, other_profile
    ):  # ✅ Added other_profile
        """Should return 404 when user is not a member at all."""
        request = other_authenticated_request("/campaign/1/settings/")
        decorated_view = gm_members_only("campaign_id")(view_func)
        response = decorated_view(request, campaign_id=campaign1.id)

        assert response.status_code == 404

    def test_blocks_unauthenticated_user(self, factory, view_func, campaign1):
        """Should return 404 when user is not authenticated."""
        request = factory.get("/campaign/1/settings/")
        request.user = Mock(is_authenticated=False)

        decorated_view = gm_members_only("campaign_id")(view_func)
        response = decorated_view(request, campaign_id=campaign1.id)

        assert response.status_code == 404

    def test_allows_multiple_gm_campaigns(
        self,
        authenticated_request,
        view_func,
        campaign1,
        campaign2,
        profile,
        membership2,
    ):
        """Should allow access when user is GM of all campaigns."""
        # Make user GM of campaign1 too
        CampaignMembership.objects.create(
            user=profile, campaign=campaign1, role=CampaignMembership.CampaignRoles.GM
        )

        request = authenticated_request("/compare/1/2/")
        decorated_view = gm_members_only("campaign_id", "other_id")(view_func)
        response = decorated_view(
            request, campaign_id=campaign1.id, other_id=campaign2.id
        )

        assert response.status_code == 200

    def test_blocks_when_not_gm_of_all_campaigns(
        self, authenticated_request, view_func, campaign1, campaign2
    ):
        """Should return 404 when user is not GM of all campaigns."""
        request = authenticated_request("/compare/1/2/")
        decorated_view = gm_members_only("campaign_id", "other_id")(view_func)
        response = decorated_view(
            request,
            campaign_id=campaign1.id,  # User is PLAYER here
            other_id=campaign2.id,  # User is GM here
        )

        assert response.status_code == 404


# ============= PARAMETERIZED TESTS =============


@pytest.mark.django_db
class TestParametrizedDecorators:
    """Parameterized tests for decorators."""

    @pytest.mark.parametrize(
        "is_member,expected_status",
        [
            (True, 200),
            (False, 404),
        ],
    )
    def test_membership_access(
        self,
        authenticated_request,
        other_authenticated_request,
        view_func,
        campaign1,
        profile,
        membership1,
        other_profile,
        is_member,
        expected_status,
    ):  # ✅ Added profile and other_profile
        """Test both member and non-member cases parametrized."""
        if is_member:
            request = authenticated_request("/campaign/1/")
        else:
            request = other_authenticated_request("/campaign/1/")

        decorated_view = members_only("campaign_id")(view_func)
        response = decorated_view(request, campaign_id=campaign1.id)

        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "campaign_exists,is_member,expected_status",
        [
            (True, True, 200),
            (True, False, 404),
            (False, True, 404),
            (False, False, 404),
        ],
    )
    def test_various_scenarios(
        self,
        authenticated_request,
        other_authenticated_request,
        view_func,
        campaign1,
        profile,
        membership1,
        other_profile,
        campaign_exists,
        is_member,
        expected_status,
    ):  # ✅ Added profile and other_profile
        """Test all combinations of campaign existence and membership."""
        if is_member:
            request = authenticated_request("/campaign/1/")
        else:
            request = other_authenticated_request("/campaign/1/")

        campaign_id = campaign1.id if campaign_exists else 999

        decorated_view = members_only("campaign_id")(view_func)
        response = decorated_view(request, campaign_id=campaign_id)

        assert response.status_code == expected_status


# ============= DATABASE QUERY COUNT TESTS =============


@pytest.mark.django_db
class TestQueryCounts:
    """Tests to ensure decorators use minimal database queries."""

    def test_members_only_minimal_queries(
        self, authenticated_request, view_func, campaign1, membership1
    ):
        """Should use minimal database queries (2)."""
        request = authenticated_request("/campaign/1/")
        decorated_view = members_only("campaign_id")(view_func)

        with CaptureQueriesContext(connection) as queries:
            response = decorated_view(request, campaign_id=campaign1.id)

        assert response.status_code == 200
        assert len(queries) <= 2  # Campaign query + Membership query

    def test_pass_campaign_and_membership_minimal_queries(
        self, authenticated_request, campaign1, membership1
    ):
        """Should use minimal queries when passing objects."""

        def view_with_params(request, campaign_id, campaign, membership):
            return HttpResponse("Success")

        request = authenticated_request("/campaign/1/")
        decorated_view = members_only_pass_campaign_and_membership("campaign_id")(
            view_with_params
        )

        with CaptureQueriesContext(connection) as queries:
            response = decorated_view(request, campaign_id=campaign1.id)

        assert response.status_code == 200
        assert len(queries) <= 2  # Campaign query + Membership query

    def test_multiple_campaigns_query_count(
        self,
        authenticated_request,
        view_func,
        campaign1,
        campaign2,
        membership1,
        membership2,
    ):
        """Should use 4 queries for 2 campaigns (2 campaigns + 2 memberships)."""
        request = authenticated_request("/compare/1/2/")
        decorated_view = members_only("campaign_id", "other_id")(view_func)

        with CaptureQueriesContext(connection) as queries:
            response = decorated_view(
                request, campaign_id=campaign1.id, other_id=campaign2.id
            )

        assert response.status_code == 200
        assert len(queries) <= 4  # 2 campaigns + 2 memberships


# ============= HTMX TESTS =============


@pytest.mark.django_db
class TestHTMXDecorators:
    """Tests for HTMX-specific behavior."""

    def test_htmx_request_returns_404_with_htmx_header(
        self, other_authenticated_request, view_func, campaign1, membership1
    ):
        """Should return 404 with HTMX header for consistency."""
        request = other_authenticated_request("/campaign/1/", HTTP_HX_REQUEST="true")

        decorated_view = members_only("campaign_id")(view_func)
        response = decorated_view(request, campaign_id=campaign1.id)

        assert response.status_code == 404
        assert isinstance(response, HttpResponseNotFound)

    def test_htmx_request_for_non_existent_campaign(
        self, authenticated_request, view_func, profile
    ):
        """Should return 404 with HTMX header for non-existent campaign."""
        request = authenticated_request("/campaign/999/", HTTP_HX_REQUEST="true")

        decorated_view = members_only("campaign_id")(view_func)
        response = decorated_view(request, campaign_id=999)

        assert response.status_code == 404
        assert isinstance(response, HttpResponseNotFound)

    def test_htmx_request_allows_member(
        self, authenticated_request, view_func, campaign1, membership1
    ):
        """Should allow HTMX request when user is a member."""
        request = authenticated_request("/campaign/1/", HTTP_HX_REQUEST="true")

        decorated_view = members_only("campaign_id")(view_func)
        response = decorated_view(request, campaign_id=campaign1.id)

        assert response.status_code == 200
        assert response.content == b"Success"


# ============= EDGE CASE TESTS =============


@pytest.mark.django_db
class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_decorator_with_duplicate_params(
        self, authenticated_request, view_func, campaign1, membership1
    ):
        """Should handle duplicate campaign ID parameters."""
        request = authenticated_request("/campaign/1/")
        decorated_view = members_only("campaign_id", "campaign_id")(view_func)
        response = decorated_view(request, campaign_id=campaign1.id)

        assert response.status_code == 200

    def test_decorator_with_none_campaign_id(self, authenticated_request, view_func):
        """Should handle None campaign ID."""
        request = authenticated_request("/campaign/")
        decorated_view = members_only("campaign_id")(view_func)
        response = decorated_view(request, campaign_id=None)

        assert response.status_code == 404

    def test_decorator_with_empty_string_campaign_id(
        self, authenticated_request, view_func
    ):
        """Should handle empty string campaign ID."""
        request = authenticated_request("/campaign/")
        decorated_view = members_only("campaign_id")(view_func)
        response = decorated_view(request, campaign_id="")

        assert response.status_code == 404

    def test_decorator_with_invalid_campaign_id(self, authenticated_request, view_func):
        """Should handle non-numeric campaign ID."""
        request = authenticated_request("/campaign/abc/")
        decorated_view = members_only("campaign_id")(view_func)
        response = decorated_view(request, campaign_id="abc")

        assert response.status_code == 404

    def test_decorator_with_negative_campaign_id(
        self, authenticated_request, view_func
    ):
        """Should handle negative campaign ID."""
        request = authenticated_request("/campaign/-1/")
        decorated_view = members_only("campaign_id")(view_func)
        response = decorated_view(request, campaign_id=-1)

        assert response.status_code == 404

    def test_decorator_with_zero_campaign_id(self, authenticated_request, view_func):
        """Should handle zero campaign ID."""
        request = authenticated_request("/campaign/0/")
        decorated_view = members_only("campaign_id")(view_func)
        response = decorated_view(request, campaign_id=0)

        assert response.status_code == 404

    def test_decorator_preserves_function_metadata(self, view_func):
        """Should preserve the original function's metadata."""
        decorated_view = members_only("campaign_id")(view_func)

        assert decorated_view.__name__ == view_func.__name__
        assert decorated_view.__module__ == view_func.__module__

    def test_decorator_works_with_class_based_views(
        self, authenticated_request, campaign1, membership1
    ):
        """Should work with class-based views when applied with method_decorator."""
        from django.views.generic import TemplateView
        from django.utils.decorators import method_decorator

        @method_decorator(members_only("campaign_id"), name="dispatch")
        class TestView(TemplateView):
            template_name = "test.html"

        request = authenticated_request("/campaign/1/")
        view = TestView.as_view()
        response = view(request, campaign_id=campaign1.id)

        assert response.status_code == 200
