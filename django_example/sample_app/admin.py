# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from models import SampleModel

# Register your models here.
class SampleModelAdmin(admin.ModelAdmin):
    list_display = ['title', 'sequence', 'created']

admin.site.register(SampleModel, SampleModelAdmin)

