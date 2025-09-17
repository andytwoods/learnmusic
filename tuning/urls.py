# ruff: noqa
from django.urls import path


from . import views

urlpatterns = [
    # Test JS URL
    path('tuning/', views.tuning, name='tuning'),



]
