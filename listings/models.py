from django.conf import settings
from django.db import models


class BoardingHouse(models.Model):
    AVAILABILITY_CHOICES = [
        ("Available", "Available"),
        ("Not Available", "Not Available"),
    ]

    house_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.PositiveIntegerField()
    availability_status = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default="Available")
    image = models.URLField(blank=True, default="img.jpg")
    is_active = models.BooleanField(default=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, through='UserBoardingHouse', related_name='boarding_houses')

    class Meta:
        ordering = ["house_name"]

    def __str__(self):
        return self.house_name

    @property
    def title(self):
        return self.house_name

    @property
    def location(self):
        return self.address

    @property
    def image_url(self):
        return self.image


class UserBoardingHouse(models.Model):
    ROLE_CHOICES = [
        ("landlord", "Landlord"),
        ("tenant", "Tenant"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="boarding_house_assignments")
    boarding_house = models.ForeignKey(BoardingHouse, on_delete=models.CASCADE, related_name="user_assignments")
    assigned_role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    date_assigned = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.boarding_house} ({self.assigned_role})"


class Room(models.Model):
    ROOM_TYPE_CHOICES = [
        ("single", "Single"),
        ("double", "Double"),
        ("suite", "Suite"),
    ]
    AVAILABILITY_CHOICES = [
        ("Available", "Available"),
        ("Not Available", "Not Available"),
    ]

    boarding_house = models.ForeignKey(BoardingHouse, on_delete=models.CASCADE, related_name="rooms")
    room_number = models.CharField(max_length=50)
    room_type = models.CharField(max_length=50, choices=ROOM_TYPE_CHOICES)
    capacity = models.PositiveIntegerField()
    price = models.PositiveIntegerField()
    availability_status = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default="Available")

    class Meta:
        unique_together = ("boarding_house", "room_number")
        ordering = ["boarding_house", "room_number"]

    def __str__(self):
        return f"{self.boarding_house.house_name} - Room {self.room_number}"


class Reservation(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Confirmed", "Confirmed"),
        ("Cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reservations")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="reservations")
    reservation_date = models.DateField(auto_now_add=True)
    check_in_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")

    class Meta:
        ordering = ["-reservation_date"]

    def __str__(self):
        return f"Reservation {self.pk} for {self.room}"


class Inquiry(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Closed", "Closed"),
        ("Responded", "Responded"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="inquiries")
    boarding_house = models.ForeignKey(BoardingHouse, on_delete=models.CASCADE, related_name="inquiries")
    message = models.TextField()
    date_sent = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")

    class Meta:
        ordering = ["-date_sent"]

    def __str__(self):
        return f"Inquiry {self.pk} from {self.user}"


class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    boarding_house = models.ForeignKey(BoardingHouse, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    review_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-review_date"]

    def __str__(self):
        return f"Review {self.pk} ({self.rating}) for {self.boarding_house}"
