from django.urls import path
from . import views

app_name = "posts"

urlpatterns = [
    path("markdown-editor/", views.markdown_editor, name="markdown-editor"),
]
