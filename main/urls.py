from django.urls import path
from .views import HomePageView, SearchView, WeatherDataView

app_name = "weather"
urlpatterns = [
    path("",HomePageView.as_view(),name="home"),
    path("search/",SearchView.as_view(),name="search"),
    path("api/weather/",WeatherDataView.as_view(),name="api_weather"),
]
