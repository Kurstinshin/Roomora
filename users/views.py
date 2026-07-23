from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q

from .forms import LoginForm, ProfileEditForm, RegisterForm
from listings.models import BoardingHouse, Favorite, Inquiry, Message, Notification, Reservation


def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("login")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully. Please log in.")
            return redirect("login")
        messages.error(request, "Please fill in all required fields.")
    else:
        form = RegisterForm()

    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                messages.error(request, "Account does not exist.")
                return render(request, "users/login.html", {"form": form})

            authenticated_user = authenticate(request, username=user.username, password=password)
            if authenticated_user is not None:
                login(request, authenticated_user)
                messages.success(request, "Welcome to Roomora!")
                next_url = request.GET.get("next")
                if next_url:
                    return redirect(next_url)
                return redirect("dashboard")
            messages.error(request, "Incorrect email or password.")
    else:
        form = LoginForm()

    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("login")


@login_required
def dashboard(request):
    # Landlords go to their own dashboard
    try:
        if request.user.profile.role == "landlord":
            return redirect("landlord_dashboard")
    except Exception:
        pass

    listings = BoardingHouse.objects.filter(is_active=True)
    search = request.GET.get("search", "").strip()
    location = request.GET.get("location", "").strip()
    price_filter = request.GET.get("price", "").strip()

    if search:
        listings = listings.filter(
            Q(house_name__icontains=search)
            | Q(description__icontains=search)
            | Q(address__icontains=search)
        )

    if location:
        listings = listings.filter(address__icontains=location)

    if price_filter:
        try:
            max_price = int(price_filter)
            listings = listings.filter(price__lte=max_price)
        except ValueError:
            messages.error(request, "Invalid price filter.")

    locations = (
        BoardingHouse.objects.filter(is_active=True)
        .order_by("address")
        .values_list("address", flat=True)
        .distinct()
    )

    # Tenant-specific data
    my_reservations = Reservation.objects.filter(
        user=request.user
    ).select_related("room", "room__boarding_house").order_by("-reservation_date")

    my_inquiries = Inquiry.objects.filter(
        user=request.user
    ).select_related("boarding_house").order_by("-date_sent")

    inbox_messages = Message.objects.filter(
        recipient=request.user
    ).select_related("sender", "boarding_house").order_by("-sent_at")

    unread_count = inbox_messages.filter(is_read=False).count()

    # Favorites
    fav_ids = set(
        Favorite.objects.filter(user=request.user).values_list("boarding_house_id", flat=True)
    )
    fav_listings = BoardingHouse.objects.filter(
        pk__in=fav_ids, is_active=True
    ).prefetch_related("rooms")

    # Notifications
    notif_unread = Notification.objects.filter(user=request.user, is_read=False).count()
    recent_notifs = Notification.objects.filter(user=request.user).order_by("-created_at")[:8]

    return render(request, "users/dashboard.html", {
        "listings": listings,
        "search": search,
        "location": location,
        "price_filter": price_filter,
        "locations": locations,
        "my_reservations": my_reservations,
        "my_inquiries": my_inquiries,
        "inbox_messages": inbox_messages,
        "unread_count": unread_count,
        "fav_ids": fav_ids,
        "fav_listings": fav_listings,
        "notif_unread": notif_unread,
        "recent_notifs": recent_notifs,
    })


@login_required
def profile_edit(request):
    """Edit the logged-in user's profile details."""
    user = request.user
    try:
        profile = user.profile
    except Exception:
        from users.models import Profile
        profile = Profile.objects.create(user=user)

    if request.method == "POST":
        form = ProfileEditForm(request.POST, request.FILES, user=user)
        if form.is_valid():
            user.first_name = form.cleaned_data["first_name"]
            user.last_name = form.cleaned_data["last_name"]
            user.email = form.cleaned_data["email"]
            user.save()

            profile.contact_number = form.cleaned_data.get("contact_number", "")
            profile.bio = form.cleaned_data.get("bio", "")
            if form.cleaned_data.get("profile_photo"):
                profile.profile_photo = form.cleaned_data["profile_photo"]
            profile.save()

            messages.success(request, "Profile updated successfully.")
            return redirect("profile_edit")
        else:
            for errs in form.errors.values():
                for err in errs:
                    messages.error(request, err)
    else:
        form = ProfileEditForm(
            user=user,
            initial={
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "contact_number": profile.contact_number,
                "bio": profile.bio,
            },
        )

    notif_unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(request, "users/profile_edit.html", {
        "form": form,
        "profile": profile,
        "notif_unread": notif_unread,
    })


@login_required
def booking_detail(request, pk):
    """Tenant's detailed view of a single reservation."""
    reservation = get_object_or_404(Reservation, pk=pk, user=request.user)
    notif_unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(request, "users/booking_detail.html", {
        "reservation": reservation,
        "notif_unread": notif_unread,
    })


