"""
Tests for campaign service layer.
"""

import pytest

from apps.accounts.models import UserProfile
from apps.campaigns.models import Campaign, CampaignMembership
from apps.campaigns import services
from apps.campaigns.exceptions import (
    UserCampaignMembershipLimitReachedError,
    UserNotMemberError,
    UserNotSoleGMError,
    LastGMCannotLeaveError,
    CampaignMembershipFullError,
    UserAlreadyMemberError,
    UserAlreadyGMError,
    UserAlreadyPlayerError,
    CampaignTitleIsInvalidError,
    CampaignDescriptionIsInvalidError,
)
from blue_booking_app.settings import USER_CAMPAIGN_LIMIT, CAMPAIGN_MEMBER_LIMIT

# --- Fixtures ---


# campaigns/tests/conftest.py or test_services.py

import pytest
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile
from apps.campaigns.models import Campaign, CampaignMembership


@pytest.fixture
def user_profile(db) -> UserProfile:
    """Create a test user profile with a Django user."""
    user = User.objects.create_user(
        username="testuser", email="test@example.com", password="password123"
    )
    return UserProfile.objects.create(user=user, display_name="Test User")


@pytest.fixture
def another_user(db) -> UserProfile:
    """Create another test user profile with a Django user."""
    user = User.objects.create_user(
        username="anotheruser", email="another@example.com", password="password123"
    )
    return UserProfile.objects.create(user=user, display_name="Another User")


@pytest.fixture
def campaign(db, user_profile) -> Campaign:
    """Create a test campaign with an owner/GM."""
    campaign = Campaign.objects.create(
        title="Test Campaign", description="A test campaign for unit testing"
    )
    CampaignMembership.objects.create(
        user=user_profile, campaign=campaign, role=CampaignMembership.CampaignRoles.GM
    )
    return campaign


@pytest.fixture
def full_campaign(db) -> Campaign:
    """Create a campaign that's at maximum capacity."""
    campaign = Campaign.objects.create(
        title="Full Campaign", description="This campaign is full"
    )

    # Add members up to the limit
    for i in range(CAMPAIGN_MEMBER_LIMIT):
        user = User.objects.create_user(
            username=f"member{i}",
            email=f"member{i}@example.com",
            password="password123",
        )
        profile = UserProfile.objects.create(user=user, display_name=f"Member {i}")
        CampaignMembership.objects.create(
            user=profile,
            campaign=campaign,
            role=CampaignMembership.CampaignRoles.PLAYER,
        )

    return campaign


@pytest.fixture
def user_at_limit(db) -> UserProfile:
    """Create a user at their campaign membership limit."""
    user = User.objects.create_user(
        username="limiteduser", email="limited@example.com", password="password123"
    )
    profile = UserProfile.objects.create(user=user, display_name="Limited User")

    # Create campaigns up to the limit
    for i in range(USER_CAMPAIGN_LIMIT):
        campaign = Campaign.objects.create(
            title=f"Campaign {i}", description=f"Test campaign {i}"
        )
        CampaignMembership.objects.create(
            user=profile,
            campaign=campaign,
            role=CampaignMembership.CampaignRoles.PLAYER,
        )

    return profile


# --- Tests for Helper Functions ---


class TestHasReachedCampaignLimit:
    """Tests for has_reached_campaign_limit function."""

    def test_user_below_limit(self, user_profile):
        """User with no campaigns should not have reached limit."""
        assert services.has_reached_campaign_limit(user_profile) is False

    def test_user_at_limit(self, user_at_limit):
        """User at limit should return True."""
        assert services.has_reached_campaign_limit(user_at_limit) is True

    def test_user_above_limit(self, user_profile):
        """User above limit should return True."""
        # Add more campaigns than the limit
        for i in range(USER_CAMPAIGN_LIMIT + 1):
            campaign = Campaign.objects.create(
                title=f"Campaign {i}", description=f"Test campaign {i}"
            )
            CampaignMembership.objects.create(
                user=user_profile,
                campaign=campaign,
                role=CampaignMembership.CampaignRoles.PLAYER,
            )

        assert services.has_reached_campaign_limit(user_profile) is True


class TestIsCampaignMembershipFull:
    """Tests for is_campaign_membership_full function."""

    def test_campaign_empty(self, campaign):
        """Campaign with no members should not be full."""
        assert services.is_campaign_membership_full(campaign) is False

    def test_campaign_at_limit(self, full_campaign):
        """Campaign at limit should return True."""
        assert services.is_campaign_membership_full(full_campaign) is True


# --- Tests for Core Service Functions ---


class TestCreateCampaign:
    """Tests for create_campaign function."""

    def test_create_campaign_success(self, user_profile):
        """Successfully create a campaign with a GM."""
        campaign = services.create_campaign(
            creator=user_profile, title="My Campaign", description="A great adventure"
        )

        assert campaign.title == "My Campaign"
        assert campaign.description == "A great adventure"
        assert campaign.id is not None

        # Check that creator is the GM
        membership = CampaignMembership.objects.get(
            user=user_profile, campaign=campaign
        )
        assert membership.role == CampaignMembership.CampaignRoles.GM

    def test_create_campaign_title_too_long(self, user_profile):
        """Raise error when title exceeds 100 characters."""
        long_title = "A" * 101

        with pytest.raises(CampaignTitleIsInvalidError) as exc_info:
            services.create_campaign(
                creator=user_profile, title=long_title, description="Valid description"
            )

        assert "Title must be less than 100 characters" in str(exc_info.value)

    def test_create_campaign_description_too_long(self, user_profile):
        """Raise error when description exceeds 500 characters."""
        long_description = "A" * 501

        with pytest.raises(CampaignDescriptionIsInvalidError) as exc_info:
            services.create_campaign(
                creator=user_profile, title="Valid Title", description=long_description
            )

        assert "Description must be less than 500 characters" in str(exc_info.value)

    def test_create_campaign_user_at_limit(self, user_at_limit):
        """Raise error when creator has reached campaign limit."""
        with pytest.raises(UserCampaignMembershipLimitReachedError):
            services.create_campaign(
                creator=user_at_limit,
                title="New Campaign",
                description="This should fail",
            )

    def test_create_campaign_at_exact_limits(self, user_profile):
        """Test edge cases: exactly 100 characters for title, 500 for description."""
        title = "A" * 100
        description = "A" * 500

        campaign = services.create_campaign(
            creator=user_profile, title=title, description=description
        )

        assert campaign.title == title
        assert campaign.description == description


class TestDeleteCampaign:
    """Tests for delete_campaign function."""

    def test_delete_campaign_success(self, user_profile, campaign):
        """Successfully delete a campaign when user is sole GM."""
        campaign_id = campaign.id

        services.delete_campaign(deleter=user_profile, campaign=campaign)

        assert not Campaign.objects.filter(id=campaign_id).exists()
        assert not CampaignMembership.objects.filter(campaign_id=campaign_id).exists()

    def test_delete_campaign_not_member(self, another_user, campaign):
        """Raise error when deleter is not a member."""
        with pytest.raises(UserNotMemberError):
            services.delete_campaign(deleter=another_user, campaign=campaign)

    def test_delete_campaign_not_sole_gm(self, user_profile, another_user, campaign):
        """Raise error when deleter is not the sole GM."""
        # Add another GM
        CampaignMembership.objects.create(
            user=another_user,
            campaign=campaign,
            role=CampaignMembership.CampaignRoles.GM,
        )

        with pytest.raises(UserNotSoleGMError) as exc_info:
            services.delete_campaign(deleter=user_profile, campaign=campaign)

        assert "must be the only GM" in str(exc_info.value)

    def test_delete_campaign_with_players(self, user_profile, campaign):
        """Delete campaign even with players present (sole GM can delete)."""
        # Add a player
        user = User.objects.create_user(
            username="holding_on_user",
            email="nostalgia@example.com",
            password="password123",
        )

        player = UserProfile.objects.create(user=user, display_name="Player")
        CampaignMembership.objects.create(
            user=player, campaign=campaign, role=CampaignMembership.CampaignRoles.PLAYER
        )

        services.delete_campaign(deleter=user_profile, campaign=campaign)

        assert not Campaign.objects.filter(id=campaign.id).exists()


class TestJoinCampaign:
    """Tests for join_campaign function."""

    def test_join_campaign_success(self, user_profile, another_user, campaign):
        """Successfully join a campaign as a PLAYER."""
        # Use another_user, not user_profile (who is already the GM)
        membership = services.join_campaign(user=another_user, campaign=campaign)

        assert membership.user == another_user
        assert membership.campaign == campaign
        assert membership.role == CampaignMembership.CampaignRoles.PLAYER

        # Verify membership exists in database
        assert CampaignMembership.objects.filter(
            user=another_user, campaign=campaign
        ).exists()

    def test_join_campaign_already_member(self, user_profile, campaign):
        """Raise error when user is already a member."""
        # User is already the GM from fixture
        with pytest.raises(UserAlreadyMemberError):
            services.join_campaign(user=user_profile, campaign=campaign)

    def test_join_campaign_full(self, full_campaign, user_profile):
        """Raise error when campaign is full."""
        with pytest.raises(CampaignMembershipFullError):
            services.join_campaign(user=user_profile, campaign=full_campaign)

    def test_join_campaign_user_at_limit(self, user_at_limit, campaign):
        """Raise error when user has reached campaign limit."""
        # Create a new campaign (user_at_limit is already in USER_CAMPAIGN_LIMIT campaigns)
        new_campaign = Campaign.objects.create(
            title="New Campaign", description="This should be inaccessible"
        )

        with pytest.raises(UserCampaignMembershipLimitReachedError):
            services.join_campaign(user=user_at_limit, campaign=new_campaign)


class TestLeaveCampaign:
    def test_leave_campaign_success(self, user_profile, campaign):
        """Successfully leave a campaign when not the last GM."""
        # Add another GM
        user = User.objects.create_user(
            username="other_gm_user",
            email="other_gm@example.com",
            password="password123",
        )
        other_gm = UserProfile.objects.create(user=user, display_name="Other GM")
        CampaignMembership.objects.create(
            user=other_gm, campaign=campaign, role=CampaignMembership.CampaignRoles.GM
        )

        services.leave_campaign(member=user_profile, campaign=campaign)

        assert not CampaignMembership.objects.filter(
            user=user_profile, campaign=campaign
        ).exists()
        assert Campaign.objects.filter(id=campaign.id).exists()  # Campaign still exists

    def test_leave_campaign_not_member(self, another_user, campaign):
        """Raise error when user is not a member."""
        with pytest.raises(UserNotMemberError):
            services.leave_campaign(member=another_user, campaign=campaign)

    def test_leave_campaign_last_gm_with_players_raises_error(
        self, user_profile, campaign
    ):
        """
        Raise error when user is the last GM but there are other members (players).
        """
        # Add a player (not a GM)
        user = User.objects.create_user(
            username="player_user",
            email="player@example.com",
            password="password123",
        )
        player = UserProfile.objects.create(user=user, display_name="Player")
        CampaignMembership.objects.create(
            user=player, campaign=campaign, role=CampaignMembership.CampaignRoles.PLAYER
        )

        # user_profile is the last GM and there are other members
        with pytest.raises(LastGMCannotLeaveError):
            services.leave_campaign(member=user_profile, campaign=campaign)

    def test_leave_campaign_last_gm_and_only_member_deletes_campaign(
        self, user_profile, campaign
    ):
        """
        Campaign is deleted when the last GM and only member leaves.
        """
        campaign_id = campaign.id  # Store ID before deletion

        services.leave_campaign(member=user_profile, campaign=campaign)

        # Campaign should be deleted
        assert not Campaign.objects.filter(id=campaign_id).exists()
        # No memberships should exist
        assert not CampaignMembership.objects.filter(campaign_id=campaign_id).exists()

    def test_leave_campaign_player(self, user_profile, campaign):
        """Player can leave without restrictions."""
        # Add a player
        user = User.objects.create_user(
            username="leaving_player_user",
            email="leaving_player@example.com",
            password="password123",
        )
        player = UserProfile.objects.create(user=user, display_name="Player")
        CampaignMembership.objects.create(
            user=player, campaign=campaign, role=CampaignMembership.CampaignRoles.PLAYER
        )

        services.leave_campaign(member=player, campaign=campaign)

        assert not CampaignMembership.objects.filter(
            user=player, campaign=campaign
        ).exists()
        assert Campaign.objects.filter(id=campaign.id).exists()

    def test_leave_campaign_player_when_gm_remains(self, user_profile, campaign):
        """
        Player leaves when GM remains - campaign continues.
        """
        # Add a player
        user = User.objects.create_user(
            username="another_player_user",
            email="another_player@example.com",
            password="password123",
        )
        player = UserProfile.objects.create(user=user, display_name="Another Player")
        CampaignMembership.objects.create(
            user=player, campaign=campaign, role=CampaignMembership.CampaignRoles.PLAYER
        )

        services.leave_campaign(member=player, campaign=campaign)

        # GM (user_profile) still exists
        assert CampaignMembership.objects.filter(
            user=user_profile, campaign=campaign
        ).exists()
        assert Campaign.objects.filter(id=campaign.id).exists()


class TestPromoteToGM:
    """Tests for promote_to_gm function."""

    def test_promote_to_gm_success(self, user_profile, campaign):
        """Successfully promote a player to GM."""
        # Add a player
        user = User.objects.create_user(
            username="locked_in", email="locked_in@example.com", password="password123"
        )

        player = UserProfile.objects.create(user=user, display_name="Player")
        CampaignMembership.objects.create(
            user=player, campaign=campaign, role=CampaignMembership.CampaignRoles.PLAYER
        )

        services.promote_to_gm(member=player, campaign=campaign)

        membership = CampaignMembership.objects.get(user=player, campaign=campaign)
        assert membership.role == CampaignMembership.CampaignRoles.GM

    def test_promote_to_gm_not_member(self, another_user, campaign):
        """Raise error when user is not a member."""
        with pytest.raises(UserNotMemberError):
            services.promote_to_gm(member=another_user, campaign=campaign)

    def test_promote_to_gm_already_gm(self, user_profile, campaign):
        """Raise error when user is already a GM."""
        with pytest.raises(UserAlreadyGMError):
            services.promote_to_gm(member=user_profile, campaign=campaign)


class TestDemoteToPlayer:
    """Tests for demote_to_player function."""

    def test_demote_to_player_success(self, user_profile, campaign):
        """Successfully demote a GM to player."""
        # Add another GM so we can demote user_profile
        user = User.objects.create_user(
            username="burnout_user",
            email="burntout@example.com",
            password="password123",
        )

        other_gm = UserProfile.objects.create(user=user, display_name="Other GM")
        CampaignMembership.objects.create(
            user=other_gm, campaign=campaign, role=CampaignMembership.CampaignRoles.GM
        )

        services.demote_to_player(member=user_profile, campaign=campaign)

        membership = CampaignMembership.objects.get(
            user=user_profile, campaign=campaign
        )
        assert membership.role == CampaignMembership.CampaignRoles.PLAYER

    def test_demote_to_player_not_member(self, another_user, campaign):
        """Raise error when user is not a member."""
        with pytest.raises(UserNotMemberError):
            services.demote_to_player(member=another_user, campaign=campaign)

    def test_demote_to_player_already_player(self, user_profile, campaign):
        """Raise error when user is already a player."""
        # Demote to player first
        user = User.objects.create_user(
            username="bad_at_job_user",
            email="badjob@example.com",
            password="password123",
        )

        other_gm = UserProfile.objects.create(user=user, display_name="Other GM")
        CampaignMembership.objects.create(
            user=other_gm, campaign=campaign, role=CampaignMembership.CampaignRoles.GM
        )
        services.demote_to_player(member=user_profile, campaign=campaign)

        # Try to demote again
        with pytest.raises(UserAlreadyPlayerError):
            services.demote_to_player(member=user_profile, campaign=campaign)

    def test_demote_last_gm_to_player(self, user_profile, campaign):
        """Raise error when trying to demote the last GM."""
        with pytest.raises(LastGMCannotLeaveError):
            services.demote_to_player(member=user_profile, campaign=campaign)


# --- Integration Tests ---


class TestServiceIntegration:
    """Integration tests combining multiple service functions."""

    def test_full_user_flow(self, user_profile, another_user):
        """Test a complete user journey through the service layer."""
        # 1. Create campaign
        campaign = services.create_campaign(
            creator=user_profile,
            title="Integration Test",
            description="Testing the full flow",
        )

        assert campaign.title == "Integration Test"
        assert CampaignMembership.objects.filter(
            user=user_profile,
            campaign=campaign,
            role=CampaignMembership.CampaignRoles.GM,
        ).exists()

        # 2. Another user joins
        membership = services.join_campaign(user=another_user, campaign=campaign)
        assert membership.role == CampaignMembership.CampaignRoles.PLAYER

        # 3. Promote another_user to GM
        services.promote_to_gm(member=another_user, campaign=campaign)
        membership.refresh_from_db()
        assert membership.role == CampaignMembership.CampaignRoles.GM

        # 4. Original user leaves (now safe because there's another GM)
        services.leave_campaign(member=user_profile, campaign=campaign)
        assert not CampaignMembership.objects.filter(
            user=user_profile, campaign=campaign
        ).exists()

        # 5. Campaign still exists with another_user as GM
        assert Campaign.objects.filter(id=campaign.id).exists()
        assert CampaignMembership.objects.filter(
            user=another_user,
            campaign=campaign,
            role=CampaignMembership.CampaignRoles.GM,
        ).exists()

    def test_atomic_transaction_rollback(self, user_profile):
        """Test that transactions rollback on error."""
        # Create a campaign that will fail due to invalid data
        with pytest.raises(CampaignTitleIsInvalidError):
            services.create_campaign(
                creator=user_profile,
                title="A" * 101,  # Invalid title
                description="Valid description",
            )

        # Verify no campaign was created
        assert Campaign.objects.count() == 0

        # Now create a valid campaign
        campaign = services.create_campaign(
            creator=user_profile, title="Valid Title", description="Valid description"
        )

        # Verify one campaign was created
        assert Campaign.objects.count() == 1
        assert CampaignMembership.objects.count() == 1


# --- Edge Cases ---


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_concurrent_membership_creation(self, another_user, campaign):
        """Test handling of concurrent membership attempts."""
        # First join should succeed - another_user is not yet a member
        membership1 = services.join_campaign(user=another_user, campaign=campaign)
        assert membership1 is not None

        # Second join should fail - now another_user IS a member
        with pytest.raises(UserAlreadyMemberError):
            services.join_campaign(user=another_user, campaign=campaign)

    def test_empty_string_handling(self, user_profile):
        """Test handling of empty strings for title and description."""
        # Empty title should not be allowed
        with pytest.raises(CampaignTitleIsInvalidError):
            campaign = services.create_campaign(
                creator=user_profile, title="", description="Description"
            )  # Empty string

        # Empty description should be allowed
        campaign = services.create_campaign(
            creator=user_profile, title="Title", description=""  # Empty string
        )
        assert campaign.description == ""

    def test_whitespace_handling(self, user_profile):
        """Test handling of whitespace-only strings."""
        # You might want to strip whitespace in your service
        campaign = services.create_campaign(
            creator=user_profile,
            title="  Title with spaces  ",
            description="  Description with spaces  ",
        )
        # Currently, this preserves whitespace - adjust based on your requirements
        assert campaign.title == "  Title with spaces  "
        assert campaign.description == "  Description with spaces  "
