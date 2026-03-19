import logging
from app.telegram.sender import send_message
from app.services import users, topics, subscriptions

logger = logging.getLogger(__name__)


def handle_start(chat_id: int, user: dict, args: list[str]) -> None:
    users.ensure_user(chat_id=chat_id, user_info=user)
    text = (
        "👋 Привіт! Я бот, який надсилає корисну інформацію за підпискою.\n\n"
        "📋 /topics — список доступних тем\n"
        "✅ /subscribe <тема> — підписатися\n"
        "❌ /unsubscribe <тема> — відписатися\n"
        "📌 /mysubs — мої підписки\n"
        "❓ /help — допомога"
    )
    send_message(chat_id, text, parse_mode=None)


def handle_help(chat_id: int, user: dict, args: list[str]) -> None:
    text = (
        "*Доступні команди:*\n\n"
        "/topics — список доступних тем\n"
        "/subscribe <topic\\_id> — підписатися на тему\n"
        "/unsubscribe <topic\\_id> — відписатися від теми\n"
        "/mysubs — переглянути мої підписки\n"
        "/help — ця довідка"
    )
    send_message(chat_id, text)


def handle_topics(chat_id: int, user: dict, args: list[str]) -> None:
    all_topics = topics.list_enabled_topics()
    if not all_topics:
        send_message(chat_id, "Поки немає доступних тем.", parse_mode=None)
        return

    lines = ["*Доступні теми:*\n"]
    for t in all_topics:
        lines.append(f"• `{t['id']}` — {t['description']}")
    lines.append("\nПідписатися: /subscribe <topic\\_id>")
    send_message(chat_id, "\n".join(lines))


def handle_subscribe(chat_id: int, user: dict, args: list[str]) -> None:
    if not args:
        send_message(chat_id, "Вкажіть тему: /subscribe <topic\\_id>\nСписок тем: /topics")
        return

    topic_id = args[0].lower()

    topic = topics.get_topic(topic_id)
    if not topic:
        send_message(chat_id, f"Тему `{topic_id}` не знайдено. Перевірте /topics")
        return

    users.ensure_user(chat_id=chat_id, user_info=user)
    already = subscriptions.subscribe(user_id=str(user.get("id", chat_id)), chat_id=chat_id, topic_id=topic_id)

    if already:
        send_message(chat_id, f"Ви вже підписані на `{topic_id}` ✅")
    else:
        send_message(chat_id, f"Підписано на `{topic_id}` ✅")


def handle_unsubscribe(chat_id: int, user: dict, args: list[str]) -> None:
    if not args:
        send_message(chat_id, "Вкажіть тему: /unsubscribe <topic\\_id>\nМої підписки: /mysubs")
        return

    topic_id = args[0].lower()
    user_id = str(user.get("id", chat_id))
    was_active = subscriptions.unsubscribe(user_id=user_id, topic_id=topic_id)

    if was_active:
        send_message(chat_id, f"Відписано від `{topic_id}` ❌")
    else:
        send_message(chat_id, f"Ви не були підписані на `{topic_id}`.")


def handle_mysubs(chat_id: int, user: dict, args: list[str]) -> None:
    user_id = str(user.get("id", chat_id))
    subs = subscriptions.get_user_subscriptions(user_id)

    if not subs:
        send_message(chat_id, "У вас немає активних підписок.\nПерегляньте /topics")
        return

    lines = ["*Ваші підписки:*\n"]
    for s in subs:
        lines.append(f"• `{s['topic_id']}`")
    lines.append("\nВідписатися: /unsubscribe <topic\\_id>")
    send_message(chat_id, "\n".join(lines))
