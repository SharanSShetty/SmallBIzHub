from django.db import models

class CustomUser(models.Model):
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255, blank=True, null=True)  # Blank for Google users
    phone_number = models.CharField(max_length=15, blank=True, null=True)  # Optional phone number
    profile = models.ImageField(upload_to='profile_pics/', blank=True, null=True)  # Profile photo
    saved_businesses = models.ManyToManyField('Business.Business', blank=True, related_name='saved_by')

    def _str_(self):
        return self.username