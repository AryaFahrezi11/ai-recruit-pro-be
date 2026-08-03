import urllib.request, urllib.error
import json

req = urllib.request.Request(
    'http://localhost:8000/api/users/profile', 
    method='PUT', 
    headers={'Authorization': 'Bearer 123'}
)

try:
    urllib.request.urlopen(req)
except urllib.error.HTTPError as e:
    print(e.code, e.read().decode('utf-8'))
