import datetime

from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q

from .forms import (
    BoardingHouseForm,
    BookingForm,
    InquiryForm,
    InquiryReplyForm,
    MessageForm,
    ReservationForm,
    ReviewForm,
    RoomForm,
)
from .models import BoardingHouse, Inquiry, Message, Reservation, Review, Room, UserBoardingHouse


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def _require_landlord(request):
    """Return None if user is a landlord, or HttpResponseForbidden."""
    try:
        if request.user.profile.role == "landlord":
            return None
    except Exception:
        pass
    return HttpResponseForbidden("You must be a landlord to access this page.")


def _room_is_available(room, check_in, check_out, exclude_reservation_pk=None):
    """
    Return True if the room has no confirmed/pending reservations
    overlapping the [check_in, check_out) window.
    """
    qs = Reservation.objects.filter(
        room=room,
        status__in=("Pending", "Confirmed"),
        check_in_date__lt=check_out,
        check_out_date__gt=check_in,
    )
    if exclude_reservation_pk:
        qs = qs.exclude(pk=exclude_reservation_pk)
    return not qs.exists()


# ──────────────────────────────────────────────
# LISTING DETAIL  (public-facing)
# ──────────────────────────────────────────────

def listing_detail(request, pk):
    listing = get_object_or_404(BoardingHouse, pk=pk, is_active=True)
    rooms   = listing.rooms.all()
    reviews = listing.reviews.select_related("user").all()
    avg_rating = None
    if reviews:
        avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 1)

    is_owner = False
    if request.user.is_authenticated:
        is_owner = UserBoardingHouse.objects.filter(
            user=request.user, boarding_house=listing, assigned_role="landlord"
        ).exists()

    available_rooms = rooms.filter(availability_status="Available")

    return render(request, "listings/listing_detail.html", {
        "listing":          listing,
        "rooms":            rooms,
        "available_rooms":  available_rooms,
        "reviews":          reviews,
        "avg_rating":       avg_rating,
        "is_owner":         is_owner,
        "reservation_form": ReservationForm(),
        "booking_form":     BookingForm(),
        "inquiry_form":     InquiryForm(),
        "review_form":      ReviewForm(),
        "today":            datetime.date.today().isoformat(),
    })


# ──────────────────────────────────────────────
# BOOKING (tenant)
# ──────────────────────────────────────────────

@login_required
def make_reservation(request, pk):
    """
    RESERVE — tenant holds a room with just a move-in date.
    Month-to-month, no checkout date, no price computation.
    """
    listing = get_object_or_404(BoardingHouse, pk=pk, is_active=True)
    if request.method != "POST":
        return redirect("listing_detail", pk=pk)

    form = ReservationForm(request.POST)
    if not form.is_valid():
        for errs in form.errors.values():
            for err in errs:
                messages.error(request, err)
        return redirect("listing_detail", pk=pk)

    move_in = form.cleaned_data["move_in_date"]
    room_id = form.cleaned_data.get("room_id") or request.POST.get("room_id")

    if room_id:
        room = get_object_or_404(Room, pk=room_id, boarding_house=listing)
    else:
        room = listing.rooms.filter(availability_status="Available").first()

    if not room:
        messages.error(request, "No available rooms for this boarding house.")
        return redirect("listing_detail", pk=pk)

    if room.availability_status != "Available":
        messages.error(request, f"Room {room.room_number} is not available.")
        return redirect("listing_detail", pk=pk)

    reservation = Reservation.objects.create(
        user=request.user,
        room=room,
        booking_type="reservation",
        check_in_date=move_in,
        status="Pending",
    )
    # Mark room as held
    room.availability_status = "Not Available"
    room.save(update_fields=["availability_status"])

    return redirect("booking_confirmation", pk=reservation.pk)


@login_required
def make_booking(request, pk):
    """
    BOOK NOW — tenant books for a fixed period with check-in & check-out dates.
    Validates no date overlap, computes estimated total.
    """
    listing = get_object_or_404(BoardingHouse, pk=pk, is_active=True)
    if request.method != "POST":
        return redirect("listing_detail", pk=pk)

    form = BookingForm(request.POST)
    if not form.is_valid():
        for errs in form.errors.values():
            for err in errs:
                messages.error(request, err)
        return redirect("listing_detail", pk=pk)

    check_in  = form.cleaned_data["check_in_date"]
    check_out = form.cleaned_data["check_out_date"]
    notes     = form.cleaned_data.get("notes", "")
    room_id   = form.cleaned_data.get("room_id") or request.POST.get("room_id")

    if room_id:
        room = get_object_or_404(Room, pk=room_id, boarding_house=listing)
    else:
        room = listing.rooms.filter(availability_status="Available").first()

    if not room:
        messages.error(request, "No available rooms for this boarding house.")
        return redirect("listing_detail", pk=pk)

    # Check for overlap with existing bookings on this room
    if not _room_is_available(room, check_in, check_out):
        messages.error(
            request,
            f"Room {room.room_number} is already booked for those dates. "
            "Please choose different dates or another room."
        )
        return redirect("listing_detail", pk=pk)

    # Compute estimated total from duration
    days  = (check_out - check_in).days
    total = round(room.price * (days / 30))

    reservation = Reservation.objects.create(
        user=request.user,
        room=room,
        booking_type="booking",
        check_in_date=check_in,
        check_out_date=check_out,
        notes=notes,
        total_amount=total,
        status="Pending",
    )
    # Mark room as held
    room.availability_status = "Not Available"
    room.save(update_fields=["availability_status"])

    return redirect("booking_confirmation", pk=reservation.pk)


@login_required
def booking_confirmation(request, pk):
    """Booking confirmation / summary page."""
    reservation = get_object_or_404(Reservation, pk=pk, user=request.user)
    return render(request, "listings/booking_confirmation.html", {
        "reservation": reservation,
    })


@login_required
def cancel_reservation(request, pk):
    """Tenant cancels their own booking (Pending only)."""
    reservation = get_object_or_404(Reservation, pk=pk, user=request.user)

    if reservation.status not in ("Pending",):
        messages.error(request, "Only pending bookings can be cancelled by you.")
        return redirect("dashboard")

    if request.method == "POST":
        reservation.status = "Cancelled"
        reservation.save()
        # Re-open the room if no other active bookings exist
        other_active = Reservation.objects.filter(
            room=reservation.room,
            status__in=("Pending", "Confirmed"),
        ).exclude(pk=reservation.pk).exists()
        if not other_active:
            reservation.room.availability_status = "Available"
            reservation.room.save(update_fields=["availability_status"])
        messages.success(request, f"Booking #{reservation.pk} has been cancelled.")

    return redirect("dashboard")


# ──────────────────────────────────────────────
# TENANT ACTIONS — Inquiry & Review
# ──────────────────────────────────────────────

@login_required
def send_inquiry(request, pk):
    listing = get_object_or_404(BoardingHouse, pk=pk, is_active=True)
    if request.method != "POST":
        return redirect("listing_detail", pk=pk)

    form = InquiryForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Invalid inquiry data.")
        return redirect("listing_detail", pk=pk)

    Inquiry.objects.create(
        user=request.user, boarding_house=listing, message=form.cleaned_data["message"]
    )
    messages.success(request, "Inquiry sent. The owner will respond shortly.")
    return redirect("listing_detail", pk=pk)


@login_required
def submit_review(request, pk):
    listing = get_object_or_404(BoardingHouse, pk=pk, is_active=True)
    if request.method != "POST":
        return redirect("listing_detail", pk=pk)

    form = ReviewForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Invalid review data.")
        return redirect("listing_detail", pk=pk)

    Review.objects.create(
        user=request.user,
        boarding_house=listing,
        rating=form.cleaned_data["rating"],
        comment=form.cleaned_data.get("comment", ""),
    )
    messages.success(request, "Thanks — your review has been submitted.")
    return redirect("listing_detail", pk=pk)


# ──────────────────────────────────────────────
# MESSAGING (both roles)
# ──────────────────────────────────────────────

@login_required
def send_message(request):
    if request.method != "POST":
        return redirect("dashboard")

    form = MessageForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Invalid message data.")
        return redirect(request.META.get("HTTP_REFERER", "dashboard"))

    recipient = get_object_or_404(User, pk=form.cleaned_data["recipient_id"])
    house_id  = form.cleaned_data.get("boarding_house_id")
    house     = BoardingHouse.objects.filter(pk=house_id).first() if house_id else None

    Message.objects.create(
        sender=request.user,
        recipient=recipient,
        boarding_house=house,
        subject=form.cleaned_data.get("subject", ""),
        body=form.cleaned_data["body"],
    )
    messages.success(request, "Message sent successfully.")
    return redirect(request.META.get("HTTP_REFERER", "dashboard"))


# ──────────────────────────────────────────────
# LANDLORD DASHBOARD
# ──────────────────────────────────────────────

@login_required
def landlord_dashboard(request):
    forbidden = _require_landlord(request)
    if forbidden:
        return forbidden

    if request.method == "POST" and "publish_house" in request.POST:
        form = BoardingHouseForm(request.POST, request.FILES)
        if form.is_valid():
            house = form.save(commit=False)
            house.is_active = True
            house.save()
            UserBoardingHouse.objects.create(
                user=request.user, boarding_house=house, assigned_role="landlord"
            )
            messages.success(request, "Boarding house published successfully.")
        else:
            messages.error(request, "Please correct the boarding house details.")
        return redirect("landlord_dashboard")

    houses = BoardingHouse.objects.filter(
        user_assignments__user=request.user,
        user_assignments__assigned_role="landlord",
    ).prefetch_related("rooms").distinct()

    house_data       = []
    all_reservations = []
    all_inquiries    = []
    all_reviews      = []

    for house in houses:
        reservations = Reservation.objects.filter(
            room__boarding_house=house
        ).select_related("user", "room")
        inquiries = Inquiry.objects.filter(boarding_house=house).select_related("user")
        reviews   = Review.objects.filter(boarding_house=house).select_related("user")
        rooms     = house.rooms.all()

        house_data.append({
            "house":             house,
            "rooms":             rooms,
            "room_count":        rooms.count(),
            "reservation_count": reservations.count(),
            "inquiry_count":     inquiries.count(),
            "review_count":      reviews.count(),
            "room_form":         RoomForm(),
        })
        all_reservations.extend(reservations)
        all_inquiries.extend(inquiries)
        all_reviews.extend(reviews)

    inbox_messages = Message.objects.filter(recipient=request.user).select_related(
        "sender", "boarding_house"
    )

    all_reservations.sort(key=lambda r: r.reservation_date, reverse=True)
    all_inquiries.sort(key=lambda i: i.date_sent, reverse=True)
    all_reviews.sort(key=lambda r: r.review_date, reverse=True)

    # Counts for landlord stats
    pending_count   = sum(1 for r in all_reservations if r.status == "Pending")
    confirmed_count = sum(1 for r in all_reservations if r.status == "Confirmed")

    return render(request, "listings/landlord_dashboard.html", {
        "houses":           house_data,
        "all_reservations": all_reservations,
        "all_inquiries":    all_inquiries,
        "all_reviews":      all_reviews,
        "inbox_messages":   inbox_messages,
        "unread_count":     inbox_messages.filter(is_read=False).count(),
        "pending_count":    pending_count,
        "confirmed_count":  confirmed_count,
        "house_form":       BoardingHouseForm(),
        "reply_form":       InquiryReplyForm(),
        "message_form":     MessageForm(),
    })


@login_required
def add_room(request, house_pk):
    forbidden = _require_landlord(request)
    if forbidden:
        return forbidden

    house = get_object_or_404(
        BoardingHouse,
        pk=house_pk,
        user_assignments__user=request.user,
        user_assignments__assigned_role="landlord",
    )

    if request.method != "POST":
        return redirect("landlord_dashboard")

    form = RoomForm(request.POST)
    if form.is_valid():
        room = form.save(commit=False)
        room.boarding_house = house
        room.save()
        messages.success(request, f"Room {room.room_number} added to {house.house_name}.")
    else:
        messages.error(request, "Invalid room details. Please try again.")

    return redirect("landlord_dashboard")


@login_required
def update_reservation_status(request, pk):
    forbidden = _require_landlord(request)
    if forbidden:
        return forbidden

    reservation = get_object_or_404(Reservation, pk=pk)
    owns = UserBoardingHouse.objects.filter(
        user=request.user,
        boarding_house=reservation.room.boarding_house,
        assigned_role="landlord",
    ).exists()
    if not owns:
        return HttpResponseForbidden("You don't own this property.")

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in ("Confirmed", "Cancelled", "Completed"):
            old_status = reservation.status
            reservation.status = new_status
            reservation.save()

            # If cancelling, potentially free up the room
            if new_status == "Cancelled":
                other_active = Reservation.objects.filter(
                    room=reservation.room, status__in=("Pending", "Confirmed")
                ).exclude(pk=reservation.pk).exists()
                if not other_active:
                    reservation.room.availability_status = "Available"
                    reservation.room.save(update_fields=["availability_status"])

            messages.success(request, f"Booking #{reservation.pk} marked as {new_status}.")
        else:
            messages.error(request, "Invalid status.")

    return redirect("landlord_dashboard")


@login_required
def reply_inquiry(request, pk):
    forbidden = _require_landlord(request)
    if forbidden:
        return forbidden

    inquiry = get_object_or_404(Inquiry, pk=pk)
    owns = UserBoardingHouse.objects.filter(
        user=request.user,
        boarding_house=inquiry.boarding_house,
        assigned_role="landlord",
    ).exists()
    if not owns:
        return HttpResponseForbidden("You don't own this property.")

    if request.method == "POST":
        form = InquiryReplyForm(request.POST)
        if form.is_valid():
            Message.objects.create(
                sender=request.user,
                recipient=inquiry.user,
                boarding_house=inquiry.boarding_house,
                subject=f"Re: Inquiry about {inquiry.boarding_house.house_name}",
                body=form.cleaned_data["reply"],
            )
            inquiry.status = "Responded"
            inquiry.save()
            messages.success(request, "Reply sent to tenant.")
        else:
            messages.error(request, "Reply cannot be empty.")

    return redirect("landlord_dashboard")


@login_required
def toggle_house_availability(request, pk):
    forbidden = _require_landlord(request)
    if forbidden:
        return forbidden

    house = get_object_or_404(BoardingHouse, pk=pk)
    owns = UserBoardingHouse.objects.filter(
        user=request.user, boarding_house=house, assigned_role="landlord"
    ).exists()
    if not owns:
        return HttpResponseForbidden("You don't own this property.")

    if request.method == "POST":
        house.availability_status = (
            "Available" if house.availability_status == "Not Available" else "Not Available"
        )
        house.save()

    return redirect("landlord_dashboard")


@login_required
def edit_house(request, pk):
    """Landlord edits an existing boarding house they own."""
    forbidden = _require_landlord(request)
    if forbidden:
        return forbidden

    house = get_object_or_404(BoardingHouse, pk=pk)
    owns = UserBoardingHouse.objects.filter(
        user=request.user, boarding_house=house, assigned_role="landlord"
    ).exists()
    if not owns:
        return HttpResponseForbidden("You don't own this property.")

    if request.method == "POST":
        form = BoardingHouseForm(request.POST, request.FILES, instance=house)
        if form.is_valid():
            form.save()
            messages.success(request, f"'{house.house_name}' has been updated.")
        else:
            for errs in form.errors.values():
                for err in errs:
                    messages.error(request, err)

    return redirect("landlord_dashboard")


@login_required
def mark_message_read(request, pk):
    msg = get_object_or_404(Message, pk=pk, recipient=request.user)
    msg.is_read = True
    msg.save()
    role = getattr(getattr(request.user, "profile", None), "role", "tenant")
    return redirect("landlord_dashboard" if role == "landlord" else "dashboard")
