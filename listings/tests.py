from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from listings.models import BoardingHouse, Inquiry, Reservation, Review, Room, UserBoardingHouse
from users.models import Profile


class LandlordDashboardTests(TestCase):
    def setUp(self):
        self.landlord = get_user_model().objects.create_user(
            username="landlord",
            email="landlord@example.com",
            password="secret123",
        )
        Profile.objects.create(user=self.landlord, role="landlord")

        self.tenant = get_user_model().objects.create_user(
            username="tenant",
            email="tenant@example.com",
            password="secret123",
        )
        Profile.objects.create(user=self.tenant, role="tenant")

    def test_landlord_can_create_boarding_house_from_dashboard(self):
        self.client.login(username="landlord", password="secret123")

        response = self.client.post(
            reverse("landlord_dashboard"),
            {
                "house_name": "Sunset House",
                "address": "Cebu City",
                "description": "Bright and quiet place",
                "price": 4500,
                "image": "https://example.com/house.jpg",
            },
        )

        self.assertEqual(response.status_code, 302)
        house = BoardingHouse.objects.get(house_name="Sunset House")
        self.assertTrue(house.is_active)
        self.assertTrue(
            UserBoardingHouse.objects.filter(
                user=self.landlord,
                boarding_house=house,
                assigned_role="landlord",
            ).exists()
        )

    def test_tenant_activity_appears_on_landlord_dashboard(self):
        house = BoardingHouse.objects.create(
            house_name="Oak House",
            address="Mandaue City",
            price=4000,
            description="Comfortable home",
            image="https://example.com/oak.jpg",
        )
        UserBoardingHouse.objects.create(user=self.landlord, boarding_house=house, assigned_role="landlord")
        Room.objects.create(
            boarding_house=house,
            room_number="101",
            room_type="single",
            capacity=1,
            price=4000,
            availability_status="Available",
        )

        self.client.login(username="tenant", password="secret123")
        self.client.post(reverse("make_reservation", args=[house.pk]), {"check_in_date": "2026-07-15", "room_id": room.pk})
        self.client.post(reverse("send_inquiry", args=[house.pk]), {"message": "I would like to know about parking."})
        self.client.post(
            reverse("submit_review", args=[house.pk]),
            {"rating": 5, "comment": "Great place"},
        )

        dashboard_response = self.client.get(reverse("dashboard"))
        self.assertContains(dashboard_response, "Oak House")
        self.assertContains(dashboard_response, "Pending")
        self.client.logout()

        self.client.login(username="landlord", password="secret123")
        response = self.client.get(reverse("landlord_dashboard"))

        self.assertContains(response, "Oak House")
        self.assertContains(response, "I would like to know about parking.")
        self.assertContains(response, "Great place")
        self.assertTrue(Reservation.objects.filter(user=self.tenant).exists())
        self.assertTrue(Inquiry.objects.filter(user=self.tenant).exists())
        self.assertTrue(Review.objects.filter(user=self.tenant).exists())
        self.assertEqual(Room.objects.get(pk=room.pk).availability_status, "Not Available")
