from slack_sdk import WebClient
from shroud.utils import db


def get_message_body_by_ts(ts: str, channel: str, client: WebClient) -> str:
    try:
        message = client.conversations_history(
            channel=channel, oldest=ts, inclusive=True, limit=1
        ).data["messages"][0]
        return message["text"]
    except IndexError:
        return None


def get_profile_picture_url(user_id, client: WebClient) -> str:
    user_info = client.users_info(user=user_id)
    profile_picture_url = user_info["user"]["profile"]["image_512"]
    return profile_picture_url


def get_name(user_id, client: WebClient) -> str:
    user_info = client.users_info(user=user_id)
    return user_info.data["user"]["real_name"]


def begin_forward(event: dict, client: WebClient) -> str:
    channel_id = event["channel"]
    selection_prompt = client.chat_postMessage(
        channel=channel_id,
        text="Select how this message should be forwarded",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Do you want to forward this report anonymously or with your username?",
                },
                "accessory": {
                    "type": "static_select",
                    "action_id": "report_forwarding",
                    "placeholder": {"type": "plain_text", "text": "Choose an option"},
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Forward Anonymously",
                            },
                            "value": "anonymous",
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Forward with Username",
                            },
                            "value": "with_username",
                        },
                    ],
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Submit"},
                        "style": "primary",
                        "action_id": "submit_forwarding",
                    }
                ],
            },
        ],
    )
    selection_ts = selection_prompt.data["ts"]

    db.save_forward_start(
        dm_ts=event["ts"],
        selection_ts=selection_ts,
        dm_channel=event["channel"],
    )
