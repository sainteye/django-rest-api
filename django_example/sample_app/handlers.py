
from rest_api.handler import BaseIndexHandler, BaseObjectHandler
from rest_api.utils import process_integer

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


class ObjectHandler(BaseObjectHandler):
	allowed_methods = ('GET', 'POST')
	query_model = SampleModel
	read_auth_exempt = True

	create_kwargs = ('title', 'sequence')
	form_fields = ('title', 'sequence')
	update_instead_save = True

	def create_validate(self, query_dict, **kwargs):
		process_integer(query_dict, ['sequence'])

