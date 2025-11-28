from rest_framework import serializers
from .models import Paper, Category, Institution, Author, Abstract, YearCitation, Guest, GuestFavorite, GuestCategoryCount

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"

class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = "__all__"

class PaperSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paper
        fields = "__all__"

class PaperDetailSerializer(serializers.ModelSerializer):
    abstract = serializers.CharField(source='abstract.context', read_only=True)
    year_citations = serializers.SerializerMethodField()
    authors = serializers.SerializerMethodField()

    class Meta:
        model = Paper
        fields = "__all__"

    def get_year_citations(self, obj):
        try:
            return {
                "year1": obj.yearcitation.recent_year1_count,
                "year2": obj.yearcitation.recent_year2_count,
                "year3": obj.yearcitation.recent_year3_count,
            }
        except:
            return None
    
    def get_authors(self, obj):
        return list(obj.author_set.values("author_id", "author_name"))

class GuestFavoriteSerializer(serializers.ModelSerializer):
    paper = PaperSerializer()

    class Meta:
        model = GuestFavorite
        fields = "__all__"
