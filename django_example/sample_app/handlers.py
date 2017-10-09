
from rest_api.handler import BaseIndexHandler, BaseObjectHandler
from sample_app.models import SampleModel

class IndexHandler(BaseIndexHandler):
	allowed_methods = ('GET', 'POST')
	query_model = SampleModel
	read_auth_exempt = True

	# for POST function
	create_kwargs = ('title', 'sequence')
	required_fields = ('title', )

	def create(self, request, **kwargs):
		title = request.CLEANED['title']
		sequence = request.CLEANED['sequence']
		sample_obj = SampleModel(title=title, sequence=sequence)
		sample_obj.save()

		return sample_obj.to_json()


class ObjectHandler(BaseObjectHandler):
	allowed_methods = ('GET', )
	query_model = SampleModel
	read_auth_exempt = True

