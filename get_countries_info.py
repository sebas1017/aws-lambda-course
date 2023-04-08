from fastapi import FastAPI, HTTPException
from psycopg2 import OperationalError
from core.config import settings
from db.session import engine 
from db.base import Base  
from db.models.statistics import StatisticsCountries
import json
import requests
import pandas as pd
import time
import random
import hashlib
import os
import asyncio
import aiohttp
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)



def create_tables():           
	Base.metadata.create_all(bind=engine)



app = FastAPI(title=settings.PROJECT_NAME,version=settings.PROJECT_VERSION)
create_tables()      
	
def insert_data(statistics, db):
	try:
		db_statistics = StatisticsCountries(
		total_time = statistics['Time [ms]'].sum() ,
		mean_time =  statistics['Time [ms]'].mean() ,
		min_time = statistics['Time [ms]'].min() ,
		max_time = statistics['Time [ms]'].max()
		)
		db.add(db_statistics)
		db.commit()
		db.refresh(db_statistics)
		return True
	except OperationalError:
		return "Por el momento nuestro servidor se encuentra abajo Espere por favor..."



def json_read():
		script_dir = os.path.dirname(__file__) # <-- absolute dir the script 
		rel_path = "data.json"
		abs_file_path = os.path.join(script_dir, rel_path)
		# open json file and give it to data variable as a dictionary
		with open(abs_file_path) as data_file:
			data_information = json.load(data_file)
		return data_information

async def fetch(session, url):
    async with session.get(url) as response:
        if response.status == 200:
            data_response = response.json()
            return await data_response
    return {}

@app.get("/")
async def get_countries():
		try:
			url = "https://restcountries.com/v3.1/all"
			url_countries_by_region = "https://restcountries.com/v3.1/region/{region}"

			headers = {
				'x-rapidapi-key': "921cfc17abmsh42834139575656fp12725cjsn8ce3ad10333d",
				'x-rapidapi-host': "restcountries-v1.p.rapidapi.com"
				}
			regions_data = []
			hash_languages =[]
			countries = []
			times=[]
			data  = requests.get(url, headers=headers)
			if data.status_code == 200:
				try: 
					for information in data.json():
						if information["region"]  and not information["region"]  in regions_data:
							regions_data.append(information["region"])
							# only the different existing regions

					async with aiohttp.ClientSession() as session:
						for region in regions_data:
							start_time = time.time()
							data_task = asyncio.create_task( fetch(session, url_countries_by_region.format(region=region) ))
							response_by_region = await asyncio.gather(data_task)

							response_by_region = response_by_region[0]
       
							
							# we consult the data requested by region
							valid = False
							while valid is False:
								country_option = random.randint(0,len(response_by_region)-1)
								if "languages" in list( response_by_region[country_option].keys()):
									valid = True
								else:
									response_by_region.pop(country_option)

							countries.append(response_by_region[country_option]['name']['common'])
							key_language =  list(response_by_region[country_option]['languages'].keys())[0]
							hash_languages.append(hashlib.sha1(response_by_region[country_option]['languages'][str(key_language)].encode()).hexdigest())
							end_time = time.time()
							times.append(round((end_time-start_time)*1000,2))
				except KeyError:
					data = {"message":"Error en API externa de paises recargar nuevamente"}
					raise HTTPException(status_code=500,detail=data)
				
				df = pd.DataFrame({
					"Region": regions_data,
					"Country": countries,
					"Language SHA1": hash_languages,
					"Time [ms]": times
				})
				#  we build a dataframe and a data.json file with the results of the algorithm
				df.to_json(path_or_buf='data.json')
				# here we can return the answer in html format but I decided to leave the answer in json format
				data_information = json_read()
			
				#results_database = insert_data(df,db)
				results_database = True
				if results_database != True:
					data = {"message":"Error interno servidor DB recargar nuevamente"}
					raise HTTPException(status_code=500,detail=data)
				else:
					return data_information
			else:
				data = {"message":"error en api externa de paises"}
				raise HTTPException(status_code=500,detail=data)
		except Exception as error:
			logger.error(f"Error in funcion index endpoint -> {error}")



async def run_countries_info(event , context):
	try:
		logger.info(f"event -> {event}")
		logger.info(f"context -> {context}")
		countries_data = await  get_countries()
		logger.info(f"countries_data -> {countries_data}")
		return {
			'statusCode': 200,
			'body': json.dumps(countries_data)
		}
	except Exception as e:
		logger.error(f"error in run_countries_info -> {e}")
		return {
			'statusCode': 50,
			'body': json.dumps({"error": "Internal server error"})
		}

def lambda_handler(event, context):
	return asyncio.run(run_countries_info(event, context))



"""
import types 
import json
context =types.SimpleNamespace()
body = {"body":json.dumps({
	"country":"CO"
})}
response = lambda_handler(body, context)
print(f"local response -> {response}")
"""


		
    