import sys, inspect

from django.http import (HttpResponse, Http404, HttpResponseNotAllowed,
    HttpResponseForbidden, HttpResponseServerError)
from django.views.debug import ExceptionReporter
from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.db.models.query import QuerySet
from django.http import Http404

from rest_api.piston.handler import typemapper
from rest_api.piston.doc import HandlerMethod
from rest_api.piston.utils import coerce_put_post, FormValidationError, HttpStatusCode
from rest_api.piston.utils import rc, format_error, translate_mime, MimerDataException

CHALLENGE = object()

class Resource(object):
    """
    Resource. Create one for your URL mappings, just
    like you would with Django. Takes one argument,
    the handler. The second argument is optional, and
    is an authentication handler. If not specified,
    `NoAuthentication` will be used by default.
    """
    callmap = { 'GET': 'read', 'POST': 'create',
                'PUT': 'update', 'DELETE': 'delete' }

    def __init__(self, handler):
        if not callable(handler):
            raise AttributeError, "Handler not callable."

        self.handler = handler()
        self.csrf_exempt = getattr(self.handler, 'csrf_exempt', True)

        # Erroring
        self.email_errors = getattr(settings, 'PISTON_EMAIL_ERRORS', True)
        self.display_errors = getattr(settings, 'PISTON_DISPLAY_ERRORS', True)
        self.stream = getattr(settings, 'PISTON_STREAM_OUTPUT', False)

    def determine_emitter(self, request, *args, **kwargs):
        """
        Function for determening which emitter to use
        for output. It lives here so you can easily subclass
        `Resource` in order to change how emission is detected.

        You could also check for the `Accept` HTTP header here,
        since that pretty much makes sense. Refer to `Mimer` for
        that as well.
        """
        em = kwargs.pop('emitter_format', None)

        if not em:
            em = request.GET.get('format', 'json')

        return em

    def form_validation_response(self, e):
        """
        Method to return form validation error information. 
        You will probably want to override this in your own
        `Resource` subclass.
        """
        resp = rc.BAD_REQUEST
        resp.write(' '+str(e.form.errors))
        return resp

    @staticmethod
    def cleanup_request(request):
        """
        Removes `oauth_` keys from various dicts on the
        request object, and returns the sanitized version.
        """
        for method_type in ('GET', 'PUT', 'POST', 'DELETE'):
            block = getattr(request, method_type, { })

            if True in [ k.startswith("oauth_") for k in block.keys() ]:
                sanitized = block.copy()

                for k in sanitized.keys():
                    if k.startswith("oauth_"):
                        sanitized.pop(k)

                setattr(request, method_type, sanitized)

        return request

    # --

    def email_exception(self, reporter):
        subject = "Piston crash report"
        html = reporter.get_traceback_html()

        message = EmailMessage(settings.EMAIL_SUBJECT_PREFIX+subject,
                                html, settings.SERVER_EMAIL,
                                [ admin[1] for admin in settings.ADMINS ])

        message.content_subtype = 'html'
        message.send(fail_silently=True)


    def error_handler(self, e, request, meth, em_format):
        """
        Override this method to add handling of errors customized for your 
        needs
        """
        if isinstance(e, FormValidationError):
            return self.form_validation_response(e)

        elif isinstance(e, TypeError):
            result = rc.BAD_REQUEST
            hm = HandlerMethod(meth)
            sig = hm.signature

            msg = 'Method signature does not match.\n\n'

            if sig:
                msg += 'Signature should be: %s' % sig
            else:
                msg += 'Resource does not expect any parameters.'

            if self.display_errors:
                msg += '\n\nException was: %s' % str(e)

            result.content = format_error(msg)
            return result
        elif isinstance(e, Http404):
            return rc.NOT_FOUND

        elif isinstance(e, HttpStatusCode):
            return e.response
 
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
            exc_type, exc_value, tb = sys.exc_info()
            rep = ExceptionReporter(request, exc_type, exc_value, tb.tb_next)
            if self.email_errors:
                self.email_exception(rep)
            if self.display_errors:
                return HttpResponseServerError(
                    format_error('\n'.join(rep.format_exception())))
            else:
                raise
