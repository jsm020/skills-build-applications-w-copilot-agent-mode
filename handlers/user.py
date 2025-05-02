from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from models import SessionLocal, User, Auction, Bid
from utils.deeplink import parse_auction_deeplink
from datetime import datetime

router = Router()

@router.message(CommandStart(deep_link=True))
async def start_with_deeplink(msg: types.Message, command: CommandStart, bot):
    auction_id = parse_auction_deeplink(command.args)
    if not auction_id:
        await msg.answer("Invalid auction link.")
        return

    async with SessionLocal() as session:
        user = await session.execute(
            User.__table__.select().where(User.tg_id == msg.from_user.id)
        )
        user = user.scalar_one_or_none()
        if not user:
            user = User(tg_id=msg.from_user.id, username=msg.from_user.username)
            session.add(user)
            await session.commit()
        auction = await session.get(Auction, auction_id)
        if not auction or not auction.is_active:
            await msg.answer("Auction not found or not active.")
            return
        await msg.answer(
            f"Welcome to the auction!\n\nItem: {auction.item_desc}\nBase price: {auction.base_price}$\nAuction starts now!",
            parse_mode=ParseMode.HTML
        )

@router.message(lambda m: m.text and m.text.isdigit())
async def handle_bid(msg: types.Message, bot):
    bid_amount = float(msg.text)
    async with SessionLocal() as session:
        user_result = await session.execute(
            User.__table__.select().where(User.tg_id == msg.from_user.id)
        )
        user_row = user_result.first()
        if not user_row:
            await msg.answer("User not found.")
            return
        user = user_row._mapping if hasattr(user_row, '_mapping') else user_row
        user_id = user['id'] if isinstance(user, dict) else user.id
        auction_result = await session.execute(
            Auction.__table__.select().where(Auction.is_active == True)
        )
        auction_row = auction_result.first()
        if not auction_row:
            await msg.answer("No active auction.")
            return
        auction = auction_row._mapping if hasattr(auction_row, '_mapping') else auction_row
        auction_id = auction['id'] if isinstance(auction, dict) else auction.id
        base_price = auction['base_price'] if isinstance(auction, dict) else auction.base_price
        last_bid_result = await session.execute(
            Bid.__table__.select()
            .where(Bid.auction_id == auction_id)
            .order_by(Bid.amount.desc())
        )

        last_bid_row = last_bid_result.first()
        if last_bid_row:
            last_bid = last_bid_row._mapping if hasattr(last_bid_row, "_mapping") else last_bid_row
            last_bid_amount = last_bid["amount"] if isinstance(last_bid, dict) else last_bid.amount
        else:
            last_bid_amount = None

        min_bid = base_price if last_bid_amount is None else last_bid_amount + 1

        if bid_amount < min_bid:
            await msg.answer(f"Bid must be at least {min_bid}$")
            return
        bid = Bid(
            auction_id=auction_id,
            user_id=user_id,  # To‘g‘ri ishlatilgan
            amount=bid_amount
        )
        session.add(bid)
        await session.commit()
        await msg.answer(f"Your bid of {bid_amount}$ is accepted!")

        # --- Timer and End Auction Integration ---
        # Import timer and participants from channel handler
        try:
            from handlers.channel import auction_timer, auction_participants
            from services.timer import AuctionTimer
            from main import bot as main_bot
        except ImportError:
            auction_timer = None
            auction_participants = set()
            main_bot = bot

        # Track participants
        auction_participants.add(msg.from_user.id)

        # Start or reset the timer
        # Use auction_timer from channel, do not redeclare as global
        if auction_timer and auction_timer.task:
            auction_timer.reset()
        else:
            auction_timer = AuctionTimer(auction_id, main_bot, list(auction_participants))
            await auction_timer.start()
