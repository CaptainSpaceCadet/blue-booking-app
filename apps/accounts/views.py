from allauth import account
from allauth.account.views import PasswordChangeView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render
from django.utils.decorators import method_decorator


def open_view(request):
    return render(request, "test1.html")


@login_required
def secret_view(request):
    return render(request, "test2.html")


@login_required
def password_change_partial(request):
    return render(
        request,
        "settings/_password_change.html",
        {"form": PasswordChangeForm(request.user)},
    )


class CustomPasswordChangeView(PasswordChangeView):
    def get(self, request, *args, **kwargs):
        if request.htmx:
            print("htmx get")
            return render(
                request, "settings/_password_change.html", {"form": self.get_form()}
            )

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            form.save()
            if request.htmx:
                print("htmx post")
                return render(
                    request,
                    "settings/_password_change_success.html",
                    {"message": "Password changed successfully!"},
                )
            return super().post(request, *args, **kwargs)
        else:
            if request.htmx:
                return render(request, "settings/_password_change.html", {"form": form})

            return super().post(request, *args, **kwargs)
