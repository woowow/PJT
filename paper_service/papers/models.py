from django.db import models

# Create your models here.
class Paper(models.Model):
    title = models.CharField(max_length=500)
    authors = models.TextField()
    abstract = models.TextField()
    arxiv_id = models.CharField(max_length=100, unique=True)
    published = models.DateTimeField()
    updated = models.DateTimeField()
    categories = models.CharField(max_length=200)
    pdf_url = models.URLField()

    # # Semantic Scholar 추가 필드
    # citation_count = models.IntegerField(null=True, blank=True)
    # influential_citation_count = models.IntegerField(null=True, blank=True)
    # recent_interest = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
