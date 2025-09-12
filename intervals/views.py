from django.shortcuts import render

# Create your views here.

def attempt_view(request):
    return render(request, "intervals/attempt.html")
