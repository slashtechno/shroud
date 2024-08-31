import dotenv
import re
import json
# import yaml
# import importlib.resources

# Slack imports
from slack_bolt import App, BoltResponse
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.web.client import WebClient


# Types
from slack_bolt.context.respond import Respond
from slack_bolt.context.say import Say
from slack_sdk.errors import SlackApiError
# To avoid a log message about unhandled requests
from slack_bolt.error import BoltUnhandledRequestError
from shroud import settings

dotenv.load_dotenv()
SLACK_BOT_TOKEN = settings.slack_bot_token
SLACK_APP_TOKEN = settings.slack_app_token


app = App(token=SLACK_BOT_TOKEN, raise_error_for_unhandled_request=True)

# https://api.slack.com/events/message.im
@app.event("message")
def handle_message(event, say: Say, client: WebClient, respond: Respond):
    try:
        with open("message_mapping.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        say("JSON file not found")
        return
    if event.get("channel_type") == "im" and event.get("subtype") is None:
        if event.get("thread_ts") is not None:
            # Find where to forward the message  
            for k, v in data.items():
                if k == event["thread_ts"]:
                    to_send = f"{event['text']}"
                    client.chat_postMessage(channel=settings.channel, text=to_send, thread_ts=data[k]["forwarded_ts"])
                    break
            else:
                client.chat_postEphemeral(
                    channel=event["channel"],
                    user=event["user"],
                    text="No message found",
                )
        else:
            forwarded_ts = forward_to_channel(event, client)
            save_message_mapping(event["ts"], forwarded_ts, event["channel"])
            client.chat_postEphemeral(
                channel=event["channel"],
                user=event["user"],
                text="Message content forwarded. Any replies to the forwarded message will be sent back to you as a threaded reply.",
            )
    elif (event.get("channel_type") == "group" or event.get("channel_type") == "channel") and event.get("subtype") is None:
        if event.get("thread_ts", None) is not None:
            for k, v in data.items():
                if data[k]["forwarded_ts"] == event["thread_ts"]:
                    to_send = f"<@{event['user']}>: {event['text']}"
                    client.chat_postMessage(channel=data[k]["dm_channel"], text=to_send, thread_ts=k)
                    break
            else:
                client.chat_postEphemeral(
                    channel=event["channel"],
                    user=event["user"],
                    text="No message found",
                )
        else:
            print("Ignoring message as it's not a reply")
    # else:
        # print(event)


def save_message_mapping(ts, forwarded_ts, dm_channel) -> None:
    try: 
        with open("message_mapping.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    data[ts] = {"forwarded_ts": forwarded_ts, "dm_channel": dm_channel}
    with open("message_mapping.json", "w") as f:
        json.dump(data, f)

def forward_to_channel(event, client: WebClient, thread_ts=None) -> str:
    resp = client.chat_postMessage(channel=settings.channel, text=event["text"], thread_ts=thread_ts)
    return resp.data["ts"]


# https://github.com/slackapi/bolt-python/issues/299#issuecomment-823590042
@app.error
def handle_errors(error, body, respond: Respond):
    if isinstance(error, BoltUnhandledRequestError):
        return BoltResponse(status=200, body="")
    else:
        print(f"Error: {str(error)}")
        try:
            respond(
                "Something went wrong. If this persists, please contact <@U075RTSLDQ8>."
            )
        except SlackApiError as e:
            print(f"Error sending message: {e.response['error']}")
        return BoltResponse(status=500, body="Something Wrong")


def main():
    global app
    SocketModeHandler(app, SLACK_APP_TOKEN).start()


if __name__ == "__main__":
    main()

# @app.command("/shroud-help")
# def help_command(ack, respond: Respond):
#     ack()
#     manifest_path = importlib.resources.files(__package__).parent / "manifest.yml"
#     with open(manifest_path, "r") as f:
#         features = yaml.safe_load(f)["features"]

#     help_text = "Commands:"
#     slash_commands = features["slash_commands"]
#     for command in slash_commands:
#         try:
#             help_text += f"\n`{command['command']} {command['usage_hint']}`: {command['description']}"
#         except KeyError:
#             # Most likely means that usage_hint is not defined
#             help_text += f"\n`{command['command']}`: {command['description']}"
#     if len(slash_commands) == 0:
#         help_text += "\nNo commands available.\n"
#     else: 
#         help_text += "\n"
    
#     shortcuts = features["shortcuts"]
#     help_text += "\nShortcuts:"
#     message_shortcuts_text = "Message shortcuts:"
#     global_shortcuts_text = "Global shortcuts:"
#     for shortcut in shortcuts:
#         if shortcut["type"] == "message":
#             message_shortcuts_text += f"\n`{shortcut["name"]}`: {shortcut['description']}"
#         elif shortcut["type"] == "global":
#             global_shortcuts_text += f"\n`{shortcut["name"]}`: {shortcut['description']}"
#     if len(shortcuts) == 0:
#         help_text += "\nNo shortcuts available."
#     else:
#         if message_shortcuts_text != "Message shortcuts:":
#             help_text += f"\n{message_shortcuts_text}"
#         if global_shortcuts_text != "Global shortcuts:":
#             help_text += f"\n{global_shortcuts_text}"
    
#     respond(help_text)