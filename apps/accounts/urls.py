from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("open-view/", views.open_view, name="open_view"),
    path("secret-view/", views.secret_view, name="secret_view"),
]
