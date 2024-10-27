from rest_framework import serializers
from utils.models import DailyData, FrequentData
from django.utils.html import escape

class FrequentDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = FrequentData
        fields = ['id', 'section', 'imageurl', 'headline', 'wordcount', 'publishdate', 'nohtmlbody', 'slug']

    def validate(self, data):
        for field in data:
            if isinstance(data[field], str):
                data[field] = escape(data[field])
        return data

class ArticleDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = FrequentData
        fields = ['id', 'section', 'imageurl', 'headline', 'wordcount', 'publishdate', 'htmlbody', 'slug']

    def validate(self, data):
        for field in data:
            if isinstance(data[field], str):
                data[field] = escape(data[field])
        return data