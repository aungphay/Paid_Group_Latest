from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from bot import CMD, LOGGER
from bot.helpers.translations import lang
from bot.helpers.utils.clean import clean_up
from bot.helpers.utils.check_link import check_link
from bot.helpers.database.postgres_impl import user_settings
from bot.helpers.utils.auth_check import check_id, checkLogins
from bot.helpers.qobuz.handler import qobuz
from bot.helpers.deezer.handler import deezerdl
from bot.helpers.kkbox.kkbox_helper import kkbox
from bot.helpers.tidal_func.events import startTidal
from bot.helpers.spotify.handler import spotify_dl

@Client.on_message(filters.command(CMD.DOWNLOAD))
async def download_track(bot, update):
    # Extract message from update, handle CallbackQuery or invalid update
    message = update if isinstance(update, Message) else (update.message if isinstance(update, CallbackQuery) else None)
    if not message or not hasattr(message, 'chat') or not hasattr(message, 'id'):
        LOGGER.error(f"Invalid update type or message: {update}")
        return await bot.send_message(
            chat_id=getattr(update, 'chat', {}).get('id', update.from_user.id if hasattr(update, 'from_user') else None),
            text="Invalid command usage. Please use this command with a valid message.",
            reply_to_message_id=getattr(update, 'id', None)
        )

    if not await check_id(message=message):
        return await bot.send_message(
            chat_id=message.chat.id,
            text="You are not authorized to download.",
            reply_to_message_id=message.id
        )

    try:
        if message.reply_to_message:
            link = message.reply_to_message.text
            reply_to_id = message.reply_to_message.id
        else:
            link = message.text.split(" ", maxsplit=1)[1]
            reply_to_id = message.id
    except (IndexError, AttributeError):
        return await bot.send_message(
            chat_id=message.chat.id,
            text=lang.select.ERR_NO_LINK,
            reply_to_message_id=message.id
        )

    if link:
        provider = await check_link(link)
        if provider:
            err, err_msg = await checkLogins(provider)
            if err:
                return await bot.send_message(
                    chat_id=message.chat.id,
                    text=err_msg,
                    reply_to_message_id=message.id
                )
        else:
            return await bot.send_message(
                chat_id=message.chat.id,
                text=lang.select.ERR_LINK_RECOGNITION,
                reply_to_message_id=message.id
            )

        # Check if from_user exists before logging
        user_name = message.from_user.first_name if message.from_user else "Unknown User"
        LOGGER.info(f"Download Initiated By - {user_name}")

        msg = await bot.send_message(
            chat_id=message.chat.id,
            text=lang.select.START_DOWNLOAD,
            reply_to_message_id=message.id
        )
        botmsg_id = msg.id

        # Handle username or first_name for u_name
        if message.from_user:
            if message.from_user.username:
                u_name = f"@{message.from_user.username}"
            else:
                u_name = f'<a href="tg://user?id={message.from_user.id}">{message.from_user.first_name}</a>'
        else:
            u_name = "Anonymous User"

        user_settings.set_var(message.chat.id, "ON_TASK", True)
        try:
            if provider == "tidal":
                await startTidal(link, bot, message.chat.id, reply_to_id, message.from_user.id if message.from_user else None, u_name)
            elif provider == "kkbox":
                await kkbox.start(link, bot, message, reply_to_id, u_name)
            elif provider == 'qobuz':
                await qobuz.start(link, bot, message, reply_to_id, u_name)
            elif provider == 'deezer':
                await deezerdl.start(link, bot, message, reply_to_id, u_name)
            elif provider == 'spotify':
                await spotify_dl.start(link, bot, message, reply_to_id, u_name)
            await bot.delete_messages(message.chat.id, msg.id)
            await bot.send_message(
                chat_id=message.chat.id,
                text=lang.select.TASK_COMPLETED,
                reply_to_message_id=message.id
            )
        except Exception as e:
            LOGGER.error(f"Download error: {str(e)}", exc_info=True)
            await bot.send_message(
                chat_id=message.chat.id,
                text=f"Error: {str(e)}",
                reply_to_message_id=message.id
            )
        user_settings.set_var(message.chat.id, "ON_TASK", False)

        await clean_up(reply_to_id, provider)
