from django.contrib import admin

from .models import BoardingHouse, UserBoardingHouse, Room, Reservation, Inquiry, Review


@admin.register(BoardingHouse)
class BoardingHouseAdmin(admin.ModelAdmin):
    list_display = ("house_name", "address", "price", "availability_status")
    search_fields = ("house_name", "address")


@admin.register(UserBoardingHouse)
class UserBoardingHouseAdmin(admin.ModelAdmin):
    list_display = ("user", "boarding_house", "assigned_role", "date_assigned")
    list_filter = ("assigned_role",)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("room_number", "boarding_house", "room_type", "capacity", "price", "availability_status")
    list_filter = ("room_type", "availability_status")


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "room", "reservation_date", "check_in_date", "status")
    list_filter = ("status",)


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "boarding_house", "date_sent", "status")
    list_filter = ("status",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "boarding_house", "rating", "review_date")
    list_filter = ("rating",)
