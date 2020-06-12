import json
import os

from flask import make_response
from google.cloud import bigquery


def _insert_into_bigquery(json_row):
    dataset = os.environ['BQ_DATASET']
    table = os.environ['BQ_TABLE']

    bq = bigquery.Client()
    table = bq.dataset(dataset).table(table)
    
    errors = bq.insert_rows_json(table,
                            [json_row])
    if errors != []:
        print("Error: Data didn't insert to Bigquery")
        return 500

    return 200


def _event_handler(data):
    event_type = data.get('type')
    subtype = data.get('subtype')
    
    if event_type == 'message' and subtype is None:
        payload = {
            'channel': data['channel'],
            'timestamp': data['ts'],
        }
    else:
        return 200

    return _insert_into_bigquery(payload)


def streaming(request):
    data = request.get_json()

    if 'challenge' in data:
        return data.get("challenge")

    if "event" in data:
        event = data.get("event")
        status = _event_handler(event)

        if 300 > status:
            return make_response('OK', status)
        else:
            return make_response('NG', status)

    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
            you're looking for.", 404, {"X-Slack-No-Retry": 1})