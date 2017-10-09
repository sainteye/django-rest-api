RESTful API framework for Django
=====================================================


Thanks for taking a look at **django-rest-api**! We take pride in having an easy-to-use api solution that works for Django.

## Install

```
pip install https://github.com/sainteye/django-rest-api/tarball/master
```


## Simple Usage for Django Model RESTful API

Add **rest_api** to installed_apps:

**settings.py**

```python
INSTALLED_APPS = [
    ...
    
    'rest_api',
]
```

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
	read_auth_exempt = True

```

Add request path to **urls.py**:

**urls.py**

```python
from django.conf.urls import url
from django.contrib import admin

from sample_app.handlers import IndexHandler
from rest_api.resources import BaseResource

urlpatterns = [
  url(r'^admin/', admin.site.urls),
  url(r'^api/sample_model/', BaseResource(handler=IndexHandler)),
]
```

Create an object to your Django database (run in **./manage.py shell**):

```python
>>> from sample_app.models import SampleModel
>>> SampleModel(sequence=123, title="Sample Title").save()
>>> SampleModel(sequence=777, title="Another Title").save()
```

Make a http request to **/api/sample_model/**

You will get your first api response:

```json
{
  "info": {},
  "data": [
    {
      "title": "Sample Title",
      "sequence": 123,
      "id": 1,
      "created": 1507528440
    },
    {
      "title": "Another Title",
      "sequence": 777,
      "id": 2,
      "created": 1507528451
    }
  ],
  "success": true
}
```

**created** is the timestamp you create your object.

## IndexHandler & ObjectHandler

For RESTful api, basically we have two different type resources. One is for collection resource, another one is for any single object in the collection.


### IndexHandler: 
IndexHandler is designed for **collection resource**. When you make a GET request to url like **/api/:collection/**, it will return collection objects. If you make a POST request to **/api/:collection/**, it will create an object to this collection.

#### GET /api/:collection/
The api should return your collection objects. For GET only collection api, your **handlers.py** file should look like this:

```python
from rest_api.handler import BaseIndexHandler
from sample_app.models import SampleModel

class IndexHandler(BaseIndexHandler):
	allowed_methods = ('GET', )
	query_model = SampleModel
	read_auth_exempt = True
```

set attribute **read\_auth\_exempt = True** to ensure anonymous users can access this resource. Otherwise, only loggined users can access this resource.


#### POST /api/:collection/
When you make a POST request to this api, it should **create an object** to this collection. You have to implement ``create`` method and add `'POST'` to handler `allowed_methods`. Now, your **handlers.py** file should look like this:

```python
from rest_api.handler import BaseIndexHandler
from sample_app.models import SampleModel

class IndexHandler(BaseIndexHandler):
	allowed_methods = ('GET', 'POST')
	query_model = SampleModel
	read_auth_exempt = True

	# for POST function
	create_kwargs = ('title', 'sequence')
	required_fields = ('title', )
	create_auth_exempt = False

	def create(self, request, **kwargs):
		title = request.CLEANED['title']
		sequence = request.CLEANED['sequence']
		sample_obj = SampleModel(title=title, sequence=sequence)
		sample_obj.save()

		return sample_obj.to_json()
```

`create_kwargs` defines what POST data will be passed into `create` method. You can access these data in `request.CLEANED`, it is a dictionary just like **"request.GET/request.POST"** in native django Request object. `required_fields` defines what POST data **must** be specified by request. If a user did not specify the data content for fields in `required_fields`, api will return **"400 Bad Request"**. 

Basically, users have to login your service to create an object. Therefore, by default we should set `create_auth_exempt = False`.

If you are using the sample project, you can login here
**[local django admin](http://localhost:8000/admin/)** with User / Password: **superuser** / **sup12345** .

Good request (will create an object):

`POST /api/sample_model/ title="New Title" sequence="789"`
`POST /api/sample_model/ title="Another New Title"`

Bad request (will **NOT** create an object and will return **"400 Bad Request"**):

`POST /api/sample_model/ sequence="789"`

```json
{
    "success": false,
    "error": {
        "debug": "'title' is missing in params.",
        "message": "Method signature does not match.",
        "code": 10001
    }
}
```

TODO: link to error handling section

### ObjectHandler: 
ObjectHandler is designed for getting, updating or deleting an **object resource**. 

#### GET: Getting an object

When you make a GET request to url like **/api/:collection/:object_id/**, it will simply return the object matching the **object\_id**. For example, if you make a request:

`GET /api/sample_model/1/`

you will get the SampleModel object with id = 1:

```json
{
  "id": 1,
  "title": "Sample Title",
  "sequence": 123,
  "created": 1507528440
}
```


and your **handlers.py** file should look like this:

```python
from rest_api.handler import BaseObjectHandler
from sample_app.models import SampleModel

class ObjectHandler(BaseObjectHandler):
	allowed_methods = ('GET', )
	query_model = SampleModel
	read_auth_exempt = True
```

#### POST: Updating an object

When you make a POST request to url **/api/:collection/:object_id/**, you can update the data of the specific object matching **object\_id**. For example if you want to update the **sequence** field for object with id 2, you can make a POST request like this:

`POST /api/sample_model/2/ sequence="555"`

the api will update the sequence field for object with id = 2:

```json
{
  "id": 2,
  "title": "Another Title",
  "sequence": 555,
  "created": 1507528451
}
```

and your **handlers.py** file should look like this:

```
from rest_api.handler import BaseObjectHandler
from rest_api.utils import process_integer

from sample_app.models import SampleModel

class ObjectHandler(BaseObjectHandler):
	allowed_methods = ('GET', 'POST')
	query_model = SampleModel
	read_auth_exempt = True

	create_kwargs = ('title', 'sequence')
	form_fields = ('title', 'sequence')
	update_instead_save = True

	def create_validate(self, query_dict, **kwargs):
		process_integer(query_dict, ['sequence'])

```

#### /api/:collection/:object_id/




## Runnable Django Example Project
A full example is in **django_example** folder. After download, do:

**Install django-rest-api (best in a virtual env):**

```pip install -r requirements.txt```

**Runserver:**

```./manage.py runserver```

**Open [http://localhost:8000/api/sample_model/](http://localhost:8000/api/sample_model/) :**

You will get a sample response from your db (sample object already in db.sqlite3):
![](https://c1.staticflickr.com/5/4503/36876707014_0006f7768a.jpg)

Try to add new object to your database and see api response change.


