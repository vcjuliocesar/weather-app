from django.shortcuts import render
from django.views.generic.base import TemplateView
# Create your views here.
class HomePageView(TemplateView):
    template_name = "main/home.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #context[""] = 
        return context
    