from django.shortcuts import render

# Create your views here.
def tuning(request):
    context = {}
    return render(request, template_name='tuning/tuning.html', context=context)
