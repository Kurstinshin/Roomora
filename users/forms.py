from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile

class RegisterForm(UserCreationForm):
    username = forms.CharField(
        required=True,
        label="Username",
        widget=forms.TextInput(attrs={"placeholder": "Username"}),
        error_messages={
            "required": "Username is required.",
        },
    )
    first_name = forms.CharField(
        required=True,
        label="First Name",
        widget=forms.TextInput(attrs={"placeholder": "First Name"}),
        error_messages={
            "required": "Required fields cannot be empty.",
        },
    )
    last_name = forms.CharField(
        required=True,
        label="Last Name",
        widget=forms.TextInput(attrs={"placeholder": "Last Name"}),
        error_messages={
            "required": "Required fields cannot be empty.",
        },
    )
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "Email"}),
        error_messages={
            "required": "Required fields cannot be empty.",
            "invalid": "Invalid email.",
        },
    )
    contact_number = forms.CharField(
        required=False,
        label="Contact Number",
        widget=forms.TextInput(attrs={"placeholder": "Contact Number"}),
    )
    role = forms.ChoiceField(
        required=True,
        choices=Profile.ROLE_CHOICES,
        label="Role",
        error_messages={
            "required": "Required fields cannot be empty.",
        },
    )

    password1 = forms.CharField(
        label="Password",
        strip=False,
        min_length=8,
        widget=forms.PasswordInput(attrs={"placeholder": "Password"}),
        error_messages={
            "required": "Password is required.",
            "min_length": "Password is too short.",
        },
    )
    password2 = forms.CharField(
        label="Confirm Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"placeholder": "Confirm Password"}),
        error_messages={
            "required": "Password is required.",
        },
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "password1", "password2"]
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Username"}),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            Profile.objects.create(
                user=user,
                contact_number=self.cleaned_data.get("contact_number", ""),
                role=self.cleaned_data.get("role", "tenant"),
            )
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "Email"}),
    )
    password = forms.CharField(
        required=True,
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"placeholder": "Password"}),
    )


class ProfileEditForm(forms.Form):
    """Edit User + Profile in a single form."""
    first_name = forms.CharField(
        required=False,
        label="First Name",
        widget=forms.TextInput(attrs={"placeholder": "First name"}),
    )
    last_name = forms.CharField(
        required=False,
        label="Last Name",
        widget=forms.TextInput(attrs={"placeholder": "Last name"}),
    )
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "Email address"}),
    )
    contact_number = forms.CharField(
        required=False,
        label="Contact Number",
        widget=forms.TextInput(attrs={"placeholder": "+63 9XX XXX XXXX"}),
    )
    bio = forms.CharField(
        required=False,
        label="Bio",
        widget=forms.Textarea(attrs={"placeholder": "Tell others a little about yourself…", "rows": 3}),
        max_length=500,
    )
    profile_photo = forms.ImageField(
        required=False,
        label="Profile Photo",
        widget=forms.ClearableFileInput(attrs={"accept": "image/*"}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = user

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if self._user and User.objects.filter(email__iexact=email).exclude(pk=self._user.pk).exists():
            raise forms.ValidationError("This email is already in use by another account.")
        return email