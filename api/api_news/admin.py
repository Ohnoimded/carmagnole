# from django.contrib import admin
# from .models import DailyData, FrequentData

# @admin.register(DailyData)
# class DailyDataAdmin(admin.ModelAdmin):
#     list_display = ('url', 'source', 'author', 'publishdate')
#     list_filter = ('source', 'publishdate')
#     search_fields = ('url', 'author')
#     date_hierarchy = 'publishdate'
#     readonly_fields = ('url', 'source', 'author', 'publishdate', 'imageurl', 'headline', 'description')

# @admin.register(FrequentData)
# class FrequentDataAdmin(admin.ModelAdmin):
#     list_display = ('url', 'source', 'author', 'publishdate')
#     list_filter = ('source', 'publishdate')
#     search_fields = ('url', 'author')
#     date_hierarchy = 'publishdate'
#     readonly_fields = ('url', 'source', 'author', 'publishdate', 'imageurl', 'headline', 'htmlbody', 'wordcount')
