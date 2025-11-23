import asyncio
from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.views.generic import FormView,TemplateView
from django.views.decorators.http import require_GET
from django.utils.decorators import method_decorator
from .forms import SearchForm
from .models import City, Search
from .services import fetch_weather
# Create your views here.


class HomePageView(TemplateView):
    template_name = "main/search.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = SearchForm()
        return context
    

class SearchView(FormView):
    template_name = "main/search.html"
    form_class = SearchForm
    
    
    def form_valid(self, form):
        city = form.cleaned_data.get("city")
        country = form.cleaned_data.get("country")
        
        Search.objects.create(
            query=f"{city},{country}",
            ip=self.request.META.get("REMOTE_ADDR"),
        )
        context = self.get_context_data(form=form, city=city, country=country)
        return self.render_to_response(context)
    
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