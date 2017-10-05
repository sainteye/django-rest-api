
from rest_api.handler import BaseIndexHandler
from sample_app.models import SampleModel

class IndexHandler(BaseIndexHandler):
	allowed_methods = ('GET', ) 
	query_model = SampleModel
	read_auth_exempt = True
