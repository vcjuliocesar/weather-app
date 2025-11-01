from urllib import response
import requests
from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.conf import settings
# Create your views here.

API = settings.API
API_TOKEN = settings.API_TOKEN
#{'coord': {'lon': -98.9, 'lat': 19.2667}, 'weather': [{'id': 803, 'main': 'Clouds', 'description': 'broken clouds', 'icon': '04n'}], 'base': 'stations', 'main': {'temp': 21.98, 'feels_like': 21.17, 'temp_min': 21.66, 'temp_max': 21.98, 'pressure': 1015, 'humidity': 36, 'sea_level': 1015, 'grnd_level': 749}, 'visibility': 10000, 'wind': {'speed': 1.68, 'deg': 155, 'gust': 2.02}, 'clouds': {'all': 58}, 'dt': 1761956533, 'sys': {'type': 1, 'id': 7146, 'country': 'MX', 'sunrise': 1761914151, 'sunset': 1761955344}, 'timezone': -21600, 'id': 3531200, 'name': 'Chalco', 'cod': 200}
class HomePageView(TemplateView):
    template_name = "main/home.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        city = 'chalco'
        country = 'mexico'
        r = requests.get(f"{API}data/2.5/weather?q={city},{country}&appid={API_TOKEN}").json()
        if r.get('cod') == 200:
            weather_data = {
                'city':r['name'],
                'temp':r['main']['temp'],
                'description':r['weather'][0]['description'],
                'country':r['sys']['country'],
                'humidity':r['main']['humidity'],
                'wind_speed':r['wind']['speed']
            }
        print(weather_data)
        context["weather_data"] = weather_data
        return context
    
    def get_geo(self,city:str):
        r = requests.get(f"{API}geo/1.0/direct?q={city}&appid={API_TOKEN}")
        
        if r.status_code == 200:
            info = r.json()
        return ([info[0]['lat'],info[0]['lon']])
        
    