
from rest_api.handler import BaseIndexHandler, BaseObjectHandler, BaseHandler
from rest_api.utils import process_integer
from rest_api.errors import GlobalAPIException
from globals import api_errors

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
        sample_obj = SampleModel(title=title)
        sample_obj.save()

        return sample_obj.to_json()


class ObjectHandler(BaseObjectHandler):
    allowed_methods = ('GET', 'POST')
    query_model = SampleModel
    read_auth_exempt = True

    create_kwargs = ('title', 'sequence')
    form_fields = ('title', 'sequence')
    update_instead_save = True

    def create_validate(self, query_dict, **kwargs):
        process_integer(query_dict, ['sequence'])


class SampleHandler(BaseHandler):
    allowed_methods = ('GET',)
    read_kwargs = ('title', )
    read_auth_exempt = True

    def read_validate(self, query_dict, **kwargs):
        if query_dict.get('title') == '':
            raise GlobalAPIException(api_errors.ERROR_SAMPLE_TITLE_ERROR)
            # raise a customize APIException
        
        if query_dict.get('title') == 'unexpect':
              query_dict['title'] = undefined_variable
              # this will cause system error

    def read(self, request, **kwargs):
        return {'title': request.CLEANED.get('title')}
