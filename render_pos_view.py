import os, sys, traceback
os.environ.setdefault('DJANGO_SETTINGS_MODULE','forneria.settings_dev')
import django
django.setup()
from django.test import RequestFactory
from pos import views

rf = RequestFactory()
req = rf.get('/pos/sistema/')
try:
    resp = views.inicio(req)
    print('STATUS:', getattr(resp, 'status_code', 'n/a'))
    content = getattr(resp, 'content', None)
    if content is None:
        print('Response has no content attribute; type:', type(resp))
    else:
        print('LENGTH:', len(content))
        try:
            print(content.decode('utf-8')[:4000])
        except Exception:
            print(repr(content)[:1000])
except Exception as e:
    print('EXCEPTION during view execution:')
    traceback.print_exc()
    sys.exit(1)
