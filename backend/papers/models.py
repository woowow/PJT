from django.db import models

class Category(models.Model):
    category_name = models.TextField()
    alex_category_id = models.TextField(unique=True)

class Institution(models.Model):
    institution_name = models.TextField()
    country_code = models.TextField()

class Author(models.Model):
    author_name = models.TextField()
    institution = models.ForeignKey(Institution, on_delete=models.RESTRICT, null=True)
    citation_total = models.IntegerField(null=True)
    main_topic_1 = models.TextField(null=True)
    main_topic_2 = models.TextField(null=True)
    main_topic_3 = models.TextField(null=True)
    alex_author_id = models.TextField(unique=True)

class Paper(models.Model):
    title = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.RESTRICT, null=True) # chk(null=True를 해야 장고 migration이 가능해서 일단 이렇게 했음, 이후에 False로 수정 필요)
    institution = models.ForeignKey(Institution, on_delete=models.RESTRICT, null=True)
    citation = models.IntegerField(null=True)
    open_access = models.BooleanField(null=True)
    locations = models.TextField(null=True)
    announcement_date = models.DateField(null=True)
    weekly_count = models.IntegerField(default=0)
    submit = models.TextField(null=True)
    alex_paper_id = models.TextField(unique=True, null=True) # chk

class Abstract(models.Model):
    paper = models.OneToOneField(Paper, primary_key=True, on_delete=models.RESTRICT)
    context = models.TextField(null=True)

class YearCitation(models.Model):
    paper = models.OneToOneField(Paper, primary_key=True, on_delete=models.RESTRICT)
    recent_year1_count = models.IntegerField(null=True)
    recent_year2_count = models.IntegerField(null=True)
    recent_year3_count = models.IntegerField(null=True)

class Guest(models.Model):
    guestname = models.TextField()
    pwd = models.TextField()
    interest_1 = models.TextField(null=True)
    interest_2 = models.TextField(null=True)
    interest_3 = models.TextField(null=True)

class GuestFavorite(models.Model):
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE)
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('guest', 'paper')

class GuestCategoryCount(models.Model):
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    count = models.IntegerField(default=0)
