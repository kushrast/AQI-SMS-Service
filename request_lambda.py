from __future__ import print_function
# from botocore.vendored import requests
import requests
import csv
import os
import re

def get_AirNow_api_key():
	return os.environ['airnow_api_key']

def get_AQI(zip_code):
	if is_valid_zip_code(zip_code):
		response = requests.get('http://www.airnowapi.org/aq/observation/zipCode/current/?format=text/csv&zipCode=94568&distance=10&API_KEY=%s' % (get_AirNow_api_key()))

		response_body = response.text
		csv_reader = csv.DictReader(response_body.splitlines())
		for row in csv_reader:
			# Only sending PM 2.5 for now, can incorporate Ozone later
			if (row['ParameterName'] == "PM2.5"):
				return (row['AQI'], row['CategoryName'], row['HourObserved'])
	return None

def format_AQI(aqi_report, zip_code):
	if (aqi_report == None):
		return 'Sorry, we could not get the latest AQI data for ZIP code: %s :(' % (zip_code)
	else:
		return '%s:00:00 - Air Quality: %s, PM 2.5: %s in %s' % (aqi_report[2], aqi_report[1], aqi_report[0], zip_code)

def is_valid_zip_code(zip_code):
	regex = re.compile('^[0-9]{5}(?:-[0-9]{4})?$')
	return regex.match(zip_code)

def lambda_handler(event, context):
    print("Received context: " + str(context))

    zip_code = event['Body']
    aqi = get_AQI(zip_code)
    formatted_text = format_AQI(aqi, zip_code)
    return '<?xml version=\"1.0\" encoding=\"UTF-8\"?>'\
           '<Response><Message><Body>%s</Body></Message></Response>' % (formatted_text)