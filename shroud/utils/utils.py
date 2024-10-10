from slack_sdk import WebClient
from shroud import settings
from shroud.utils import db

# {ts: selected_option}
selected_option = {

}

def get_profile_picture_url(user_id, client: WebClient) -> str:
    user_info = client.users_info(user=user_id)
    profile_picture_url = user_info["user"]["profile"]["image_512"]
    return profile_picture_url


def get_name(user_id, client: WebClient) -> str:
    user_info = client.users_info(user=user_id)
    return user_info.data["user"]["real_name"]


def new_forward(event: dict, client: WebClient) -> str:
    # Post as shroud (anonymous)
    client.chat_postMessage(
        channel=event["channel"],
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
    print("SKIPPING FORWARDING")
    return
    resp = client.chat_postMessage(channel=settings.channel, text=event["text"])

    # Save mappihng and send confirmation
    forwarded_ts = resp.data["ts"]
    db.save_message_mapping(event["ts"], forwarded_ts, event["channel"])
    client.chat_postEphemeral(
        channel=event["channel"],
        user=event["user"],
        text="Message content forwarded. Any replies to the forwarded message will be sent back to you as a threaded reply.",
    )


