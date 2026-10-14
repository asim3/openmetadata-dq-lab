from _api import *
t = token()
for p in call("/services/ingestionPipelines?limit=50&fields=pipelineStatuses", tok=t)["data"]:
    s = p.get("pipelineStatuses")
    if isinstance(s, list): s = s[0] if s else None
    print(p["service"]["name"], p["pipelineType"], (s or {}).get("pipelineState"), p["provider"])
