import asyncio
from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.views.generic.base import FormView,TemplateView
from django.views.decorators.http import require_GET
from django.utils.decorators import method_decorator
from .forms import SearchForm
from .models import City, Search
from .services import fetch_weather
# Create your views here.


class HomePageView(TemplateView):
    template_name = "main/search.html"
    

class SearchView(TemplateView):
    template_name = "main/search.html"
    form_class = SearchForm
    
    
    def form_valid(self, form):
        city = form.cleaned_data.get("city")
        country = form.cleaned_data.get("country")
        
        Search.objects.create(
            query=f"{city},{country}",
            ip=self.request.META.get("REMOTE_ADDR"),
        )
        
        return self.render_to_response(self.get_context_data(city=city, country=country))
    
@method_decorator(require_GET, name='dispatch')
class WeatherDataView(TemplateView):
    
    def get(self,request,*args,**kwargs):
        city = request.GET.get("city")
        country = request.GET.get("country")
        
        if not city or not country:
            raise Http404("Missing city")
        
        data = asyncio.run(fetch_weather(city,country))
        return JsonResponse({
            "city": data.city,
            "country": data.country,
            "current": data.current,
        })