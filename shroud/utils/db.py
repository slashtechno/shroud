from pyairtable import Api, Table
from pyairtable.formulas import match, OR
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
                            limit=1,
                        ).data["messages"]
                    ]
                )
            except KeyError:
                table.delete(full_record["id"])

            if len(messages) < 2:
                table.delete(full_record["id"])

            for m in messages:
                if m.get("subtype") == "tombstone":
                    table.delete(full_record["id"])


def save_forward_start(dm_ts, selection_ts, dm_channel) -> None:
    global table
    table.create(
        {
            "dm_ts": dm_ts,
            "selection_ts": selection_ts,
            # "forwarded_ts": forwarded_ts,
            "dm_channel": dm_channel,
        }
    )


def save_forwarded_ts(dm_ts, forwarded_ts) -> None:
    global table
    record = table.first(formula=match({"dm_ts": dm_ts}))
    if record is None:
        raise ValueError(f"Record with timestamp {dm_ts} not found")
    table.update(record["id"], {"forwarded_ts": forwarded_ts})


def save_selection(selection_ts, selection) -> None:
    global table
    record = table.first(formula=match({"selection_ts": selection_ts}))
    if record is None:
        raise ValueError(f"Record with timestamp {selection_ts} not found")
    table.update(record["id"], {"selection": selection})


def get_message_by_ts(ts) -> dict:
    global table
    # https://pyairtable.readthedocs.io/en/stable/tables.html#formulas
    # formula = OR(
    #     match({"forwarded_ts": ts}),
    #     match({"dm_ts": ts}),
    #     match({"selection_ts": ts})
    # )
    #
    # From the docs: "If match_any=True, expressions are grouped with OR(), record is return if any of the values match."
    formula = match(
        {"dm_ts": ts, "forwarded_ts": ts, "selection_ts": ts}, match_any=True
    )
    record = table.first(formula=formula)
    if record is None:
        raise ValueError(f"Record with timestamp {ts} not found")
    return record


def main():
    global table
    table = get_table()


main()
