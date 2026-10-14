import base64, json, urllib.request
B = "http://localhost:8585/api/v1"
def call(path, data=None, tok=None, method=None):
    h = {"Content-Type": "application/json"}
    if tok: h["Authorization"] = "Bearer " + tok
    req = urllib.request.Request(B + path, data=json.dumps(data).encode() if data is not None else None, headers=h, method=method)
    return json.load(urllib.request.urlopen(req))
def token(user="admin@open-metadata.org", pw="admin"):
    return call("/users/login", {"email": user, "password": base64.b64encode(pw.encode()).decode()})["accessToken"]
