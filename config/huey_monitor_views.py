from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path
from django.views.generic import RedirectView

# In django-huey-monitor 0.10.1, there is no urls module to import
# Instead, huey-monitor is integrated with the Django admin interface
# We'll create a simple redirect to the admin interface for the huey-monitor URLs

urlpatterns = [
    # Redirect to the TaskModel admin page
    path('', staff_member_required(RedirectView.as_view(
        pattern_name='admin:huey_monitor_taskmodel_changelist'
    ))),

    # Redirect to the SignalInfoModel admin page
    path('signals/', staff_member_required(RedirectView.as_view(
        pattern_name='admin:huey_monitor_signalinfomodel_changelist'
    ))),
]
