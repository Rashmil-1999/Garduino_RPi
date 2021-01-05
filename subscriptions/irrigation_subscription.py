from gql import gql, Client
from gql.transport.websockets import WebsocketsTransport
import json
import socket
import os

IRRIGATION_TIME_SUBSCRIPTION = """
  subscription irrigation_time_subscription($u_uuid: uuid!) {
  irrigation_timings(where: {u_uuid: {_eq: $u_uuid}}) {
    channel_1
    channel_2
    channel_3
    channel_4
    schedule
  }
}
"""

def not_connected():
    try:
        # connect to the host -- tells us if the host is actually
        # reachable
        socket.create_connection(("1.1.1.1", 53))
        return False
    except OSError:
        pass
    return True

# Initialize the WebsocketsTransport for subscription to the irrigation_timings table
transport = WebsocketsTransport(url='wss://relieved-asp-16.hasura.app/v1/graphql', headers={'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwNTM4Zjk5Yi1iNmIzLTRjNzgtOGIzNy1kYTkzMjQ5ZmQ0ZjAiLCJpYXQiOjE2MDQ5MTQ3OTEuOTUyLCJlbWFpbCI6InJhc2htaWxwODMzQGdtYWlsLmNvbSIsInJvbGVzIjpbInVzZXIiXSwiaHR0cHM6Ly9oYXN1cmEuaW8vand0L2NsYWltcyI6eyJ4LWhhc3VyYS1hbGxvd2VkLXJvbGVzIjpbInVzZXIiXSwieC1oYXN1cmEtZGVmYXVsdC1yb2xlIjoidXNlciIsIngtaGFzdXJhLXVzZXItaWQiOiIwNTM4Zjk5Yi1iNmIzLTRjNzgtOGIzNy1kYTkzMjQ5ZmQ0ZjAiLCJ4LWhhc3VyYS1vcmctaWQiOiJnYXJkdWlubyIsIngtaGFzdXJhLWFkbWluLXNlY3JldCI6ImFkbWluLXNlY3JldCJ9LCJleHAiOjE2MzY0NTA3OTF9.2HJ14CJ1ShUsU7YqqsD3smRKbx2FJjF_xI6vG1-ZKBc'})

# Create a GraphQL client using the defined transport
client = Client(transport=transport, fetch_schema_from_transport=True)

# Provide a GraphQL query
subscription = gql(IRRIGATION_TIME_SUBSCRIPTION)

params = {
  "u_uuid": "0538f99b-b6b3-4c78-8b37-da93249fd4f0"
}

path = '/home/pi/Desktop/proj/logs'

try:
    while not_connected():
        pass
    for result in client.subscribe(subscription,variable_values=params):
        print(json.dumps(result, indent=4, sort_keys=True))
        if result.get("irrigation_timings") is not None:
            with open(os.path.join(path, "irrigation_time.json"), "w") as f:
                json.dump(result,f)
except KeyboardInterrupt:
    quit()
except Exception as e:
    print(e)
    quit()