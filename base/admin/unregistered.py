from django.contrib import admin
from django.contrib.auth.models import Group


from django_celery_results.models import TaskResult, GroupResult
from django_celery_beat.models import (
    ClockedSchedule,
    CrontabSchedule,
    IntervalSchedule,
    SolarSchedule,
    PeriodicTask,
)

# Unregister django_celery_beat models
admin.site.unregister(ClockedSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(SolarSchedule)
admin.site.unregister(PeriodicTask)

# Unregister django_celery_results models
admin.site.unregister(TaskResult)
admin.site.unregister(GroupResult)

admin.site.unregister(Group)
