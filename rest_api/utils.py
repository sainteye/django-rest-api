import time, math
import json
from collections import namedtuple

from datetime import datetime
from django.contrib.auth.models import User
from django.http import QueryDict

import rest_api.errors as api_errors
from rest_api.errors import GlobalAPIException

# New api django_ct
TYPE_LIST = ['Unknown', 'auth.user', ]

TOKEN_LENGTH = 20
DEFAULT_RETURN_NUM = 20
MAX_RETURN_NUM = 300

SysRequest = namedtuple('SysRequest', ['user', 'CLEANED', 'is_iphone', 'is_android', 'META'])


def create_sys_request(user=None, query_dict=None):
    if not query_dict:
        query_dict = QueryDict('', mutable=True)
        query_dict['detail'] = True
        query_dict['offset'], query_dict['limit'] = parse_pagination()
        query_dict['endpoint'] = query_dict['offset'] + query_dict['limit']
        query_dict['order_by'] = None

    if query_dict.get('limit') is None:
        query_dict['offset'], query_dict['limit'] = parse_pagination()
        query_dict['endpoint'] = query_dict['offset'] + query_dict['limit']
        
    sys_request = SysRequest(user=user, CLEANED=query_dict, is_iphone=False, is_android=False, META={})
    return sys_request


def make_sys_request(handler, params, request, method='GET'):
    if method == 'GET':
        _get = QueryDict('', mutable=True)
        for key in params:
            _get[key] = params[key]
        handler.read_validate(_get)
        sys_request = create_sys_request(request.user, handler.map_para(_get))
        response = handler.read(sys_request)
        if type(response) is dict:
            if response.get('_response'):
                return response.get('_response')
        return response
    else:
        raise Exception('Not implement')


def to_json(obj, **kwargs):
    obj = obj.get_profile() if obj.__class__==User else obj
    return obj.to_json(**kwargs) if hasattr(obj, 'to_json') else obj


def process_json(json_str):
    try:
        json_obj = None
        if json_str is not None:
            if type(json_str) == list:
                json_obj = json_str
            elif type(json_str) == dict:
                json_obj = json_str
            else:
                json_obj = json.loads(json_str)

            return json_obj
    except:
        raise GlobalAPIException(api_errors.ERROR_GENERAL_BAD_PARA_FORMAT, 'Not valid json format.')


def process_timestamp(query_dict, process_fields=[]):
    try:
        for field in process_fields:
            if query_dict.get(field)!=None:
               query_dict[field] = datetime.fromtimestamp(float(query_dict[field]))
    except:
        raise GlobalAPIException(api_errors.ERROR_GENERAL_BAD_PARA_FORMAT, 'Not valid timestamp format.')


def process_latlon(latlon, reverse=False):
    if not latlon:
        raise GlobalAPIException(api_errors.ERROR_GENERAL_BAD_SIGNATURE, 'Location information is missing.')

    latlon_list = latlon.split(',')
    if len(latlon_list) != 2:
        raise GlobalAPIException(api_errors.ERROR_GENERAL_BAD_PARA_FORMAT, 'Location format is not valid.')

    try:
        latitude, longitude = map(lambda x:float(x), latlon_list)
    except (TypeError, KeyError):
        raise GlobalAPIException(api_errors.ERROR_GENERAL_BAD_PARA_FORMAT, 'Location format is not valid.')

    if -90>latitude or latitude>90:
        raise GlobalAPIException(api_errors.ERROR_GENERAL_BAD_PARA_FORMAT, 'latitude is out of range. It should be in [-90,90], and it is %s.'% latitude)

    if -180>longitude or longitude>180:
        raise GlobalAPIException(api_errors.ERROR_GENERAL_BAD_PARA_FORMAT, 'longitude is out of range. It should be in [-180,180], and it is %s.'% longitude)

    if math.isnan(latitude) or math.isnan(longitude):
        raise GlobalAPIException(api_errors.ERROR_GENERAL_BAD_PARA_FORMAT, 'Location format is not valid. %s, %s' % (latitude, longitude))

    return (latitude, longitude) if not reverse else (longitude, latitude)


def process_boolean(query_dict, process_fields=[]):
    # boolean is 'true', 'false' or None and will transform into True, False and None
    for field in process_fields:
        if query_dict.get(field) != None:
            query_dict[field] = query_dict[field] in ('true', 'True', '1', True, 1)


def process_list(query_dict, process_fields=[]):
    # This should only used for POST function
    for field in process_fields:
        if query_dict.get(field) not in (None, ''):
            query_dict[field] = query_dict[field].split(',')
        else:
            query_dict[field] = []


def process_float(query_dict, process_fields=[]):
    for field in process_fields:
        if query_dict.get(field) != None:
            if query_dict[field] == '': #empty string
                query_dict[field] = None
            else:
                try:
                    query_dict[field] = float(query_dict[field])
                except:
                    raise GlobalAPIException(api_errors.ERROR_GENERAL_BAD_PARA_FORMAT, 'Not valid float format.')
        

def process_integer(query_dict, process_fields=[]):
    try:
        for field in process_fields:
            if query_dict.get(field)!=None:
                query_dict[field] = int(query_dict[field].split('.')[0])
    except:
        raise GlobalAPIException(api_errors.ERROR_GENERAL_BAD_PARA_FORMAT, 'Not valid integer format.')


def process_choices(value, choices):
    try:
        value = int(value)
    except ValueError:
        raise GlobalAPIException(api_errors.ERROR_GENERAL_BAD_PARA_FORMAT, 'At least one of the input choices is not valid integer format.')
    if value not in map(lambda x: x[0], choices):
        raise GlobalAPIException(api_errors.ERROR_GENERAL_BAD_PARA_FORMAT, 'The input choices are not valid.')
    return value


def wrap_info(response, info):
    return {'_response':response, '_info': info}


def get_now_ts(rtn_type='str'):
    ts = time.mktime(datetime.now().timetuple())
    if rtn_type == 'str':
        return str(ts).split('.')[0]
    else:
        return ts

def parse_pagination(offset=None, limit=None):
    try:
        offset = int(offset) if offset else 0
        limit = int(limit) if limit else DEFAULT_RETURN_NUM
        if limit > MAX_RETURN_NUM:
            limit = MAX_RETURN_NUM
    except ValueError:
        raise GlobalAPIException(api_errors.ERROR_GENERAL_BAD_PARA_FORMAT, "The 'offset' and 'limit' must be integer.")
    return offset, limit


def process_request(cls, request, *args, **kwargs):
    user_in_session = request.session.get('user')

    if not request.user.is_authenticated():
        if request.method=='GET' and cls.read_auth_exempt:
            pass
        elif request.method=='POST' and cls.create_auth_exempt:
            pass
        elif request.method=='DELETE' and cls.delete_auth_exempt:
            pass
        elif user_in_session:
            if hasattr(request, 'user'):
                request.user = user_in_session
        else:
            raise GlobalAPIException(api_errors.ERROR_AUTH_NOT_AUTHENTICATED)

    # Check of super user
    if cls.superuser_only and not request.user.is_superuser:
        raise GlobalAPIException(api_errors.ERROR_AUTH_NOT_AUTHENTICATED)

    # Check authorized
    # For Backbone post data
    _post_json_dict = {}
    if request.META.get('CONTENT_TYPE')=="application/json":
        _post_json_dict = json.loads(request.raw_post_data)

    _resource_dict = cls.auth_resource(request=request, json_dict=_post_json_dict, **kwargs)
    if not _resource_dict:
        _resource_dict = {}
    _resource_dict['request_user'] = request.user

    # Validate Create Args
    if request.method == 'POST':
        _post = QueryDict('', mutable=True)
        _post['detail'] = request.POST.get('detail') == 'true'
        # POST parameters

        # For Json
        content_type = request.META.get('CONTENT_TYPE', '')
        if "application/json" in content_type or content_type == '':
            if request.raw_post_data:
                json_dict = json.loads(request.raw_post_data)
                for kwarg in cls.create_kwargs:
                    if json_dict.get(kwarg) == None and kwarg in cls.required_fields:
                        raise GlobalAPIException(api_errors.ERROR_GENERAL_BAD_SIGNATURE, "'%s' is missing in params." % kwarg)
                    _post[kwarg] = json_dict.get(kwarg)
        # For XML
        else:
            for kwarg in cls.create_kwargs:
                if request.POST.get(kwarg) == None and kwarg in cls.required_fields:
                    raise GlobalAPIException(api_errors.ERROR_GENERAL_BAD_SIGNATURE, "'%s' is missing in params." % kwarg)
                _post[kwarg] = request.POST.get(kwarg)
        # FILE parameters
        for kwarg in cls.files_kwargs:
            if request.FILES.get(kwarg) == None and request.POST.get('file64') == None:
                raise GlobalAPIException(api_errors.ERROR_GENERAL_BAD_SIGNATURE, "'%s' is missing in upload file request." % kwarg)
            _post[kwarg] = request.FILES.get(kwarg)
        _post.update(_resource_dict)
        cls.create_validate(_post, request=request, **kwargs)
        request.CLEANED = _post
    # Pagination
    elif request.method == 'GET':
        _get = QueryDict('', mutable=True)
        _get['offset'], _get['limit'] = parse_pagination(request.GET.get('offset'), request.GET.get('limit'))
        _get['order_by'] = request.GET.get('order_by')
        _get['endpoint'] = _get['offset'] + _get['limit']
        _get['detail'] = request.GET.get('detail')=='true'
        
        for required_field in cls.required_fields_for_read:
            if required_field not in request.GET:
                raise GlobalAPIException(api_errors.ERROR_GENERAL_BAD_SIGNATURE, "'%s' is missing in params." % required_field)
            else:
                _get[required_field] = request.GET.get(required_field)
                
        for kwarg in cls.read_kwargs:
            if request.GET.get(kwarg) != None:
                _get[kwarg] = request.GET.get(kwarg)
        _get.update(_resource_dict)
        cls.read_validate(_get, request=request, **kwargs)
        request.CLEANED = cls.map_para(_get)
    # Validate Delete Args
    elif request.method == 'DELETE':
        _delete = QueryDict(request.body, mutable=True)

        for kwarg in cls.delete_kwargs:
            if not _delete.get(kwarg):
                _delete[kwarg] = request.GET.get(kwarg)

        _delete.update(_resource_dict)
        cls.delete_validate(_delete, request=request, **kwargs)
        request.CLEANED = _delete

    return request
