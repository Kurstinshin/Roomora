import datetime
from django import forms
from django.core.exceptions import ValidationError

from .models import BoardingHouse, BoardingHousePhoto, Room


class ReservationForm(forms.Form):
    """
    Simple room hold — tenant picks a room and a move-in date.
    Month-to-month, no checkout date required.
    """
    room_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    move_in_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Intended Move-in Date",
    )

    def clean_move_in_date(self):
        date = self.cleaned_data.get("move_in_date")
        if date and date < datetime.date.today():
            raise forms.ValidationError("Move-in date cannot be in the past.")
        return date


class BookingForm(forms.Form):
    """
    Fixed-period booking — tenant picks a room, check-in and check-out dates,
    with optional notes. A total amount is computed from the duration.
    """
    room_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    check_in_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Check-in Date",
    )
    check_out_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Check-out Date",
    )
    notes = forms.CharField(
        required=False,
        label="Special Requests (optional)",
        widget=forms.Textarea(attrs={
            "rows": 2,
            "placeholder": "e.g. I'll arrive late evening, need extra blankets…",
        }),
        max_length=1000,
    )

    def clean(self):
        cleaned   = super().clean()
        check_in  = cleaned.get("check_in_date")
        check_out = cleaned.get("check_out_date")
        today     = datetime.date.today()

        if check_in and check_in < today:
            self.add_error("check_in_date", "Check-in date cannot be in the past.")
        if check_in and check_out:
            if check_out <= check_in:
                self.add_error("check_out_date", "Check-out must be after check-in.")
        return cleaned


class InquiryForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), max_length=2000)


class InquiryReplyForm(forms.Form):
    reply = forms.CharField(
        label="Your reply",
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Type your reply…"}),
        max_length=2000,
    )


class ReviewForm(forms.Form):
    rating = forms.IntegerField(min_value=1, max_value=5)
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        max_length=2000,
    )


class BoardingHouseForm(forms.ModelForm):
    class Meta:
        model = BoardingHouse
        fields = ["house_name", "address", "description", "price", "image"]
        widgets = {
            "house_name": forms.TextInput(attrs={"placeholder": "e.g. Sunrise Boarding House"}),
            "address": forms.TextInput(attrs={"placeholder": "Full address"}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Describe the boarding house"}),
            "price": forms.NumberInput(attrs={"min": 1, "placeholder": "Monthly price"}),
            "image": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ["room_number", "room_type", "capacity", "price", "availability_status"]
        widgets = {
            "room_number": forms.TextInput(attrs={"placeholder": "e.g. 101"}),
            "capacity": forms.NumberInput(attrs={"min": 1, "placeholder": "Max occupants"}),
            "price": forms.NumberInput(attrs={"min": 1, "placeholder": "Monthly price"}),
        }


class RoomEditForm(forms.ModelForm):
    """Landlord quick-edit: change availability status, available_from date, and basic room details."""
    class Meta:
        model = Room
        fields = ["room_number", "room_type", "capacity", "price", "availability_status", "available_from"]
        widgets = {
            "availability_status": forms.Select(),
            "available_from": forms.DateInput(attrs={"type": "date"}),
        }



class MessageForm(forms.Form):
    recipient_id = forms.IntegerField(widget=forms.HiddenInput())
    boarding_house_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    subject = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Subject (optional)"}),
    )
    body = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": "Write your message…"}),
        max_length=3000,
    )


class BoardingHousePhotoForm(forms.ModelForm):
    """Upload additional photos for a boarding house gallery."""
    class Meta:
        model = BoardingHousePhoto
        fields = ["image", "caption"]
        widgets = {
            "image": forms.ClearableFileInput(attrs={"accept": "image/*"}),
            "caption": forms.TextInput(attrs={"placeholder": "Optional caption (e.g. Living room)"}),
        }


class InquiryReplyForm(forms.Form):
    """Tenant or landlord reply within an inquiry thread."""
    body = forms.CharField(
        label="Your reply",
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Type your reply…"}),
        max_length=2000,
    )
