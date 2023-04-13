import types
import json
from get_countries_info_sync import lambda_handler
context = types.SimpleNamespace()
body = {"body":json.dumps(

	{"country":"CO"}
)}
response = lambda_handler(body, context)
print(response)