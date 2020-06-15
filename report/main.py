# coding: utf-8

import os

from datetime import datetime, timedelta
from flask import make_response
from google.cloud import bigquery, secretmanager
import slack


def get_start_to_end():
    today = datetime.now()
    end = datetime(today.year, today.month, today.day, today.hour)

    # Report on the number of posts per day 9:00 AM JST(UTC+9)
    if end.hour == 0:
        start = (end - timedelta(1))
        span = 24
    else:
        start = (end - timedelta(hours=3))
        span = 3

    return (start.isoformat(' '), end.isoformat(' '), span)


def create_query(start, end):
    query_string = """
        SELECT channel, count(timestamp) as post
        FROM `{}.{}.{}`
        where TIMESTAMP('{}') <= timestamp and timestamp < TIMESTAMP('{}')
        group by channel
        order by post desc
        LIMIT 5"""

    project_id = os.environ['GCP_PROJECT']
    dataset = os.environ['BQ_DATASET']
    table = os.environ["BQ_TABLE"]

    return query_string.format(project_id, dataset, table, start, end)


def access_slack_token():
    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient()

    # Build the resource name of the secret version.
    project_id = os.environ['GCP_PROJECT']
    secret_id = os.environ["SLACK_API_TOKEN_KEY_NAME"]
    name = client.secret_version_path(project_id, secret_id, "latest")

    # Access the secret version.
    response = client.access_secret_version(name)

    return response.payload.data.decode('UTF-8')


def report(request):
    try:
        start, end, span = get_start_to_end()
        query = create_query(start, end)
        client = bigquery.Client()
        query_job = client.query(query)

        results = query_job.result()  # Waits for job to complete.

        slack_token = access_slack_token()
        sc = slack.WebClient(token=slack_token, timeout=30)

        result = 'いま話題のchannel (過去{}時間の投稿数Top5)\n'.format(span)
        rank = 0
        for row in results:
            data = sc.channels_info(channel=row.channel)
            channel_name = data['channel']['name']
            rank += 1
            result += '{}. #{} ({} posts)\n'.format(rank, channel_name, row.post)

        sc.chat_postMessage(
            channel=os.environ["SLACK_REPORT_CHANNEL"],
            link_names='true',
            text=result
        )

        return make_response(result, 200)
    except Exception as e:
        print(e)
        return make_response('Fail', 500)

