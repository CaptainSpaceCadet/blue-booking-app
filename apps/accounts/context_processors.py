from django.contrib.auth.models import User

from apps.accounts.models import UserProfile


def user_profile(request):
    context = {}
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            context["user_profile"] = profile
        except User.DoesNotExist:
            context["user_profile"] = None
    else:
        context["user_profile"] = None
    return context
