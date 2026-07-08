from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import BoardingHouse, Room
from .forms import ReservationForm, InquiryForm, ReviewForm


def listing_detail(request, pk):
    listing = get_object_or_404(BoardingHouse, pk=pk, is_active=True)
    reservation_form = ReservationForm()
    inquiry_form = InquiryForm()
    review_form = ReviewForm()

    return render(
        request,
        "listings/listing_detail.html",
        {
            "listing": listing,
            "reservation_form": reservation_form,
            "inquiry_form": inquiry_form,
            "review_form": review_form,
        },
    )


@login_required
def make_reservation(request, pk):
    listing = get_object_or_404(BoardingHouse, pk=pk, is_active=True)
    if request.method != "POST":
        return redirect("listing_detail", pk=pk)

    form = ReservationForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Invalid reservation data.")
        return redirect("listing_detail", pk=pk)

    # find a first available room in the boarding house
    room = listing.rooms.filter(availability_status="Available").first()
    if not room:
        messages.error(request, "No available rooms for this boarding house.")
        return redirect("listing_detail", pk=pk)

    check_in_date = form.cleaned_data["check_in_date"]

    # create reservation
    from .models import Reservation

    Reservation.objects.create(user=request.user, room=room, check_in_date=check_in_date)
    messages.success(request, "Reservation created successfully.")
    return redirect("listing_detail", pk=pk)


@login_required
def send_inquiry(request, pk):
    listing = get_object_or_404(BoardingHouse, pk=pk, is_active=True)
    if request.method != "POST":
        return redirect("listing_detail", pk=pk)

    form = InquiryForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Invalid inquiry data.")
        return redirect("listing_detail", pk=pk)

    message = form.cleaned_data["message"]
    from .models import Inquiry

    Inquiry.objects.create(user=request.user, boarding_house=listing, message=message)
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

    rating = form.cleaned_data["rating"]
    comment = form.cleaned_data.get("comment", "")
    from .models import Review

    Review.objects.create(user=request.user, boarding_house=listing, rating=rating, comment=comment)
    messages.success(request, "Thanks — your review has been submitted.")
    return redirect("listing_detail", pk=pk)


@login_required
def landlord_dashboard(request):
    # Only allow users with landlord profile
    try:
        if request.user.profile.role != "landlord":
            from django.http import HttpResponseForbidden

            return HttpResponseForbidden("Forbidden")
    except Exception:
        from django.http import HttpResponseForbidden

        return HttpResponseForbidden("Forbidden")

    houses = BoardingHouse.objects.filter(user_assignments__user=request.user, user_assignments__assigned_role="landlord").distinct()

    # gather counts
    data = []
    for h in houses:
        reservations = h.rooms.aggregate(total_reservations=models.Count('reservations'))['total_reservations']
        inquiries = h.inquiries.count()
        reviews = h.reviews.count()
        data.append({
            'house': h,
            'reservations': reservations,
            'inquiries': inquiries,
            'reviews': reviews,
        })

    return render(request, 'listings/landlord_dashboard.html', {'houses': data})


@login_required
def toggle_house_availability(request, pk):
    # toggle availability_status between Available/Not Available
    house = get_object_or_404(BoardingHouse, pk=pk)
    # ensure landlord
    try:
        if request.user.profile.role != "landlord":
            from django.http import HttpResponseForbidden

            return HttpResponseForbidden("Forbidden")
    except Exception:
        from django.http import HttpResponseForbidden

        return HttpResponseForbidden("Forbidden")

    if request.method == 'POST':
        house.availability_status = 'Available' if house.availability_status == 'Not Available' else 'Not Available'
        house.save()
    return redirect('landlord_dashboard')
