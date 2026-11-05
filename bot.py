"""
Телеграм-бот: команди + кнопка запуску міні-застосунку.

Запуск окремо:  python bot.py   (потрібна змінна BOT_TOKEN)
Разом з веб-сервером і збором даних:  python run.py   (рекомендовано)

Міні-застосунок відкривається за WEBAPP_URL (HTTPS!). Дивіться README.md.
"""

import html

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonWebApp,
                      Update, WebAppInfo)
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes

from analysis import analyze
from config import ALL_TICKERS, BOT_TOKEN, WEBAPP_URL

DISCLAIMER = "Увага: це навчальна розробка, а не фінансова порада."


def _webapp_markup():
    """Кнопка під повідомленням, що відкриває міні-застосунок (якщо задано URL)."""
    if not WEBAPP_URL:
        return None
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("📊 Відкрити аналітику", web_app=WebAppInfo(url=WEBAPP_URL))
    ]])


def _get_ticker(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.args[0].upper() if context.args else "BTC"


async def _check_ticker(update: Update, ticker: str) -> bool:
    """False (і відповідь користувачу), якщо тікер невідомий."""
    if ticker not in ALL_TICKERS:
        await update.message.reply_text(
            f"Невідомий тікер {ticker}. Доступні: {', '.join(ALL_TICKERS)}")
        return False
    return True


def _fmt(value: float, kind: str) -> str:
    return f"{value:,.0f}".replace(",", " ") if (kind == "crypto" and value >= 1000) else f"{value:.4f}" if kind == "currency" else f"{value:.2f}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Привіт! Я аналізую курси криптовалют і валют та прогнозую їх кількома методами.\n\n"
        "Команди:\n"
        "/price BTC — поточний курс\n"
        "/analyze BTC — порівняння методів і прогноз\n"
        "/rsi BTC — індекс відносної сили\n\n"
        f"Тікери: {', '.join(ALL_TICKERS)}\n{DISCLAIMER}"
    )
    if not WEBAPP_URL:
        text += "\n\n(Міні-застосунок не налаштовано: задайте WEBAPP_URL.)"
    await update.message.reply_text(text, reply_markup=_webapp_markup())


async def app_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/app — відкрити міні-застосунок."""
    if not WEBAPP_URL:
        await update.message.reply_text("Міні-застосунок не налаштовано: задайте WEBAPP_URL (див. README).")
        return
    await update.message.reply_text("Відкрийте аналітику:", reply_markup=_webapp_markup())


async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ticker = _get_ticker(context)
    if not await _check_ticker(update, ticker):
        return
    a = analyze(ticker)
    if a is None:
        await update.message.reply_text("Даних по цьому тікеру ще немає.")
        return
    ch = a["change_1d_pct"]
    ch_txt = "" if ch is None else f" ({'▲' if ch > 0 else '▼' if ch < 0 else '•'} {ch:+.2f}% за добу)"
    await update.message.reply_text(
        f"{a['name']} ({ticker}): {_fmt(a['last_price'], a['kind'])} {a['currency_label']}{ch_txt}\n"
        f"Станом на {a['last_date']}",
        reply_markup=_webapp_markup())


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ticker = _get_ticker(context)
    if not await _check_ticker(update, ticker):
        return
    a = analyze(ticker)
    if a is None or not a["metrics"]:
        await update.message.reply_text("Недостатньо даних для аналізу.")
        return
    lines = [f"<b>{html.escape(a['name'])} ({ticker})</b>", "", "Похибка прогнозу на добу вперед:"]
    for m in a["metrics"]:
        mark = " ✅" if m["method"] == a["best_method"] else ""
        lines.append(f"• {html.escape(m['method'])}: MAPE {m['MAPE_%']:.2f}%, "
                     f"напрямок {m['accuracy_%']:.0f}%{mark}")
    f = a["forecast"]
    if f:
        lines += ["", f"Прогноз ({html.escape(f['method'])}):",
                  f"завтра — {_fmt(f['values'][0], a['kind'])}, "
                  f"через {len(f['values'])} днів — {_fmt(f['values'][-1], a['kind'])} {a['currency_label']}"]
    lines += ["", DISCLAIMER]
    await update.message.reply_text("\n".join(lines), parse_mode="HTML", reply_markup=_webapp_markup())


async def rsi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ticker = _get_ticker(context)
    if not await _check_ticker(update, ticker):
        return
    a = analyze(ticker)
    if a is None:
        await update.message.reply_text("Даних по цьому тікеру ще немає.")
        return
    await update.message.reply_text(f"RSI {ticker}: {a['rsi']:.1f} — {a['rsi_label']}")


async def _post_init(app: Application):
    """Додає синю кнопку меню «Аналітика» біля поля вводу."""
    if WEBAPP_URL:
        await app.bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text="Аналітика", web_app=WebAppInfo(url=WEBAPP_URL)))


def build_app() -> Application:
    if not BOT_TOKEN:
        raise SystemExit("Не задано BOT_TOKEN. Див. README.md.")
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(_post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("app", app_command))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("analyze", analyze_command))
    app.add_handler(CommandHandler("rsi", rsi_command))
    return app


def main():
    build_app().run_polling()


if __name__ == "__main__":
    main()
