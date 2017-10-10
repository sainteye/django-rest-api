"""api_example URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin

from globals.api_resources import Resource
from rest_api.resources import BaseResource
from sample_app.handlers import IndexHandler, ObjectHandler, SampleHandler

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    # Apis using BaseResource will not email unexpected error.
    url(r'^api/sample_model/$', BaseResource(handler=IndexHandler)),
    url(r'^api/sample_model/(?P<object_id>\w+)/$', BaseResource(handler=ObjectHandler)),

    # Only this api calls your customize "Resource" method "email_exception"
    url(r'^api/sample/$', Resource(handler=SampleHandler)),
]
