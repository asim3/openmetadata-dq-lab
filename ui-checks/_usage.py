from _api import *
t = token()
for p in call("/services/ingestionPipelines?limit=50", tok=t)["data"]:
    if p["pipelineType"] != "usage": continue
    st = call("/services/ingestionPipelines/%s/pipelineStatus?limit=1" % p["fullyQualifiedName"].replace("/", "%2F"), tok=t) if False else call("/services/ingestionPipelines/" + p["fullyQualifiedName"] + "/pipelineStatus", tok=t)
    for r in st.get("data", [])[:1]:
        print(p["service"]["name"], r.get("pipelineState"))
        for s in r.get("status", r.get("stepSummary", [])) if False else []: pass
        for k in ("status",):
            for step in r.get(k, []) or []:
                print(" ", step.get("name"), "records", step.get("records"), "warnings", step.get("warnings"), "errors", step.get("errors"))
