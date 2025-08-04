from examples.fastapi_app import app
from fastapi_agent import FastAPIDiscovery

app_discovery = FastAPIDiscovery(app)

print(app_discovery.get_openapi_spec)
print(app_discovery.get_routes_summary())
for r in app_discovery.routes_info:
    print(r)
    print(app_discovery.get_route_usage_example(r))
print(app_discovery.get_allow_methods())
