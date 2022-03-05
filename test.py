from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import datetime as dt


IRRIGATION_MUTATION_LOG = gql(
    """
    mutation IrrigationMutation($u_uuid: uuid!,$time: timestamptz!, $mode: String!) {
        insert_irrigation_log(objects: {u_uuid: $u_uuid,time: $time, mode: $mode}) {
            affected_rows
        }
    }
  """
)

query = """
query MyQuery($p_uuid: uuid!) {
  sensor_data(where: {p_uuid: {_eq: $p_uuid}}) {
    p_uuid
    timestamp
    air_humidity
    air_temperature
    soil_moisture
    soil_temp
    plant {
      plant_sensor_mappings {
        sensor_mapping {
          alias
        }
      }
    }
}
}
"""

sensor_query = gql(query)


with open(os.path.join(dire, "test.txt"), "a") as f:
    print(dt.now().strftime("%H:%M:%S"))
    f.write(str(dt.now().strftime("%H:%M:%S\n")))