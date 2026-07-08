from django.urls import path
from . import views

urlpatterns = [
    path('<int:pk>/', views.listing_detail, name='listing_detail'),
    path('<int:pk>/reserve/', views.make_reservation, name='make_reservation'),
    path('<int:pk>/inquire/', views.send_inquiry, name='send_inquiry'),
    path('<int:pk>/review/', views.submit_review, name='submit_review'),
    path('landlord/', views.landlord_dashboard, name='landlord_dashboard'),
    path('landlord/<int:pk>/toggle/', views.toggle_house_availability, name='toggle_house_availability'),
]
