# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils import timezone
from django.db import models

class SampleModel(models.Model):
    title = models.CharField(max_length=30)
    created = models.DateTimeField(default=timezone.now)
    sequence = models.IntegerField(default=0)
    
    def to_json(self, **kwargs):
        return {
        	'id': self.id,
            'title': self.title,
            'created': self.created,
            'sequence': self.sequence,
        }