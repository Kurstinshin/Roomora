from django.urls import path
from . import views

urlpatterns = [
    path('<int:pk>/', views.listing_detail, name='listing_detail'),
]
