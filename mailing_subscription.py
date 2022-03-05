from gql import gql, Client
from gql.transport.websockets import WebsocketsTransport
from gql.transport.requests import RequestsHTTPTransport
import json
import socket
import os

MAILING_SUBSCRIPTION = """
  subscription mailing_table_subscription($u_uuid: uuid!) {
  mailing_table(where: {u_uuid: {_eq: $u_uuid}}) {
    signal
    u_uuid
  }
}
"""

MAIL_SIGNAL_CHANGE_MUTATION = """
    mutation MyMutation($u_uuid: uuid!) {
        update_mailing_table(where: {u_uuid: {_eq: $u_uuid}}, _set: {signal: false}) {
            affected_rows
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
webSocketTransport = WebsocketsTransport(
    url="wss://relieved-asp-16.hasura.app/v1/graphql",
    headers={
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwNTM4Zjk5Yi1iNmIzLTRjNzgtOGIzNy1kYTkzMjQ5ZmQ0ZjAiLCJpYXQiOjE2MDQ5MTQ3OTEuOTUyLCJlbWFpbCI6InJhc2htaWxwODMzQGdtYWlsLmNvbSIsInJvbGVzIjpbInVzZXIiXSwiaHR0cHM6Ly9oYXN1cmEuaW8vand0L2NsYWltcyI6eyJ4LWhhc3VyYS1hbGxvd2VkLXJvbGVzIjpbInVzZXIiXSwieC1oYXN1cmEtZGVmYXVsdC1yb2xlIjoidXNlciIsIngtaGFzdXJhLXVzZXItaWQiOiIwNTM4Zjk5Yi1iNmIzLTRjNzgtOGIzNy1kYTkzMjQ5ZmQ0ZjAiLCJ4LWhhc3VyYS1vcmctaWQiOiJnYXJkdWlubyIsIngtaGFzdXJhLWFkbWluLXNlY3JldCI6ImFkbWluLXNlY3JldCJ9LCJleHAiOjE2MzY0NTA3OTF9.2HJ14CJ1ShUsU7YqqsD3smRKbx2FJjF_xI6vG1-ZKBc"
    },
)

HTTPTransport = RequestsHTTPTransport(
    url="https://relieved-asp-16.hasura.app/v1/graphql",
    headers={
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwNTM4Zjk5Yi1iNmIzLTRjNzgtOGIzNy1kYTkzMjQ5ZmQ0ZjAiLCJpYXQiOjE2MDQ5MTQ3OTEuOTUyLCJlbWFpbCI6InJhc2htaWxwODMzQGdtYWlsLmNvbSIsInJvbGVzIjpbInVzZXIiXSwiaHR0cHM6Ly9oYXN1cmEuaW8vand0L2NsYWltcyI6eyJ4LWhhc3VyYS1hbGxvd2VkLXJvbGVzIjpbInVzZXIiXSwieC1oYXN1cmEtZGVmYXVsdC1yb2xlIjoidXNlciIsIngtaGFzdXJhLXVzZXItaWQiOiIwNTM4Zjk5Yi1iNmIzLTRjNzgtOGIzNy1kYTkzMjQ5ZmQ0ZjAiLCJ4LWhhc3VyYS1vcmctaWQiOiJnYXJkdWlubyIsIngtaGFzdXJhLWFkbWluLXNlY3JldCI6ImFkbWluLXNlY3JldCJ9LCJleHAiOjE2MzY0NTA3OTF9.2HJ14CJ1ShUsU7YqqsD3smRKbx2FJjF_xI6vG1-ZKBc"
    },
)

# Create a GraphQL client using the defined transport
webSocketClient = Client(transport=webSocketTransport, fetch_schema_from_transport=True)

# create a http client
httpClient = Client(transport=HTTPTransport, fetch_schema_from_transport=True)

# Provide a GraphQL query
subscription = gql(MAILING_SUBSCRIPTION)
mutation = gql(MAIL_SIGNAL_CHANGE_MUTATION)

params = {"u_uuid": "0538f99b-b6b3-4c78-8b37-da93249fd4f0"}


try:
    while not_connected():
        pass
    for result in webSocketClient.subscribe(subscription, variable_values=params):
        print(json.dumps(result, indent=4, sort_keys=True))
        if result.get("mailing_table") is not None:
            if result["mailing_table"][0]["signal"]:
                print("signal for mail.")
                os.system("python3 /home/pi/Desktop/proj/mailing/generate_images.py")
                os.system("python3 /home/pi/Desktop/proj/mailing/mail_test.py")
                print("Mutating to false.")
                httpClient.execute(mutation, variable_values=params)
                print("Mutation Complete!")
except KeyboardInterrupt:
    quit()
except Exception as e:
    print(e)
    quit()