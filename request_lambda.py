from __future__ import print_function

# import requests
import csv
import os
import re

# AWS Requirements
import boto3
from botocore.exceptions import ClientError
from botocore.vendored import requests

dynamodb = boto3.client('dynamodb')

def update_saved_info(phone_number, zip_code):
	try:
		response = dynamodb.get_item(TableName="aqi_db", Key={'phone_number': {'S': phone_number}})
	except ClientError as e:
		print(e.response['Error']['Message'])
	else:
		if "Item" not in response:
			dynamodb.put_item(TableName="aqi_db", Item={'phone_number': {'S': phone_number}, 'zip_code': {'S': zip_code}})
		elif response['Item']['zip_code'] != zip_code:
			dynamodb.update_item(TableName="aqi_db", Key={'phone_number': {'S': phone_number}}, UpdateExpression = "set zip_code = :z", ExpressionAttributeValues={":z": {"S": zip_code}})

def check_if_phone_number_saved(phone_number):
	try:
		response = dynamodb.get_item(TableName="aqi_db", Key={'phone_number': {'S': phone_number}})
	except ClientError as e:
		print(e.response['Error']['Message'])
	else:
		if "Item" in response:
			return response["Item"]


def get_AirNow_api_key():
	return os.environ['airnow_api_key']

def get_AQI(zip_code):
	if is_valid_zip_code(zip_code):
		response = requests.get('http://www.airnowapi.org/aq/observation/zipCode/current/?format=text/csv&zipCode=%s&distance=10&API_KEY=%s' % (zip_code, get_AirNow_api_key()))

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
    print("Received event: " + str(event))

    zip_code = event['Body']
    phone_number = event['From'][3:]
    aqi = get_AQI(zip_code)

    update_saved_info(phone_number, zip_code)

    formatted_text = format_AQI(aqi, zip_code)
    return '<?xml version=\"1.0\" encoding=\"UTF-8\"?>'\
           '<Response><Message><Body>%s</Body></Message></Response>' % (formatted_text)