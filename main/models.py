from django.db import models

# Create your models here.
class City(models.Model):
    name = models.CharField(max_length=120)
    country = models.CharField(max_length=2,default="MX")
    lat = models.FloatField(null=True,blank=True)
    lon = models.FloatField(null=True,blank=True)
    
    class Meta:
        unique_together = ("name","country")
        
    def __str__(self):
        return f"{self.name},{self.country}"
    
    
class Search(models.Model):
    query = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True,blank=True)
    ok = models.BooleanField(default=True)