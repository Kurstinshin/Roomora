from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q

from .forms import LoginForm, RegisterForm
from listings.models import BoardingHouse, Inquiry, Message, Reservation


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


def _seed_default_listings():
    if not BoardingHouse.objects.filter(is_active=True).exists():
        BoardingHouse.objects.bulk_create([
            BoardingHouse(
                house_name="Room A",
                address="Cebu City",
                price=4500,
                description="Comfortable boarding house with fast Wi-Fi and easy access to transport.",
                image="images.jpg",
                is_active=True,
            ),
            BoardingHouse(
                house_name="Room B",
                address="Mandaue City",
                price=5000,
                description="Clean and cozy boarding house close to malls and restaurants.",
                image="https://via.placeholder.com/640x360?text=Room+B",
                is_active=True,
            ),
        ])


@login_required
def dashboard(request):
    # Landlords go to their own dashboard
    try:
        if request.user.profile.role == "landlord":
            return redirect("landlord_dashboard")
    except Exception:
        pass

    _seed_default_listings()

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
    })


@login_required
def listing_detail(request, pk):
    listing = get_object_or_404(BoardingHouse, pk=pk, is_active=True)
    return render(request, "listings/listing_detail.html", {"listing": listing})
