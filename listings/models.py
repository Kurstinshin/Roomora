from django.conf import settings
from django.db import models


# ──────────────────────────────────────────────
# NOTIFICATIONS
# ──────────────────────────────────────────────

class Notification(models.Model):
    NOTIF_TYPES = [
        ("status_change", "Status Change"),
        ("inquiry_reply", "Inquiry Reply"),
        ("message", "Message"),
        ("general", "General"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    message = models.CharField(max_length=500)
    notif_type = models.CharField(max_length=30, choices=NOTIF_TYPES, default="general")
    link = models.CharField(max_length=255, blank=True, help_text="URL to navigate to on click")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notif for {self.user} — {self.message[:50]}"


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
    image = models.ImageField(upload_to='boarding_houses/', blank=True, null=True)
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
        if self.image:
            return self.image.url
        return 'https://placehold.co/640x360/1a1a2e/7c3aed?text=No+Image'


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
    available_from = models.DateField(null=True, blank=True, help_text="Date the room becomes available (optional)")


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
        ("Completed", "Completed"),
    ]
    BOOKING_TYPE_CHOICES = [
        ("reservation", "Reservation"),
        ("booking", "Booking"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reservations")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="reservations")
    booking_type = models.CharField(max_length=20, choices=BOOKING_TYPE_CHOICES, default="reservation")
    reservation_date = models.DateField(auto_now_add=True)
    check_in_date = models.DateField()
    check_out_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Special requests or notes from the tenant")
    total_amount = models.PositiveIntegerField(null=True, blank=True, help_text="Pre-computed total in PHP")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")

    class Meta:
        ordering = ["-reservation_date"]

    def __str__(self):
        return f"Reservation {self.pk} for {self.room}"

    @property
    def duration_days(self):
        """Number of days between check-in and check-out."""
        if self.check_out_date and self.check_in_date:
            return (self.check_out_date - self.check_in_date).days
        return None

    @property
    def computed_total(self):
        """Room price * months (approx from days)."""
        days = self.duration_days
        if days and days > 0:
            months = days / 30
            return round(self.room.price * months)
        return self.room.price


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


class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages"
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_messages"
    )
    boarding_house = models.ForeignKey(
        BoardingHouse, on_delete=models.SET_NULL, null=True, blank=True, related_name="messages"
    )
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-sent_at"]

    def __str__(self):
        return f"Message from {self.sender} to {self.recipient} ({self.sent_at:%Y-%m-%d})"


# ──────────────────────────────────────────────
# FAVORITES / WISHLIST
# ──────────────────────────────────────────────

class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites"
    )
    boarding_house = models.ForeignKey(
        BoardingHouse, on_delete=models.CASCADE, related_name="favorited_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "boarding_house")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} ♥ {self.boarding_house}"


# ──────────────────────────────────────────────
# PROPERTY PHOTO GALLERY
# ──────────────────────────────────────────────

class BoardingHousePhoto(models.Model):
    boarding_house = models.ForeignKey(
        BoardingHouse, on_delete=models.CASCADE, related_name="photos"
    )
    image = models.ImageField(upload_to="boarding_house_photos/")
    caption = models.CharField(max_length=255, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "pk"]

    def __str__(self):
        return f"Photo for {self.boarding_house.house_name} (#{self.pk})"


# ──────────────────────────────────────────────
# INQUIRY CONVERSATION THREAD
# ──────────────────────────────────────────────

class InquiryReply(models.Model):
    inquiry = models.ForeignKey(
        Inquiry, on_delete=models.CASCADE, related_name="replies"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="inquiry_replies"
    )
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sent_at"]

    def __str__(self):
        return f"Reply by {self.sender} on Inquiry #{self.inquiry_id}"
