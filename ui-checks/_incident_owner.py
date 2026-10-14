import time
from _api import *
t = token()
tbl = "dqlab_mysql.default.dqlab.customers"
tb = call("/tables/name/" + tbl + "?fields=owners", tok=t)
admin = call("/users/name/admin", tok=t)
call("/tables/" + tb["id"], [{"op":"add","path":"/owners","value":[{"id":admin["id"],"type":"user"}]}], tok=t, method="PATCH") if False else None
import urllib.request, json
def patch(path, ops):
    req = urllib.request.Request(B+path, data=json.dumps(ops).encode(), headers={"Content-Type":"application/json-patch+json","Authorization":"Bearer "+t}, method="PATCH")
    return json.load(urllib.request.urlopen(req))
patch("/tables/" + tb["id"], [{"op":"add","path":"/owners","value":[{"id":admin["id"],"type":"user"}]}])
try:
    call("/dataQuality/testCases/name/dqlab_mysql.default.dqlab.customers.zz_owner_probe", tok=t)
    call("/dataQuality/testCases/name/dqlab_mysql.default.dqlab.customers.zz_owner_probe?hardDelete=true", tok=t, method="DELETE")
except Exception: pass
tc = call("/dataQuality/testCases", {"name":"zz_owner_probe","entityLink":"<#E::table::%s>" % tbl,"testDefinition":"tableRowCountToEqual","parameterValues":[{"name":"value","value":"1"}]}, tok=t)
fqn = tc["fullyQualifiedName"]
call("/dataQuality/testCases/testCaseResults/" + fqn, {"timestamp": int(time.time()*1000), "testCaseStatus":"Failed","result":"probe"}, tok=t, method="POST")
time.sleep(5)
inc = call("/dataQuality/testCases/testCaseIncidentStatus?limit=10&testCaseFQN=" + fqn, tok=t)
for i in inc["data"]:
    print(i["testCaseResolutionStatusType"], i.get("testCaseResolutionStatusDetails"))
call("/dataQuality/testCases/" + tc["id"] + "?hardDelete=true&recursive=true", tok=t, method="DELETE")
patch("/tables/" + tb["id"], [{"op":"remove","path":"/owners/0"}])
