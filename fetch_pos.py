import requests
url = 'http://127.0.0.1:8000/pos/sistema/'
try:
    r = requests.get(url, timeout=5)
    print('STATUS', r.status_code)
    print('LENGTH', len(r.content))
    text = r.text
    print('HEAD (first 800 chars):')
    print(text[:800])
except Exception as e:
    print('ERROR', e)
