from django import forms


class ReservationForm(forms.Form):
    check_in_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))


class InquiryForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), max_length=2000)


class ReviewForm(forms.Form):
    rating = forms.IntegerField(min_value=1, max_value=5)
    comment = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}), max_length=2000)
