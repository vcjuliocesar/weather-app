from django import forms
from .models import City

class SearchForm(forms.Form):
    city = forms.CharField(
        max_length=120,
        label="City",
        required=True,
        widget=forms.TextInput(attrs={"placeholder":"Enter city...","autocomplete":"off"})
    )
    country = forms.ChoiceField(
        label="Country",
        required=True,
        choices=[]
    )
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        country = (City.objects.values_list('country',flat=True).distinct().order_by('country'))
        self.fields['country'].choices = [("", "- Select country -")] + [(c,c) for c in country if c] 
        self.fields["country"].initial = "MX"
        
    def clean_city(self):
        city = (self.cleaned_data.get('city') or "").strip()
        
        if not city:
            raise forms.ValidationError("City is required.")
        
        qs = City.objects.filter(name__iexact=city)
        
        if not qs.exists():
            raise forms.ValidationError("City not found.")
        
        return city
    
    def clean(self):
        cleaned_data = super().clean()
        city = cleaned_data.get("city")
        country = cleaned_data.get("country")
        
        if city and country:
            exists = City.objects.filter(name__iexact=city, country__iexact=country).exists()
            if not exists:
                raise forms.ValidationError("The specified city does not exist in the selected country.")
        
        return cleaned_data