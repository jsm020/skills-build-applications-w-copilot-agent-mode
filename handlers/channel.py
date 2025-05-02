from aiogram import Router, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from sqlalchemy import select
from config import ADMIN_IDS, CHANNEL_ID
from models import Bid, SessionLocal, Auction
from utils.deeplink import make_auction_deeplink
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from services.timer import AuctionTimer

# Global timer and participants for auction
auction_timer = None
auction_participants = set()

router = Router()
@router.message(Command("end_auction"))
async def end_auction(msg: types.Message, bot):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("Only admins can end auctions.")
        return

    global auction_timer, auction_participants

    if auction_timer and auction_timer.task:
        auction_timer.stop()

    async with SessionLocal() as session:
        # Eng so‘nggi faol auktsionni topamiz
        result = await session.execute(
            select(Auction).where(Auction.is_active == True).order_by(Auction.start_time.desc())
        )
        auction = result.scalar_one_or_none()
        if not auction:
            await msg.answer("No active auction found.")
            return

        # Auktsionni yopamiz
        auction.is_active = False
        await session.commit()

        # G‘olibni aniqlaymiz
        result = await session.execute(
            select(Bid).where(Bid.auction_id == auction.id).order_by(Bid.amount.desc())
        )
        last_bid = result.scalar_one_or_none()

        if last_bid:
            winner_id = last_bid.user_id
            for user_id in auction_participants:
                await bot.send_message(
                    user_id,
                    f"Auction ended! 🏆 Winner: <a href='tg://user?id={winner_id}'>User {winner_id}</a>\nBid: {last_bid.amount}$",
                    parse_mode=ParseMode.HTML
                )
        else:
            for user_id in auction_participants:
                await bot.send_message(user_id, "Auction ended! ❌ No bids were placed.")

        # Tozalash
        auction_timer = None
        auction_participants.clear()

    await msg.answer("Auction ended and users notified.")


from aiogram import Router, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from config import ADMIN_IDS, CHANNEL_ID
from models import SessionLocal, Auction
from utils.deeplink import make_auction_deeplink
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

@router.message(Command("new_auction"))
async def new_auction(msg: types.Message, bot):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("Only admins can create auctions.")
        return

    # Expecting: /new_auction <base_price> <description>
    if not msg.reply_to_message or not msg.text:
        await msg.answer("Reply to an image/video with /new_auction <base_price> <description>")
        return

    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        await msg.answer("Usage: /new_auction <base_price> <description>")
        return

    base_price_and_desc = args[1]
    base_price, *desc = base_price_and_desc.split(" ", 1)
    try:
        base_price = float(base_price)
    except Exception:
        await msg.answer("Base price must be a number.")
        return

    desc = desc[0] if desc else ""
    media_type, media_file_id = None, None
    if msg.reply_to_message.photo:
        media_type = "photo"
        media_file_id = msg.reply_to_message.photo[-1].file_id
    elif msg.reply_to_message.video:
        media_type = "video"
        media_file_id = msg.reply_to_message.video.file_id
    else:
        await msg.answer("Reply to an image or video.")
        return

    async with SessionLocal() as session:
        auction = Auction(
            item_desc=desc,
            media_type=media_type,
            media_file_id=media_file_id,
            base_price=base_price,
            start_time=datetime.utcnow(),
            is_active=True
        )
        session.add(auction)
        await session.commit()
        await session.refresh(auction)

        # Deep link
        bot_username = (await bot.me()).username
        deeplink = make_auction_deeplink(auction.id, bot_username)

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Join auction", url=deeplink)]
            ]
        )

        # Send to channel
        safe_desc = desc.replace('<', '').replace('>', '')  # Escape HTML tags
        caption = f"<b>{safe_desc}</b>\nBase price: <b>{base_price}$</b>\nAuction starts now!\n\n<a href='{deeplink}'>Join auction</a>"

        if media_type == "photo":
            sent = await bot.send_photo(
                CHANNEL_ID, media_file_id,
                caption=f"<b>{safe_desc}</b>\nBase price: <b>{base_price}$</b>\nAuction starts now!\n\n<a href='{deeplink}'>Join auction</a>",
                parse_mode=ParseMode.HTML,
                reply_markup=kb
            )
        else:
            sent = await bot.send_video(
                CHANNEL_ID, media_file_id,
                caption=f"<b>{safe_desc}</b>\nBase price: <b>{base_price}$</b>\nAuction starts now!\n\n<a href='{deeplink}'>Join auction</a>",
                parse_mode=ParseMode.HTML,
                reply_markup=kb
            )

        auction.channel_msg_id = sent.message_id
        await session.commit()

    await msg.answer(f"Auction posted to channel.\n\nTo join, click: {deeplink}")
