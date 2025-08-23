from django.urls import path
from . import views


app_name = 'core'


urlpatterns = [
    path('', views.home, name='home'),
    path("download/", views.download_proxy, name="download"),
    path("play-proxy/", views.play_proxy, name="play"),
    path('about/', views.about, name='about'), 
    path('contact', views.contact, name='contact'),
]