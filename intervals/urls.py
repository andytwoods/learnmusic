from django.urls import path

from . import views

urlpatterns = [
    path("", views.attempt_view, name="attempt"),

]
