from examples.fastapi_app import app
from fastapi_agent import FastAPIDiscovery

app_discovery = FastAPIDiscovery(app)

# openapi spec
print(app_discovery.get_openapi_spec)

# all routes summary
print(app_discovery.get_routes_summary())

# routes and usage example
for r in app_discovery.routes_info:
    print(r)
    print(app_discovery.get_route_usage_example(r))

# allow methods
print(app_discovery.get_allow_methods())

# auth depends
print(app_discovery.detected_auth)
