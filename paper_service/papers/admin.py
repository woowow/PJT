from django.contrib import admin
from .models import Paper

@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    list_display = ("title", "arxiv_id", "published", "categories")
    search_fields = ("title", "abstract", "categories")



# 일단 우리가 api를 두개 쓰려고 하는데 1개는 그냥 상시 오픈(정보가 적음)
'''

admin
admin

'''