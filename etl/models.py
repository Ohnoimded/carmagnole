# from django.db import models
# from django.utils import timezone

# class DailyData(models.Model):
#     id = models.AutoField(primary_key=True)
#     url = models.TextField( unique=True)
#     source = models.TextField(null=True, blank=True)
#     author = models.TextField(null=True, blank=True)
#     imageurl = models.TextField(null=True, blank=True)
#     headline = models.TextField(null=True, blank=True)
#     publishdate = models.DateTimeField( null=False)
#     description = models.TextField(null=True, blank=True)

#     class Meta:
#         db_table = 'daily_data'
#         unique_together = [['url','id']]



# class FrequentData(models.Model):
#     id = models.AutoField(primary_key=True)
#     url = models.TextField( unique=True)
#     shorturl = models.TextField(unique=True, null=True, blank=True)
#     source = models.TextField(null=True, blank=True)
#     section = models.TextField(null=True, blank=True)
#     author = models.TextField(null=True, blank=True)
#     imageurl = models.TextField(null=True, blank=True)
#     headline = models.TextField(null=True, blank=True)
#     wordcount = models.IntegerField(null=True, blank=True)
#     publishdate = models.DateTimeField( null=False)
#     htmlbody = models.TextField(null=True, blank=True)

#     class Meta:
#         db_table = 'frequent_data'
#         unique_together = [['url','id']]
