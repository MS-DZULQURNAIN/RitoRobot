from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, Filters
from telegram.utils.helpers import escape_markdown

import RitoRobot.modules.sql.rules_sql as sql
from RitoRobot import dispatcher
from RitoRobot.modules.helper_funcs.chat_status import connection_status, user_admin
from RitoRobot.modules.helper_funcs.string_handling import markdown_parser


@connection_status
def get_rules(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    send_rules(update, chat_id)


# Do not async - not from a handler
def send_rules(update, chat_id, from_pm=False):
    bot = dispatcher.bot
    user = update.effective_user  # type: Optional[User]
    reply_msg = update.message.reply_to_message
    try:
        chat = bot.get_chat(chat_id)
    except BadRequest as excp:
        if excp.message == "Chat not found" and from_pm:
            bot.send_message(
                user.id,
                "Pintasan aturan untuk obrolan ini belum disetel dengan benar! Minta admin untuk "
                "Perbaiki ini.\Mungkin mereka lupa tanda hubung di ID",
            )
            return
        raise

    rules = sql.get_rules(chat_id)
    text = f"Aturan untuk *{escape_markdown(chat.title)}* adalah:\n\n{rules}"

    if from_pm and rules:
        bot.send_message(
            user.id,
            text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
    elif from_pm:
        bot.send_message(
            user.id,
            "Admin grup belum menetapkan aturan apa pun untuk obrolan ini. "
            "Ini mungkin tidak berarti itu melanggar hukum...!",
        )
    elif rules and reply_msg:
        reply_msg.reply_text(
            "Silakan klik tombol di bawah ini untuk melihat aturannya.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="ᴀᴛᴜʀᴀɴ ɢʀᴏᴜᴘ",
                            url=f"t.me/{bot.username}?start={chat_id}",
                        ),
                    ],
                ],
            ),
        )
    elif rules:
        update.effective_message.reply_text(
            "Silakan klik tombol di bawah ini untuk melihat aturannya.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="ᴀᴛᴜʀᴀɴ ɢʀᴏᴜᴘ",
                            url=f"t.me/{bot.username}?start={chat_id}",
                        ),
                    ],
                ],
            ),
        )
    else:
        update.effective_message.reply_text(
            "Admin grup belum menetapkan aturan apa pun untuk obrolan ini. "
            "Ini mungkin tidak berarti itu melanggar hukum...!",
        )


@connection_status
@user_admin
def set_rules(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    msg = update.effective_message  # type: Optional[Message]
    raw_text = msg.text
    args = raw_text.split(None, 1)  # use python's maxsplit to separate cmd and args
    if len(args) == 2:
        txt = args[1]
        offset = len(txt) - len(raw_text)  # set correct offset relative to command
        markdown_rules = markdown_parser(
            txt,
            entities=msg.parse_entities(),
            offset=offset,
        )

        sql.set_rules(chat_id, markdown_rules)
        update.effective_message.reply_text("Berhasil menetapkan aturan untuk grup ini.")


@connection_status
@user_admin
def clear_rules(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    sql.set_rules(chat_id, "")
    update.effective_message.reply_text("Successfully cleared rules!")


def __stats__():
    return f"• {sql.num_chats()} groups have rules."


def __import_data__(chat_id, data):
    # set chat rules
    rules = data.get("info", {}).get("rules", "")
    sql.set_rules(chat_id, rules)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return f"This chat has had it's rules set: `{bool(sql.get_rules(chat_id))}`"


__help__ = """
 ᐉ `/rules`*:* get the rules for this chat.
*Admins only:*
 ᐉ `/setrules <your rules here>`*:* set the rules for this chat.
 ᐉ `/clearrules`*:* clear the rules for this chat.
"""

__mod_name__ = "Rules"

GET_RULES_HANDLER = CommandHandler("rules", get_rules)
SET_RULES_HANDLER = CommandHandler("setrules", set_rules)
RESET_RULES_HANDLER = CommandHandler("clearrules", clear_rules)

dispatcher.add_handler(GET_RULES_HANDLER)
dispatcher.add_handler(SET_RULES_HANDLER)
dispatcher.add_handler(RESET_RULES_HANDLER)
