from slack_sdk import WebClient

def get_profile_picture_url(user_id, client: WebClient) -> str:
    user_info = client.users_info(user=user_id)
    profile_picture_url = user_info["user"]["profile"]["image_512"]
    return profile_picture_url

def get_name(user_id, client: WebClient) -> str:
    user_info = client.users_info(user=user_id)
    return user_info.data["user"]["real_name"]