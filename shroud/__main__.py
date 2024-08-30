import dotenv
import re
# import yaml
# import importlib.resources

# Slack imports
from slack_bolt import App, BoltResponse
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.web.client import WebClient


# Types
from slack_bolt.context.respond import Respond
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
def handle_message_im(event, say):
    if event.get("channel_type") == "im":
        print(event)
        text = event["text"]
        user = event["user"]
        if re.match(r"hello", text, re.IGNORECASE):
            say(f"Hello, <@{user}>!")




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
