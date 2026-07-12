from django.shortcuts import render

# Create your views here.


def markdown_editor(request):
    return render(request, "markdown-editor.html")
