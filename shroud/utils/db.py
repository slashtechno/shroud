from pyairtable import Api, Table
from pyairtable.formulas import match
from shroud import settings
table = None

def get_table() -> Table: 
    api = Api(api_key=settings.airtable_token)
    table = api.table(settings.airtable_base_id, settings.airtable_table_name)
    return table

def save_message_mapping(dm_ts, forwarded_ts, dm_channel) -> None:
    global table
    table.create(
        {
            "dm_ts": dm_ts,
            "forwarded_ts": forwarded_ts,
            "dm_channel": dm_channel,
        }
    )

def get_message_by_forwarded_ts(forwarded_ts) -> dict:
    global table
    record = table.first(
        formula=match({"forwarded_ts": forwarded_ts})
    )
    if record is None:
        raise ValueError(f"Record with forwarded_ts {forwarded_ts} not found")
    return record
def get_message_by_dm_ts(dm_ts) -> dict:
    global table
    record = table.first(
        formula=match({"dm_ts": dm_ts})
    )
    if record is None:
        raise ValueError(f"Record with dm_ts {dm_ts} not found")
    return record

def main():
    global table
    table = get_table()

main()