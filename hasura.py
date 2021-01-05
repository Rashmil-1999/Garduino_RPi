from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import datetime as dt


class HasuraClient:
  # Defining queries

  IRRIGATION_MUTATION_LOG = gql("""
    mutation IrrigationMutation($u_uuid: uuid!,$time: timestamptz!) {
        insert_irrigation_log(objects: {u_uuid: $u_uuid,time: $time}) {
            affected_rows
        }
    }
  """)

  def __init__(self, url, headers, U_UUID, fetch_schema_from_transport=True):
    self.transport = RequestsHTTPTransport(url=url, retries=3, headers=headers)
    self.client = Client(transport=self.transport, fetch_schema_from_transport=fetch_schema_from_transport)
    self.U_UUID = U_UUID
  
  def execute_normal_query(self, query, params):
    return self.client.execute(query, variable_values=params)

  def update_irrigation_log(self, time):
    params = {"u_uuid": self.U_UUID, "time":time}
    return self.client.execute(self.IRRIGATION_MUTATION_LOG, variable_values=params)
    

if __name__ == "__main__":
  import datetime as dt
  url = "https://relieved-asp-16.hasura.app/v1/graphql"
  headers = {'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwNTM4Zjk5Yi1iNmIzLTRjNzgtOGIzNy1kYTkzMjQ5ZmQ0ZjAiLCJpYXQiOjE2MDQ5MTQ3OTEuOTUyLCJlbWFpbCI6InJhc2htaWxwODMzQGdtYWlsLmNvbSIsInJvbGVzIjpbInVzZXIiXSwiaHR0cHM6Ly9oYXN1cmEuaW8vand0L2NsYWltcyI6eyJ4LWhhc3VyYS1hbGxvd2VkLXJvbGVzIjpbInVzZXIiXSwieC1oYXN1cmEtZGVmYXVsdC1yb2xlIjoidXNlciIsIngtaGFzdXJhLXVzZXItaWQiOiIwNTM4Zjk5Yi1iNmIzLTRjNzgtOGIzNy1kYTkzMjQ5ZmQ0ZjAiLCJ4LWhhc3VyYS1vcmctaWQiOiJnYXJkdWlubyIsIngtaGFzdXJhLWFkbWluLXNlY3JldCI6ImFkbWluLXNlY3JldCJ9LCJleHAiOjE2MzY0NTA3OTF9.2HJ14CJ1ShUsU7YqqsD3smRKbx2FJjF_xI6vG1-ZKBc'}

  params = {
    "u_uuid": "0538f99b-b6b3-4c78-8b37-da93249fd4f0",
    "time": str(dt.datetime.now())
  }
  try:
    remote = HasuraClient(url=url, headers=headers, U_UUID="0538f99b-b6b3-4c78-8b37-da93249fd4f0")
  except Exception as e:
    print(e.__class__.__name__ == "ConnectionError")
  
  try:
    remote.update_irrigation_log(time=str(dt.datetime.now()))
  except Exception as e:
    print("Connection Error")