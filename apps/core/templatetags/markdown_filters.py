from django.template.defaultfilters import register
from django.utils.safestring import mark_safe
from justhtml import JustHTML
import markdown


@register.filter(name="safe_markdown")
def safe_markdown(value):
    """Convert Markdown to safe HTML."""

    if not value:
        return ""

    html = markdown.markdown(
        value,
        extensions=[
            "markdown.extensions.extra",
            "markdown.extensions.tables",
            "markdown.extensions.nl2br",
            "markdown.extensions.sane_lists",
            "markdown_katex",
        ],
    )

    safe_html = JustHTML(html, fragment=True).to_html()
    return mark_safe(safe_html)
