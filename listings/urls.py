from django.urls import path
from . import views

urlpatterns = [
    # Public / tenant — listings
    path("<int:pk>/", views.listing_detail, name="listing_detail"),
    path("<int:pk>/inquire/", views.send_inquiry, name="send_inquiry"),
    path("<int:pk>/review/", views.submit_review, name="submit_review"),
    path("<int:pk>/favorite/", views.toggle_favorite, name="toggle_favorite"),

    # Booking flow
    path("<int:pk>/reserve/", views.make_reservation, name="make_reservation"),
    path("<int:pk>/book/", views.make_booking, name="make_booking"),
    path("bookings/<int:pk>/confirmation/", views.booking_confirmation, name="booking_confirmation"),
    path("bookings/<int:pk>/cancel/", views.cancel_reservation, name="cancel_reservation"),

    # Messaging
    path("messages/send/", views.send_message, name="send_message"),
    path("messages/<int:pk>/read/", views.mark_message_read, name="mark_message_read"),

    # Inquiry threads
    path("inquiries/<int:pk>/thread/", views.inquiry_thread, name="inquiry_thread"),
    path("inquiries/<int:pk>/reply/", views.reply_inquiry_thread, name="reply_inquiry_thread"),

    # Notifications
    path("notifications/", views.notifications_list, name="notifications_list"),
    path("notifications/<int:pk>/read/", views.mark_notification_read, name="mark_notification_read"),
    path("notifications/read-all/", views.mark_all_notifications_read, name="mark_all_notifications_read"),

    # Landlord-only
    path("landlord/", views.landlord_dashboard, name="landlord_dashboard"),
    path("landlord/<int:pk>/toggle/", views.toggle_house_availability, name="toggle_house_availability"),
    path("landlord/houses/<int:house_pk>/rooms/add/", views.add_room, name="add_room"),
    path("landlord/houses/<int:pk>/edit/", views.edit_house, name="edit_house"),
    path("landlord/houses/<int:pk>/delete/", views.delete_house, name="delete_house"),
    path("landlord/houses/<int:house_pk>/photos/add/", views.add_house_photo, name="add_house_photo"),
    path("landlord/photos/<int:photo_pk>/delete/", views.delete_house_photo, name="delete_house_photo"),
    path("landlord/rooms/<int:room_pk>/edit/", views.edit_room_status, name="edit_room_status"),
    path("landlord/rooms/<int:room_pk>/toggle/", views.toggle_room_availability, name="toggle_room_availability"),
    path("landlord/rooms/<int:room_pk>/delete/", views.delete_room, name="delete_room"),
    path("landlord/reservations/<int:pk>/update/", views.update_reservation_status, name="update_reservation_status"),
    path("landlord/inquiries/<int:pk>/reply/", views.reply_inquiry, name="reply_inquiry"),
    path("landlord/analytics/", views.analytics_data, name="analytics_data"),
]
