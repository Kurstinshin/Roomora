from django.db import models


class Listing(models.Model):
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=120)
    price = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True, default="https://via.placeholder.com/640x360?text=Roomora+Listing")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
