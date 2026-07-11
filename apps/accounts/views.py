from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def open_view(request):
    return render(request, "test1.html")


@login_required
def secret_view(request):
    return render(request, "test2.html")
