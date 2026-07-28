from django.urls import path

from apps.personas import views

app_name = "personas"

urlpatterns = [
    path(
        "<int:campaign_id>/create-persona/<str:persona_type>/cancel/",
        views.cancel_create_persona,
        name="cancel-create-persona",
    ),
    path(
        "<int:campaign_id>/create-persona/<str:persona_type>/",
        views.create_persona,
        name="create-persona",
    ),
    path(
        "<int:campaign_id>/edit-persona/<int:persona_id>/cancel/",
        views.cancel_edit_persona,
        name="cancel-edit-persona",
    ),
    path(
        "<int:campaign_id>/edit-persona/<int:persona_id>/",
        views.edit_persona,
        name="edit-persona",
    ),
    path(
        "<int:campaign_id>/retire-persona/<int:persona_id>/",
        views.retire_persona,
        name="retire-persona",
    ),
    path(
        "<int:campaign_id>/persona-list/<str:persona_type>/<str:persona_status>/",
        views.persona_list,
        name="persona-list",
    ),
    path(
        "<int:campaign_id>/personas-content-page/",
        views.personas_page_content,
        name="personas-content-page",
    ),
    path("<int:campaign_id>/personas-page/", views.personas_page, name="personas-page"),
]
