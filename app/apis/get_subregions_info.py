import json
import logging
import traceback

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
	try:
		logger.info(f"event---> {event}")
		logger.info(f"event---> {context}")
		body = json.loads(event.get("body", "{}"))
		result = body.get("Region",{})
		response = {
			'statusCode': 200,
			'body': json.dumps({"Region":result})
		}
		return response
	except Exception as e:
		logger.error(traceback.format_exc())
		logger.error(f"error in subregions_info -> {e}")
		return {
			'statusCode': 500,
			'body': json.dumps({"error": "Internal server error"})
		}