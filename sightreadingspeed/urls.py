from django.urls import path

from . import views

app_name = "sightreadingspeed"

urlpatterns = [
    path("", views.index, name="index"),
]
