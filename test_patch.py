import urllib.request
import urllib.error
import json

url = "http://127.0.0.1:8000/api/jobs/3e3d76e9-43c8-4290-a265-2aa76f2eac58/status"
data = json.dumps({"status": "active"}).encode('utf-8')
req = urllib.request.Request(url, data=data, method='PATCH', headers={'Content-Type': 'application/json'})

try:
    response = urllib.request.urlopen(req)
    print(response.getcode())
except urllib.error.HTTPError as e:
    print(e.code)
    print(e.read().decode('utf-8'))
except urllib.error.URLError as e:
    print(e.reason)
