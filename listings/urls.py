from django.urls import path
from . import views

urlpatterns = [
    # Public / tenant — listings
    path("<int:pk>/", views.listing_detail, name="listing_detail"),
    path("<int:pk>/inquire/", views.send_inquiry, name="send_inquiry"),
    path("<int:pk>/review/", views.submit_review, name="submit_review"),

    # Booking flow — two distinct actions
    path("<int:pk>/reserve/", views.make_reservation, name="make_reservation"),  # Hold room, move-in date only
    path("<int:pk>/book/", views.make_booking, name="make_booking"),             # Fixed-period booking
    path("bookings/<int:pk>/confirmation/", views.booking_confirmation, name="booking_confirmation"),
    path("bookings/<int:pk>/cancel/", views.cancel_reservation, name="cancel_reservation"),

    # Messaging (both roles)
    path("messages/send/", views.send_message, name="send_message"),
    path("messages/<int:pk>/read/", views.mark_message_read, name="mark_message_read"),

    # Landlord-only
    path("landlord/", views.landlord_dashboard, name="landlord_dashboard"),
    path("landlord/<int:pk>/toggle/", views.toggle_house_availability, name="toggle_house_availability"),
    path("landlord/houses/<int:house_pk>/rooms/add/", views.add_room, name="add_room"),
    path("landlord/houses/<int:pk>/edit/", views.edit_house, name="edit_house"),
    path("landlord/rooms/<int:room_pk>/edit/", views.edit_room_status, name="edit_room_status"),
    path("landlord/reservations/<int:pk>/update/", views.update_reservation_status, name="update_reservation_status"),
    path("landlord/inquiries/<int:pk>/reply/", views.reply_inquiry, name="reply_inquiry"),
]

