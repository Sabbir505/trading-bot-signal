import os
from datetime import datetime, timedelta, timezone
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = -5087254229  # <-- replace with your real group ID

# Store last trades with details
# Example: { "SOL": {"msg_id": 12345, "is_long_term": False}, ... }
last_trade_messages = {}

# China timezone (UTC+8)
CHINA_TZ = timezone(timedelta(hours=8))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    words = text.split()

    if len(words) == 0:
        return

    # --- CLOSE ALL ---
    if text == "close all":
        if not last_trade_messages:
            await context.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text="⚠️ No active positions to close."
            )
            return

        closed_any = False
        for symbol, info in last_trade_messages.items():
            if not info.get("is_long_term", False):  # skip long-term
                msg_id = info["msg_id"]
                await context.bot.send_message(
                    chat_id=GROUP_CHAT_ID,
                    text=f"💼 **Close {symbol}USDT**",
                    reply_to_message_id=msg_id,
                    parse_mode="Markdown"
                )
                closed_any = True

        if closed_any:
            await context.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text="✅ All short/mid-term positions closed."
            )
        else:
            await context.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text="💎 Only long-term positions are open — nothing to close."
            )
        return

    # --- CLOSE SINGLE ---
    if words[0] == "close" and len(words) >= 2:
        symbol = words[1].upper()
        if symbol in last_trade_messages:
            info = last_trade_messages[symbol]
            if info.get("is_long_term", False):
                await context.bot.send_message(
                    chat_id=GROUP_CHAT_ID,
                    text=f"💎 {symbol}USDT is a long-term SPOT position — not closed."
                )
            else:
                msg_id = info["msg_id"]
                await context.bot.send_message(
                    chat_id=GROUP_CHAT_ID,
                    text=f"💼 **Close {symbol}USDT**",
                    reply_to_message_id=msg_id,
                    parse_mode="Markdown"
                )
        else:
            await context.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=f"⚠️ No active position found for {symbol}"
            )
        return

    # --- BUY / SELL COMMAND ---
    if words[0] in ["buy", "sell"]:
        action = words[0].upper()
        is_long_term = "long" in words or "spot" in words

        try:
            symbol = next(w for w in words if w not in ["buy", "sell", "long", "spot"]).upper()
            price = next((w for w in reversed(words) if w.replace('.', '', 1).isdigit()), None)
        except StopIteration:
            await update.message.reply_text("⚠️ Format: buy <symbol> <price>")
            return

        # Current time in China
        now = datetime.now(CHINA_TZ)
        formatted_time = now.strftime("%Y-%m-%d %I:%M %p")  # 12-hour format with AM/PM

        emoji = "🟢" if action == "BUY" else "🔴"

        msg_text = (
            f"{emoji} **#{symbol}USDT**\n"
            f"**10X LEVERAGE**\n"
            f"**1% CAPITAL**\n"
            f"**{action} AT {price}**\n"
            f"🕒 *{formatted_time} (China Time)*"
        )

        if is_long_term:
            msg_text += "\n\n💎 *This is a LONG-TERM SPOT position.*"

        sent = await context.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=msg_text,
            parse_mode="Markdown"
        )

        # Save trade info
        last_trade_messages[symbol] = {"msg_id": sent.message_id, "is_long_term": is_long_term}
        return


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
