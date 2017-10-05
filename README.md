Django RESTful API. A RESTful api framework for Django
=====================================================


Thanks for taking a look at **django-rest-api**! We take pride in having an easy-to-use api solution that works for Django.

## Simple Usage for Django Model RESTful API

Implement **to_json** method for your Django model:

**sample_app/models.py**

```python
from django.utils import timezone
from django.db import models

class SampleModel(models.Model):
    title = models.CharField(max_length=30)
    created = models.DateTimeField(default=timezone.now)
    sequence = models.IntegerField(default=0)
    
    def to_json(self, **kwargs):
        return {
            'title': self.title,
            'created': self.created,
            'sequence': self.sequence,
        }

```

Create **handlers.py** file for your Django model:

**sample_app/handlers.py**

```python
from rest_api.handler import BaseIndexHandler
from sample_app.models import SampleModel

class IndexHandler(BaseIndexHandler):
	allowed_methods = ('GET', ) 
	query_model = SampleModel
```

Add request path to **urls.py**:

**urls.py**

```python
from django.conf.urls import url
from django.contrib import admin

from django.conf.urls import include

from rest_api.resources import BaseResource

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/sample_model/', BaseResource(handler=IndexHandler)),
]
```

Create a model to your django database:

```python
from sample_app.models import SampleModel
SampleModel(sequence=123, title="I am a Sample").save()
```

Make a http request to **/api/sample_model/**

You will get your first api response:

```json
{
   "info": {}, 
   "response": [
      {
         "sequence": 123, 
         "title": "I am a Sample", 
         "created": 1507145600.0
      }
   ], 
   "success": true
}
```
