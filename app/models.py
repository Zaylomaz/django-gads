from django.db import models
class Account(models.Model):
    account_name = models.CharField(max_length=255)
    account_id = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.account_name
class Campaign(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    campaign_name = models.CharField(max_length=255)
    campaign_id = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=1)
    conversions = models.FloatField()

    def __str__(self):
        return self.campaign_name
class Location(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    location_name = models.CharField(max_length=255)

    def __str__(self):
        return self.location_name
class AdGroup(models.Model):
    campaign = models.ForeignKey(Campaign, related_name='ad_groups', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    ad_group_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=100)
    def __str__(self):
        return self.name
# Create your models here.
