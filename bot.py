
from pydoc import cli
from nio import (
    AsyncClient,
    MatrixRoom,
    RoomMessageText,
    AsyncClientConfig,
    LoginResponse,
)

import asyncio
import sys
import json
import os

HOMESERVER = "matrix.org"
USER_ID = "user:matrix.org"
PASSWORD = ""
STORE_PATH = "store/"
CREDENTIAL_PATH = "credential"
DEVICE_NAME = "bot device"


def write_details_to_disk(resp, homeserver):
    user_id = resp.user_id
    config_file_name = "{}/{}_credentials.json".format(
        CREDENTIAL_PATH, user_id
    )
    with open(config_file_name, "w") as f:
        # write the login details to disk
        json.dump(
            {
                "homeserver": homeserver,  # e.g. "https://matrix.example.org"
                "user_id": user_id,  # e.g. "@user:example.org"
                "device_id": resp.device_id,  # device ID, 10 uppercase letters
                "access_token": resp.access_token,  # cryptogr. access token
            },
            f,
        )

async def message_callback(room: MatrixRoom, event: RoomMessageText) -> None:
    print(
        f"Message received in room {room.display_name}\n"
        f"{room.user_name(event.sender)} | {event.body}"
    )

async def login_or_restore() -> AsyncClient:

    client_config = AsyncClientConfig(
            max_limit_exceeded=0,
            max_timeouts=0,
            request_timeout=0,
            store_sync_tokens=True,
            encryption_enabled=True,
        )

    client = AsyncClient(HOMESERVER, USER_ID, store_path=STORE_PATH,config=client_config)

    file_credential = "{}/{}_credentials.json".format(CREDENTIAL_PATH, USER_ID)

    if os.path.exists(file_credential) and os.path.isfile(
            file_credential
        ):

        with open(file_credential, "r") as f:

            config = json.load(f)

            client = AsyncClient(
                config["homeserver"],
                config["user_id"],
                device_id=config["device_id"],
                store_path=STORE_PATH,
                config=client_config,
            )
            client.restore_login(
                user_id=config["user_id"],
                device_id=config["device_id"],
                access_token=config["access_token"],
            )
    
    else:
 
        resp = await client.login(password=PASSWORD, device_name=DEVICE_NAME)
  
        if isinstance(resp, LoginResponse):
            write_details_to_disk(resp, HOMESERVER)
    
    client.add_event_callback(message_callback, RoomMessageText)

    await client.sync(full_state=True)

    return client

async def send_message(client:AsyncClient , room_id: str, message: str) -> None:

    await client.room_send(
            room_id=room_id,
            message_type="m.room.message",
            content={"msgtype": "m.text", "body": message},
            ignore_unverified_devices=True
        )

async def main():

    client = await login_or_restore()

    #await  send_message(client, room_id, "Hello World !")

    await client.sync_forever(timeout=30000)  # milliseconds


try:
    asyncio.get_event_loop().run_until_complete(main())
except Exception:
    sys.exit(1)
except KeyboardInterrupt:
    sys.exit(1)