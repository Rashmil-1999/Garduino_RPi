from gql import gql, Client
from gql.transport.websockets import WebsocketsTransport
import json
import socket
import os

MANUAL_CONTROL_SUBSCRIPTION = """
    subscription irrigation_mode($u_uuid: uuid!) {
        irrigation_mode(where: {u_uuid: {_eq: $u_uuid}}) {
            ch_1
            ch_2
            ch_3
            ch_4
            ch_5
            ch_6
            ch_7
            ch_8
        }
    }
"""


# Initialize the WebsocketsTransport for subscription to the irrigation_timings table
transport = WebsocketsTransport(
    url="wss://relieved-asp-16.hasura.app/v1/graphql",
    headers={
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwNTM4Zjk5Yi1iNmIzLTRjNzgtOGIzNy1kYTkzMjQ5ZmQ0ZjAiLCJpYXQiOjE2MjYzNTA5MjUuMDUsImVtYWlsIjoicmFzaG1pbHA4MzNAZ21haWwuY29tIiwicm9sZXMiOlsidXNlciJdLCJodHRwczovL2hhc3VyYS5pby9qd3QvY2xhaW1zIjp7IngtaGFzdXJhLWFsbG93ZWQtcm9sZXMiOlsidXNlciJdLCJ4LWhhc3VyYS1kZWZhdWx0LXJvbGUiOiJ1c2VyIiwieC1oYXN1cmEtdXNlci1pZCI6IjA1MzhmOTliLWI2YjMtNGM3OC04YjM3LWRhOTMyNDlmZDRmMCIsIngtaGFzdXJhLW9yZy1pZCI6ImdhcmR1aW5vIiwieC1oYXN1cmEtYWRtaW4tc2VjcmV0IjoiYWRtaW4tc2VjcmV0In0sImV4cCI6MTY1Nzg4NjkyNX0.WHZl2DVAJRAdpkIKcuxqy84_NmtquhE3hHcer91mA4Q"
    },
)

# Create a GraphQL client using the defined transport
client = Client(transport=transport, fetch_schema_from_transport=True)

subscription = gql(MANUAL_CONTROL_SUBSCRIPTION)

params = {"u_uuid": "0538f99b-b6b3-4c78-8b37-da93249fd4f0"}
# BASE_DIR = "/home/pi/Desktop/proj/logs"
BASE_DIR = "/home/pi/Desktop/proj/logs"
IRRIGATION_CONTROL_MODE = os.path.join(BASE_DIR, "manual_control.json")
try:
    for result in client.subscribe(subscription, variable_values=params):
        print(json.dumps(result, indent=4, sort_keys=True))
        if result.get("irrigation_mode") is not None:
            with open(IRRIGATION_CONTROL_MODE, "w") as f:
                json.dump(result, f)
except KeyboardInterrupt:
    quit()
except Exception as e:
    print(e)
    quit()