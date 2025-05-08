from bot import Config
import logging

from bot.helpers.translations import lang
from bot.helpers.tidal_func.events import checkLoginTidal
from bot.helpers.database.postgres_impl import users_db, admins_db, chats_db, user_settings, set_db

# Initialize logging
LOGGER = logging.getLogger(__name__)

allowed_chats = []
allowed_users = []
admins = []

async def get_chats(return_msg=False):
    # CHATS 
    database_chats = chats_db.get_chats()
    for chat in Config.AUTH_CHAT:
        if chat not in allowed_chats:
            allowed_chats.append(chat)
    for chat in database_chats:
        if chat is not None and chat[0] is not None and chat[0] not in allowed_chats:
            allowed_chats.append(chat[0])
    # ADMINS
    database_admins = admins_db.get_admins()
    for admin in Config.ADMINS:
        if admin not in admins:
            admins.append(admin)
    for admin in database_admins:
        if admin is not None and admin[0] is not None and admin[0] not in admins:
            admins.append(admin[0])
    # USERS
    if not Config.IS_BOT_PUBLIC == "True":
        database_users = users_db.get_users()
        if Config.AUTH_USERS == "":
            pass
        else:
            for user in Config.AUTH_USERS:
                if user not in allowed_users:
                    allowed_users.append(user)
            for user in database_users:
                if user is not None and user[0] is not None and user[0] not in allowed_users:
                    allowed_users.append(user[0])

    if return_msg:
        msg = "<b>ALLOWED CHATS</b>"
        for chat in allowed_chats:
            msg += f"\n<code>{chat}</code>"

        msg += "\n\n<b>ALLOWED USERS</b>"
        if Config.IS_BOT_PUBLIC == "True":
            msg += "\nAllowed For Everyone"
        try:
            for user in allowed_users:
                msg += f"\n<code>{user}</code>"
        except:
            pass

        msg += "\n\n<b>ADMINS</b>"
        for admin in admins:
            msg += f"\n<code>{admin}</code>"

        return msg

async def check_id(id=None, message=None, restricted=False):
    all_list = allowed_chats + allowed_users + admins
    if restricted:
        if id in admins:
            return True
        else:
            return False
    else:
        # Ensure message is valid
        if not message or not hasattr(message, 'chat') or not hasattr(message, 'from_user'):
            LOGGER.warning("Invalid message object or missing attributes")
            return False

        # Seperating Group and PM
        user_id = message.from_user.id if message.from_user else None
        chat_id = message.chat.id

        if user_id is None:
            LOGGER.warning("No user info available for this message, using chat ID")
            id_to_check = chat_id
        elif user_id != chat_id:
            id_to_check = chat_id  # Group chat case
        else:
            id_to_check = user_id  # Private chat case

        if Config.ANIT_SPAM_MODE == "True":
            check = user_settings.get_var(id_to_check, "ON_TASK")
            if check:
                await message.reply_text(lang.select.ANTI_SPAM_WAIT)
                return False

        # Additional validation for public bot
        if Config.IS_BOT_PUBLIC == "True":
            if user_id is None and chat_id not in all_list:
                LOGGER.warning("Public bot access attempted without user info and chat not in allowed list")
                return False
            return True
        elif id_to_check in all_list:
            return True
        else:
            return False

async def checkLogins(provider):
    # return Error and Error Message
    if provider == "tidal":
        auth, msg = await checkLoginTidal()
        if auth:
            return False, msg
        else:
            return True, msg
    elif provider == "qobuz":
        auth, _ = set_db.get_variable("QOBUZ_AUTH")
        if not auth:
            return True, lang.select.QOBUZ_NOT_AUTH
        return False, None
    elif provider == "deezer":
        auth, _ = set_db.get_variable("DEEZER_AUTH")
        if not auth:
            return True, lang.select.DEEZER_NOT_AUTH
        return False, None
    elif provider == "kkbox":
        auth, _ = set_db.get_variable("KKBOX_AUTH")
        if not auth:
            return True, lang.select.KKBOX_NOT_AUTH
        return False, None
    elif provider == "spotify":
        auth, _ = set_db.get_variable("SPOTIFY_AUTH")
        if not auth:
            return True, lang.select.SPOTIFY_NOT_AUTH
        return False, None
    else:
        return False, None
