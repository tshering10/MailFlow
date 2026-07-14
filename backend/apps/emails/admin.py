from django.contrib import admin

# Register your models here.
from .models import EmailSchedule, TaskLog

admin.site.register(EmailSchedule)
admin.site.register(TaskLog)
