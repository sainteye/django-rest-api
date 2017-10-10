RESTful API framework for Django
=====================================================


Thanks for taking a look at **django-rest-api**! We take pride in having an easy-to-use api solution that works for Django. 

This framework is based on [django-piston](https://pypi.python.org/pypi/django-piston/0.2.3) (but basically they are very different). It should work for Django version greater than `Django==1.11.5`.

# Documentation
- [High-Level Concept](#high-level-concept)
- [Handler Structure](#handler-structure)
- [API Utils](#api-utils)


## Simple Usage for Django RESTful API

To install django-rest-api, simply use pip:

```
pip install https://github.com/sainteye/django-rest-api/tarball/master
```

Then add `'rest_api'` to your Django `INSTALLED_APPS`:

**settings.py**

```python
INSTALLED_APPS = [
    ...
    
    'rest_api',
]
```

Implement `to_json` method for your Django model:

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
      'id': self.id,
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

Create an object to your Django database (run in `./manage.py shell`):

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
  ]
}
```

(**created** is the timestamp of the creation time of your objects.)


# High-Level Concept

For RESTful api, basically we have two different type resources. One is for collection resource, another one is for any single object in the collection.


## IndexHandler - Collection Resource

### URL /api/:collection/

**Sample Response Structure**

```json
{
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
  "info": {}
}
```

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

set attribute `read_auth_exempt = True` to ensure anonymous users can access this resource. Otherwise, only loggined users can access this resource.


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

Basically, users have to login your service to create an object. Therefore, by default we should set `create_auth_exempt = False`. If you set `create_auth_exempt = False` and you have not loggined your api server, you will get **"401 Unauthorized"**:

```json
{
    "error": {
        "message": "Authentication required.",
        "code": 10100
    }
}

```

If you are using our sample project, then you can login by enter
**[local django admin](http://localhost:8000/admin/)** with User / Password: **superuser** / **sup12345** .

Here are some Good requests (will create an object):

`POST /api/sample_model/ title="New Title" sequence="789"`

`POST /api/sample_model/ title="Another New Title"`

Below is a Bad request (will **NOT** create an object and will return **"400 Bad Request"**):

`POST /api/sample_model/ sequence="789"`

```json
{
    "error": {
        "debug": "'title' is missing in params.",
        "message": "Method signature does not match.",
        "code": 10001
    }
}
```

TODO: link to error handling section

## ObjectHandler - Object Resource

### URL /api/:collection/:object_id/

**Sample Response Structure**

```json
{
  "id": 1,
  "title": "Sample Title",
  "sequence": 123,
  "created": 1507528440
}
```

ObjectHandler is designed for getting, updating or deleting an **object resource**. 

#### GET: Getting an object

When you make a GET request to url like **/api/:collection/:object_id/**, it will simply return the object matching the given **object\_id**. For example, if you make a request:

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


to get this response, your **handlers.py** file might look like this:

```python
from rest_api.handler import BaseObjectHandler
from sample_app.models import SampleModel

class ObjectHandler(BaseObjectHandler):
  allowed_methods = ('GET', )
  query_model = SampleModel
  read_auth_exempt = True
```

and you have to update your **urls.py** to pass `object_id` into ObjectHandler:

**urls.py**

```python
from django.conf.urls import url
from django.contrib import admin

from sample_app.handlers import IndexHandler, ObjectHandler
from rest_api.resources import BaseResource

urlpatterns = [
  url(r'^admin/', admin.site.urls),
  url(r'^api/sample_model/$', BaseResource(handler=IndexHandler)),
  url(r'^api/sample_model/(?P<object_id>\w+)/$', BaseResource(handler=ObjectHandler)),
]
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

your **handlers.py** file should look like this:

```python
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

read more in [Handler Structure](#handler-structure)


#### DELETE: Deleting an object

When you make a DELETE request to url **/api/:collection/:object_id/**, you will delete the data of the specific object matching **object\_id**. If you make a DELETE request like this:

`DELETE /api/sample_model/2/`

then the SampleModel object with id 2 will be deleted. All you have to do is add `'DELETE'` to `allowed_methods`: 

`allowed_methods = ('GET', 'POST', 'DELETE')`

Note: for safety concern, by default only loggined users can make a DELETE request. If you want that even anonymous user can make a DELETE request, you can set `delete_auth_exempt = True` for ObjectHandler.

# Handler Structure

## Execute Flow
Basically, a handler can handle three different type request: GET, POST, DELETE. Here is the request method executation flow:

**GET:** `read_validate` -> `read`

**POST:** `create_validate` -> `create`

**DELETE:** `delete_validate` -> `delete`

We use GET request to clarify the request processed flow. In `read_validate`, you can **validate and clean** request data. For GET request, the request data must be defined in `read_kwargs` attribute. **Data not defined in `read_kwargs` will be not accessible.**

In `read_validate` method, request data can be accessed in `query_dict`. You can use functions in `rest_api.utils` to clean and verify reqeust data. For example, `process_integer` can ensure the request data be converted into python integer.

After you validate and clean request data in `read_validate` method, you have to put this data back into `query_dict`. The `query_dict` will be assigned to `request.CLEANED` and can be accessed in the `read` method.

Below is an example, we build a **ConvertDataHandler** for the url **/api/convert_data/**.

```python
from rest_api.handler import BaseHandler
from rest_api.utils import process_integer

class ConvertDataHandler(BaseHandler):
  allowed_methods = ('GET', )
  read_auth_exempt = True  
  read_kwargs = ('title', 'sequence')
    
  def read_validate(self, query_dict, request, **kwargs):
    # Validate GET request
    process_integer(query_dict, ['sequence'])
    title = query_dict.get('title')
    if title == '':
      raise Exception('not a valide title')
    
    clean_title = title.replace('+', '')
    query_dict['clean_title'] = clean_title
    
    inc_sequence = query_dict.get('sequence', 0)
    query_dict['inc_sequence'] = inc_sequence
    
  def read(self, request, **kwargs):
    # Execute GET request
    clean_title = request.CLEANED['clean_title']
    inc_sequence = request.CLEANED['inc_sequence']
    return {'clean_title': clean_title, 'inc_sequence': inc_sequence}
```

Requet:

`GET /api/convert_data/?title=b+i+k+e&sequence=123`

Response:

```json
{
  "clean_title": "bike",
  "inc_sequence": 124
}
```

Note that the request data ***sequence*** has been converted into python integer after `process_integer(query_dict, ['sequence'])`.

## Settings

### General Settings

`allowed_methods`: Allowed request methods: might be a tuple including 'POST', 'GET', 'DELETE'.

`query_model`: model to query. (only work for IndexHandler & ObjectHandler)

### Authentication
`superuser_only`: Only superuser can access this api. Default value is **False**

`read_auth_exempt`, `create_auth_exempt`, `delete_auth_exempt`: Let anonymous users to access GET, POST, DELETE method. Default values are all **False**.


### GET
`read_kwargs`: only the parameters in read_kwargs will be kept. (it should be a superset of required_fields_for_read)

`required_fields_for_read `: parameters required for valid GET request.

`allowed_filter`: only the parameters in allowed_filter will be used as query params. (only work for IndexHandler)

### POST
`create_kwargs`: only the parameters in create_kwargs will be kept. (it should be a superset of required_fields)

`required_fields`: lists the parameters that must be specified.

`form_fields`: only the parameters in form_fields will be updated. (only work for ObjectHandler)

`update_instead_save`: use update() method instead save() for object update. It might cause risk condition if it is set as False. True -> update, False -> save. (only work for ObjectHandler)


### DELETE
`delete_kwargs `: lists the parameters that must be specified. (it 

A full example:

```python
class ExampleHandler(BaseHandler):
  allowed_methods = ('POST', 'GET', 'DELETE')
  
  # For POST:
  required_fields = ('title', )
  create_kwargs = ('title', 'sequence')
  form_fields = ('title', )
  update_instead_save = True

  # For GET:
  required_fields_for_read = ()
  read_kwargs = ('title', 'sequence')
  allowed_filter = ('sequence', )

  # For DELETE:
  delete_kwargs = ()

  query_model = SampleModel
  read_auth_exempt = True
  create_auth_exempt = False
  delete_auth_exempt = False
  
  superuser_only = False
  
```

## Response Returning Format

By default, api will wrap response if it is a python list and will directly return response if it is a python dictionary.

**List format**: if you return `[{"id": 1}, {"id": 2}]`, the response will be

```json
{
  "info": {}
  "data": [
    {"id": 1},
    {"id": 2}
  ]
}
```

**Dictionary format**: if you return `{"id": 1}`, the response will be

```json
{
  "id": 1
}
```

By design, we think an api returning list as its response is more complicated. Therefore, there might be some other infomation it wants to provide to users. For example, pagination timestamp:

```json
{
  "info": {
    "latest_ts": 1507528440
  },
  "data": [
    {"id": 1, "ts": 1507528439},
    {"id": 2, "ts": 1507528440}
  ]
}
```

Who gets this response can use `latest_ts` as a parameter for next request and he will get the next page items.

To return `info`, you can use `wrap_info(response, info)`. Here is an example:

```python
from rest_api.handler import BaseHandler
from rest_api.utils import wrap_info

class SampleResponseHandler(BaseHandler):
  allowed_methods = ('GET', )
  read_auth_exempt = True  
    
  def read(self, request, **kwargs):
    response = [
      {"id": 1, "ts": 1507528439},
      {"id": 2, "ts": 1507528440}
    ]
    info = {
      "latest_ts": 1507528440
    }
    return wrap_info(response, info)
```

If you do not want api to wrap your response, simply set `REST_API_WITH_WRAPPER = False` in your **settings.py**.

If you set `REST_API_WITH_WRAPPER = False`, the api response will directly return your returning value in handler method.

If your handler return: `[{"id": 1},{"id": 2}]`

With `REST_API_WITH_WRAPPER = True`, your response will be

```json
{
  "info": {},
  "data": [
    {"id": 1},
    {"id": 2}
  ]
}
```

with `REST_API_WITH_WRAPPER = False`

```json
[
  {"id": 1},
  {"id": 2}
]
```


# API Utils

In read\_validate, create\_validate method, we should always make sure that request data will be validated, cleaned and converted into specific python type. django-rest-api provides several utils function to complete it. If the data cannot be validated and converted, api will raise Exception with code `ERROR_GENERAL_BAD_PARA_FORMAT`.

Here is the utils list:

`process_integer`: convert data into integer. `'123' -> 123`

`process_boolean`: convert data into boolean. `'true' -> True, '1' -> True, 'True' -> True`

`process_float`: convert data into float. `'3.14159' -> 3.14159`


```python
from rest_api.handler import BaseHandler
from rest_api.utils import process_integer, process_float

class IntegerDataHandler(BaseHandler):
  allowed_methods = ('GET', )
  read_kwargs = ('a_integer', 'b_integer', 'c_integer', 'd_float')
    
  def read_validate(self, query_dict, request, **kwargs):
    # Validate GET request
    process_integer(query_dict, ['a_integer', 'b_integer'])
    print type(query_dict['a_integer'])
    # <type 'int'>
    print type(query_dict['b_integer'])
    # <type 'int'>
    print type(query_dict['c_integer'])
    # <type 'string'>
    process_float(query_dict, ['d_float'])
    print type(query_dict['d_float'])
    # <type 'float'>
    ...
    

```

# Error Handling

TODO:

**globals/api_errors.py**
```
from rest_api.errors import *

ERROR_PROTO_TITLE_ERROR = 20000 #: Proto Model Empty Title Error

IFOODIE_API_ERROR = {
	ERROR_PROTO_TITLE_ERROR: "Proto Model Empty Title Error",
}

API_ERRORS.update(IFOODIE_API_ERROR)
```



## Full Django Example Project
A full example is in **django_example** folder. After download, do:

#### Install django-rest-api (best in a virtual env):

```pip install -r requirements.txt```

#### Runserver:

```./manage.py runserver```

**Open [http://localhost:8000/api/sample_model/](http://localhost:8000/api/sample_model/) :**

You will get a sample response from your db (sample object already in db.sqlite3):
![](https://c1.staticflickr.com/5/4503/36876707014_0006f7768a.jpg)

Try to add new object to your database and see api response change.


