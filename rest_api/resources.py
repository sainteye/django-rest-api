import sys
import traceback
import json

from django.core.signals import got_request_exception
from django.http import Http404, HttpResponse, HttpResponseServerError, HttpResponseNotAllowed
from django.views.debug import ExceptionReporter
from django.views.decorators.vary import vary_on_headers
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.conf import settings
from django.db import DatabaseError
from django.core.mail import send_mail, EmailMessage

from rest_api.emitters import Emitter
from rest_api.piston.doc import HandlerMethod
from rest_api.piston.handler import typemapper
from rest_api.piston.resource import Resource
from rest_api.piston.utils import rc, translate_mime, MimerDataException, HttpStatusCode,\
    format_error

from rest_api import errors as api_errors
from rest_api.utils import process_request


def make_error_response(code, debug=None):
    """ Creates an error response for error code `code`.  If code is invalid, returns
    the default 'unknown error' response. """
    try:
        error_code, error_message = code, api_errors.API_ERRORS[code]
    except KeyError:
        error_code, error_message = api_errors.ERROR_GENERAL_UNKNOWN_ERROR,\
            api_errors.API_ERRORS[api_errors.ERROR_GENERAL_UNKNOWN_ERROR]
    
    content = {
        'error': {
            'code': error_code,
            'message': error_message,
        }
    }

    display_success = False
    if hasattr(settings, 'REST_API_DISPLAY_SUCCESS'):
        display_success = settings.REST_API_DISPLAY_SUCCESS

    if display_success:
        content['success'] = False

    if debug:
        content['error']['debug'] = debug
    
    result = rc.BAD_REQUEST
    if code == api_errors.ERROR_AUTH_NOT_AUTHENTICATED:
        result = rc.FORBIDDEN
    elif code == api_errors.ERROR_AUTH_BAD_CREDENTIALS:
        result = rc.FORBIDDEN
    elif code == api_errors.ERROR_AUTH_NOT_AUTHORIZED:
        result = rc.FORBIDDEN
    elif code == api_errors.ERROR_GENERAL_BAD_SIGNATURE:
        result = rc.BAD_REQUEST
    elif code == api_errors.ERROR_GENERAL_UNKNOWN_ERROR:
        result = rc.INTERNAL_ERROR
    elif code == api_errors.ERROR_GENERAL_NOT_FOUND:
        result = rc.NOT_FOUND
    else:
        result = rc.BAD_REQUEST

    result.content = content

    return result

CHALLENGE = object()


class BaseResource(Resource):
    
    @vary_on_headers('Authorization')
    def __call__(self, request, *args, **kwargs):
        rm = request.method.upper()
        handler, anonymous = self.handler, self.handler.is_anonymous

        if rm == 'PUT' and request.META['CONTENT_TYPE']=="application/json":
            rm = request.method = 'POST'
        
        # Translate nested datastructs into `request.data` here.
        if rm == 'POST':
            try:
                translate_mime(request)
            except MimerDataException:
                return rc.BAD_REQUEST
            if not hasattr(request, 'data'):
                request.data = request.POST
        if not rm in handler.allowed_methods:
            return HttpResponseNotAllowed(handler.allowed_methods)

        meth = getattr(handler, self.callmap.get(rm, ''), None)
        if not meth:
            raise Http404

        # Clean up the request object a bit, since we might
        # very well have `oauth_`-headers in there, and we
        # don't want to pass these along to the handler.

        request = self.cleanup_request(request)

        try:
            # The verified process of new api is all in process_request
            request = process_request(handler, request, *args, **kwargs)
            raw_response = meth(request, *args, **kwargs)
            # An implicit protocal for deliver info from handler
            use_wrapper = False
            if hasattr(settings, 'REST_API_WITH_WRAPPER'):
                use_wrapper = settings.REST_API_WITH_WRAPPER

            display_success = False
            if hasattr(settings, 'REST_API_DISPLAY_SUCCESS'):
                display_success = settings.REST_API_DISPLAY_SUCCESS

            if use_wrapper:
                if type(raw_response)==dict and raw_response.has_key('_info') and raw_response.has_key('_data'):
                    result = {
                        'data': raw_response['_data'],
                        'info': raw_response['_info'],
                    }
                else:
                    if type(raw_response)==dict:
                        result = raw_response
                    else:
                        result = {
                            'data': raw_response,
                            'info': {}
                        }

                if display_success and not type(raw_response)==dict:
                    result['success'] = True
            else:
                result = raw_response

        except Exception, e:
            result = self.error_handler(e, request, meth)

        emitter, ct = Emitter.get('json')
        fields = handler.fields

        if hasattr(handler, 'list_fields') and isinstance(result, (list, tuple, QuerySet)):
            fields = handler.list_fields

        status_code = 200
        
        # If we're looking at a response object which contains non-string
        # content, then assume we should use the emitter to format that 
        # content
        if isinstance(result, HttpResponse) and not result._is_string:
            status_code = result.status_code
            # Note: We can't use result.content here because that method attempts
            # to convert the content into a string which we don't want. 
            # when _is_string is False _container is the raw data
            result = result._container
     
        srl = emitter(result, typemapper, handler, fields, anonymous)

        try:
            """
            Decide whether or not we want a generator here,
            or we just want to buffer up the entire result
            before sending it to the client. Won't matter for
            smaller datasets, but larger will have an impact.
            """
            if self.stream: stream = srl.stream_render(request)
            else: stream = srl.render(request)

            if not isinstance(stream, HttpResponse):
                resp = HttpResponse(stream, content_type=ct, status=status_code)
            else:
                resp = stream

            resp.streaming = self.stream

            if request.method == "OPTIONS":
                # Try to make it accessible for google index search
                resp['Access-Control-Allow-Origin'] = "webcache.googleusercontent.com"
                resp['Access-Control-Allow-Methods'] = "POST, OPTIONS"
                resp['Access-Control-Allow-Headers'] = "X-Requested-With"
                resp['Access-Control-Max-Age'] = "1800"

            return resp
        except HttpStatusCode, e:
            return e.response

    def email_exception(self, reporter):
        # Implement your email method
        """
        subject = "API crash report"
        html = reporter.get_traceback_html()
        email_subject = settings.EMAIL_SUBJECT_PREFIX+subject
        to = [admin[1] for admin in settings.ADMINS]
        send_email(email_subject, '', html, settings.SERVER_EMAIL, to, throttle=True)
        """
        pass
    
    def error_handler(self, e, request, meth):
        """
        Override this method to add handling of errors customized for your 
        needs
        """
        debug_msg = None
        print e

        if request.POST.get('debug') or request.GET.get('debug') or settings.DEBUG:
            debug_msg = e.debug if isinstance(e, api_errors.GlobalAPIException) and e.debug else unicode(e)
            exc_type, exc_value, tb = sys.exc_info()
            print '%s\n' % ''.join(traceback.format_exception(exc_type, exc_value, tb, 20))

        if isinstance(e, api_errors.GlobalAPIException) and e.send_mail:
            # Send mail for customize Exception
            exc_type, exc_value, tb = sys.exc_info()
            rep = ExceptionReporter(request, exc_type, e.debug if e.debug else unicode(e), tb.tb_next)
            self.email_exception(rep)
        
        if isinstance(e, TypeError):
            result = rc.ALL_OK
            hm = HandlerMethod(meth)
            sig = hm.signature

            msg = 'Method signature does not match.\n\n'

            if sig:
                msg += 'Signature should be: %s' % sig
            else:
                msg += 'Resource does not expect any parameters.'

            if self.display_errors:
                msg += '\n\nException was: %s' % str(e)

            exc_type, exc_value, tb = sys.exc_info()
            rep = ExceptionReporter(request, exc_type, exc_value, tb.tb_next)
            if self.email_errors:
                self.email_exception(rep)

            result.content = json.dumps({
                'success': False,
                'error': {
                    'code': api_errors.ERROR_GENERAL_BAD_SIGNATURE,
                    'message': msg,
                }
            }, ensure_ascii=False, indent=3)
            return result
        
        elif isinstance(e, Http404):
            return make_error_response(api_errors.ERROR_GENERAL_NOT_FOUND)

        elif isinstance(e, DatabaseError):
            # For stupid people doing nonesense query
            error_msg = '%s' % e
            if 'ObjectId on MongoDB' in error_msg:
                return make_error_response(api_errors.ERROR_GENERAL_TARGET_NOT_FOUND, debug_msg)
 
        elif isinstance(e, api_errors.GlobalAPIException):
            return make_error_response(e.code, debug_msg)
            
        elif isinstance(e, User.DoesNotExist):
            return make_error_response(api_errors.ERROR_GENERAL_USER_NOT_FOUND, debug_msg)

        elif isinstance(e, ObjectDoesNotExist):
            return make_error_response(api_errors.ERROR_GENERAL_TARGET_NOT_FOUND, debug_msg)
        
        else: 
            """
            On errors (like code errors), we'd like to be able to
            give crash reports to both admins and also the calling
            user. There's two setting parameters for this:

            Parameters::
             - `PISTON_EMAIL_ERRORS`: Will send a Django formatted
               error email to people in `settings.ADMINS`.
             - `PISTON_DISPLAY_ERRORS`: Will return a simple traceback
               to the caller, so he can tell you what error they got.

            If `PISTON_DISPLAY_ERRORS` is not enabled, the caller will
            receive a basic "500 Internal Server Error" message.
            """
            # report the error to django
            got_request_exception.send(sender=self, request=request)
            
            exc_type, exc_value, tb = sys.exc_info()
            rep = ExceptionReporter(request, exc_type, exc_value, tb.tb_next)
            if self.email_errors:
                self.email_exception(rep)

            if self.display_errors:
                return make_error_response(api_errors.ERROR_GENERAL_UNKNOWN_ERROR, debug_msg)
                # return HttpResponseServerError(
                #     format_error('\n'.join(rep.format_exception())))
            else:
                return make_error_response(api_errors.ERROR_GENERAL_UNKNOWN_ERROR)
