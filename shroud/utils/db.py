from pyairtable import Api, Table
from pyairtable.formulas import match
from shroud import settings
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

table = None


def get_table() -> Table:
    api = Api(api_key=settings.airtable_token)
    table = api.table(settings.airtable_base_id, settings.airtable_table_name)
    return table


def clean_database(client: WebClient) -> None:
    """
    If either the DM or the forwarded message no longer exists, remove the record from the database
    """
    global table
    for list_of_records in table.iterate():
        for full_record in list_of_records:
            messages = []
            r = full_record["fields"]
            try:
                messages.extend(
                    [
                        m
                        for m in client.conversations_history(
                            channel=r["dm_channel"],
                            inclusive=True,
                            oldest=r["dm_ts"],
                            limit=1,
                        ).data["messages"]
                    ]
                )
                messages.extend(
                    [
                        m
                        for m in client.conversations_history(
                            channel=settings.channel,
                            inclusive=True,
                            oldest=r["forwarded_ts"],
                            limit=1
                        ).data["messages"]
                    ]
                )
            except KeyError:
                table.delete(full_record["id"])

            if len(messages) < 2:
                table.delete(full_record["id"])

            for m in messages:
                if m.get("subtype")  == "tombstone":
                    table.delete(full_record["id"])


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
    record = table.first(formula=match({"forwarded_ts": forwarded_ts}))
    if record is None:
        raise ValueError(f"Record with forwarded_ts {forwarded_ts} not found")
    return record


def get_message_by_dm_ts(dm_ts) -> dict:
    global table
    record = table.first(formula=match({"dm_ts": dm_ts}))
    if record is None:
        raise ValueError(f"Record with dm_ts {dm_ts} not found")
    return record


def main():
    global table
    table = get_table()


main()
