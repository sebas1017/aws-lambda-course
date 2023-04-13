from fastapi import FastAPI, HTTPException
import json
import uvicorn
import requests
import pandas as pd
import time
import random
import hashlib
import logging
import traceback
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class Settings:
    PROJECT_NAME = "API-COUNTRIES-FASTAPI"
    PROJECT_VERSION = "1.0.0"


app = FastAPI(title=Settings.PROJECT_NAME, version=Settings.PROJECT_VERSION)


def fetch(url):
    response = requests.get(url)
    if response.status_code == 200:
        data_response = response.json()
        return data_response
    return {}


def run_countries_info(event, context):
    try:
        logger.info(f"event -> {event}")
        logger.info(f"context -> {context}")
        countries_data = get_countries()
        logger.info(f"countries_data -> {countries_data}")
        return {
            'statusCode': 200,
            'body': json.dumps(countries_data)
        }
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error(f"error in run_countries_info -> {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({"error": "Internal server error"})
        }

@app.get("/")
def get_countries():
    try:
        url = "https://restcountries.com/v3.1/all"
        url_countries_by_region = "https://restcountries.com/v3.1/region/{region}"

        headers = {
            'x-rapidapi-key': "921cfc17abmsh42834139575656fp12725cjsn8ce3ad10333d",
            'x-rapidapi-host': "restcountries-v1.p.rapidapi.com"
        }
        regions_data = []
        hash_languages = []
        countries = []
        times = []
        data = requests.get(url, headers=headers)
        if data.status_code == 200:
            try:
                for information in data.json():
                    if information["region"] and not information["region"] in regions_data:
                        regions_data.append(information["region"])
                        # only the different existing regions

                for region in regions_data:
                    start_time = time.time()
                    data_task = fetch(url_countries_by_region.format(region=region))
                    response_by_region = data_task

                    # we consult the data requested by region
                    valid = False
                    while valid is False:
                        country_option = random.randint(0, len(response_by_region)-1)
                        if "languages" in list(response_by_region[country_option].keys()):
                            valid = True
                        else:
                            response_by_region.pop(country_option)

                    countries.append(response_by_region[country_option]['name']['common'])
                    key_language = list(response_by_region[country_option]['languages'].keys())[0]
                    hash_languages.append(hashlib.sha1(response_by_region[country_option]['languages'][str(key_language)].encode()).hexdigest())
                    end_time = time.time()
                    times.append(round((end_time-start_time)*1000, 2))
            except KeyError:
                logger.error(traceback.format_exc())
                data = {"message": "Error en API externa de paises recargar nuevamente"}
                raise HTTPException(status_code=500, detail=data)

            df = pd.DataFrame({
                "Region": regions_data,
                "Country": countries,
                "Language SHA1": hash_languages,
                "Time [ms]": times
            })
            # we build a dataframe and a data.json file with the results of the algorithm
            value = json.loads(df.to_json())
            return value
        else:
            data = {"message": "error en api externa de paises"}
            raise HTTPException(status_code=500, detail=data)
    except Exception as error:
        logger.error(traceback.format_exc())
        logger.error(f"Error in funcion index endpoint -> {error}")
        data = {"message": "error en api externa de paises"}
        raise HTTPException(status_code=500, detail=data)




#def lambda_handler(event, context):
#    return run_countries_info(event, context)


if __name__=="__main__":
	PORT = int(os.environ.get('PORT', 8000))
	uvicorn.run("get_countries_info_sync:app",host='0.0.0.0',port=PORT ,reload=True)