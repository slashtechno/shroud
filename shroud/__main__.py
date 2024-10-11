import dotenv
import yaml
import importlib.resources

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
from shroud.utils import db
from shroud.utils import utils

dotenv.load_dotenv()
SLACK_BOT_TOKEN = settings.slack_bot_token
SLACK_APP_TOKEN = settings.slack_app_token


app = App(token=SLACK_BOT_TOKEN, raise_error_for_unhandled_request=True)

# https://api.slack.com/events/message.im
@app.event("message")
def handle_message(event, say: Say, client: WebClient, respond: Respond):
    # Handle incoming DMs
    if event.get("channel_type") == "im" and event.get("subtype") is None:
        # Existing conversation
        if event.get("thread_ts") is not None:
                try:
                    record = db.get_message_by_ts(event["thread_ts"])["fields"]
                    to_send = f"{event['text']}"
                    client.chat_postMessage(channel=settings.channel, text=to_send, thread_ts=record["forwarded_ts"])
                except ValueError:
                    client.chat_postEphemeral(
                        channel=event["channel"],
                        user=event["user"],
                        text="No message found",
                    )
        # New conversation
        else:
            utils.begin_forward(event, client)
    # Handle incoming messages in channels
    elif (event.get("channel_type") == "group" or event.get("channel_type") == "channel") and event.get("subtype") is None:
        # We only care about messages that are threads
        if event.get("thread_ts", None) is not None:
            try:
                record = db.get_message_ts(event["thread_ts"])["fields"]

                client.chat_postMessage(
                    channel=record["dm_channel"], 
                    text=event["text"], 
                    thread_ts=record["dm_ts"],
                    username=utils.get_name(event["user"], client),
                    icon_url=utils.get_profile_picture_url(event["user"], client)
                    )
            except ValueError:
                client.chat_postEphemeral(
                    channel=event["channel"],
                    user=event["user"],
                    text="No message found",
                )
    elif event.get("subtype") == "message_changed":
        client.chat_postEphemeral(
            channel=event["channel"],
            user=event["previous_message"]["user"],
            text="It seems you might have updated a message. This bot only supports forwarding messages, at the moment. Thus, edits and deletions will not be forwarded.",
        )
    else:    
        print("Ignoring message event")
    # else:
        # print(event)




#######################
# Listener for the dropdown selection
@app.action("report_forwarding")
def handle_selection(ack, body):
    ack()

    selected_option = body["actions"][0]["selected_option"]["value"]
    db.save_selection(
        selection_ts=body["message"]["ts"],
        selection=selected_option
    )

# Listener for the submit button
@app.action("submit_forwarding")
def handle_submission(ack, body, say, client: WebClient):
    ack()

    user_id = body["user"]["id"]

    # Get the user's selection
    message_record = db.get_message_by_ts(body["message"]["ts"])
    user_selection = message_record.get("fields", {}).get("selection", None)
    if user_selection is not None:
        # TODO: Forward the message
        # TODO: Update the message instead of sending a new one
        if user_selection == "anonymous":
            # Forward anonymously
            say("Anonymously forwarding the report...")
        else:
            say("Forwarding the report with your username...")

        # Update the original message to prevent reuse
        app.client.chat_update(
            channel=message_record["fields"]["dm_channel"],
            ts=message_record["fields"]["selection_ts"],
            blocks=[
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "This report has been submitted."}
                }
            ],
            text="Report submitted" 
        )

        original_text = utils.get_message_body_by_ts(ts=message_record["fields"]["dm_ts"], 
            channel=message_record["fields"]["dm_channel"],
            client=client
        )
        forwarded_ts = client.chat_postMessage(channel=settings.channel, text=original_text).data["ts"]
        db.save_forwarded_ts(dm_ts=message_record["fields"]["dm_ts"], forwarded_ts=forwarded_ts)
        client.chat_postEphemeral(
        channel=message_record["fields"]["dm_channel"],
        user=user_id,
        text="Message content forwarded. Any replies to the forwarded message will be sent back to you as a threaded reply.",
    )
    else:
        say("Please select an option before submitting.")
#######################

@app.command("/shroud-clean-db")
def clean_db(ack, respond: Respond, client: WebClient):
    print("Cleaning database")
    ack()
    db.clean_database(client)
    respond("Removed any records where the DM or the forwarded message no longer exists.")
    print("Cleaned database")   

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

@app.command("/shroud-help")
def help_command(ack, respond: Respond):
    ack()
    manifest_path = importlib.resources.files(__package__).parent / "manifest.yml"
    with open(manifest_path, "r") as f:
        features = yaml.safe_load(f)["features"]

    help_text = "Commands:"
    slash_commands = features.get("slash_commands", [])
    for command in slash_commands:
        try:
            help_text += f"\n`{command['command']} {command['usage_hint']}`: {command['description']}"
        except KeyError:
            # Most likely means that usage_hint is not defined
            help_text += f"\n`{command['command']}`: {command['description']}"
    if len(slash_commands) == 0:
        help_text += "\nNo commands available.\n"
    else: 
        help_text += "\n"
    
    shortcuts = features.get("shortcuts", [])
    help_text += "\nShortcuts:"
    message_shortcuts_text = "Message shortcuts:"
    global_shortcuts_text = "Global shortcuts:"
    for shortcut in shortcuts:
        if shortcut["type"] == "message":
            message_shortcuts_text += f"\n`{shortcut["name"]}`: {shortcut['description']}"
        elif shortcut["type"] == "global":
            global_shortcuts_text += f"\n`{shortcut["name"]}`: {shortcut['description']}"
    if len(shortcuts) == 0:
        help_text += "\nNo shortcuts available."
    else:
        if message_shortcuts_text != "Message shortcuts:":
            help_text += f"\n{message_shortcuts_text}"
        if global_shortcuts_text != "Global shortcuts:":
            help_text += f"\n{global_shortcuts_text}"
    
    respond(help_text)

def main():
    global app
    SocketModeHandler(app, SLACK_APP_TOKEN).start()


if __name__ == "__main__":
    main()
