from django.db import models

class User(models.Model):
    email = models.EmailField(unique=True, verbose_name="Email Address")
    password = models.CharField(max_length=128, verbose_name="Password")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    def __str__(self):
        return self.email

from user.models import CustomUser  # Import from user app

class Business(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='businesses')  # Do not change
    name = models.CharField(max_length=255)
    shop = models.CharField(max_length=255)
    mobile_number = models.CharField(max_length=15)
    business_type = models.CharField(max_length=255)
    google_map_location = models.TextField()
    business_address = models.TextField()
    description = models.TextField(blank=True, null=True)  # New field
    hours_of_operation = models.CharField(max_length=255, blank=True, null=True)  # New field
    approval_status = models.BooleanField(default=False)
    likes = models.ManyToManyField(CustomUser, related_name='liked_businesses', blank=True)  # Users who liked

    def total_likes(self):
        return self.likes.count()

    def __str__(self):
        return self.name

class BusinessImage(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='business_images/')
    likes_count = models.IntegerField(default=0)

    def __str__(self):
        return f"Image for {self.business.name}"

class Visitor(models.Model):
    business = models.ForeignKey('Business', on_delete=models.CASCADE, related_name='visitors')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # Track user who visited
    visit_time = models.DateTimeField(auto_now_add=True)  # Record when they visited

    class Meta:
        unique_together = ('business', 'user')  # Prevent duplicate visits

    def __str__(self):
        return f"{self.user.username} visited {self.business.name}"
    
class Review(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # Ensure this is a ForeignKey
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="reviews")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} on {self.business.name}"