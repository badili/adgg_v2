from __future__ import absolute_import  # Python 2 only

import posixpath
import json

from urlparse import unquote

from django.http import Http404
from django.conf import settings
from django.contrib.staticfiles import finders
from django.contrib.auth.decorators import login_required
from django.views import static
from django.shortcuts import render, redirect
from django.middleware import csrf

from vendor.odk_parser import OdkParser
from .adgg import ADGG
from vendor.terminal_output import Terminal

import os
terminal = Terminal()


def serve_static_files(request, path, insecure=False, **kwargs):
    """
    Serve static files below a given point in the directory structure or
    from locations inferred from the staticfiles finders.
    To use, put a URL pattern such as::
        from django.contrib.staticfiles import views
        url(r'^(?P<path>.*)$', views.serve)
    in your URLconf.
    It uses the django.views.static.serve() view to serve the found files.
    """

    if not settings.DEBUG and not insecure:
        raise Http404
    normalized_path = posixpath.normpath(unquote(path)).lstrip('/')
    absolute_path = finders.find(normalized_path)
    if not absolute_path:
        if path.endswith('/') or path == '':
            raise Http404("Directory indexes are not allowed here.")
        raise Http404("'%s' could not be found" % path)
    document_root, path = os.path.split(absolute_path)
    return static.serve(request, path, document_root=document_root, **kwargs)


def show_landing(request):
    csrf_token = get_or_create_csrf_token(request)

    adgg = ADGG()
    stats = adgg.landing_page_stats()
    page_settings = {
        'page_title': "%s | Home" % settings.SITE_NAME,
        'csrf_token': csrf_token,
        'section_title': 'ADGG Home',
        'data': stats
    }
    return render(request, 'landing_page.html', page_settings)


@login_required(login_url='/login')
def show_dashboard(request):
    csrf_token = get_or_create_csrf_token(request)

    adgg = ADGG()
    try:
        stats = adgg.system_stats()
        page_settings = {
            'page_title': "%s | Home" % settings.SITE_NAME,
            'csrf_token': csrf_token,
            'section_title': 'ADGG Overview',
            'data': stats,
            'js_data': json.dumps(stats)
        }
        return render(request, 'dash_home.html', page_settings)
    except Exception as e:
        terminal.tprint('Error! %s' % str(e), 'fail')
        show_landing(request)


def get_or_create_csrf_token(request):
    token = request.META.get('CSRF_COOKIE', None)
    if token is None:
        token = csrf._get_new_csrf_string()
        request.META['CSRF_COOKIE'] = token
    request.META['CSRF_COOKIE_USED'] = True
    return token
