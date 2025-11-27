from django.contrib import admin
from .models import Paper

@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "category",
        "institution",
        "citation",
        "open_access",
        "locations",
        "announcement_date",
        "weekly_count",
        "submit",
        "alex_paper_id",
    )