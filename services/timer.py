import asyncio
from models import SessionLocal, Auction, Bid

class AuctionTimer:
    def __init__(self, auction_id, bot, participants):
        self.auction_id = auction_id
        self.bot = bot
        self.participants = participants
        self.task = None
        self.time_left = 300  # 5 minutes

    async def start(self):
        self.task = asyncio.create_task(self.run())

    async def run(self):
        while self.time_left > 0:
            if self.time_left in [300, 60, 10]:
                for user_id in self.participants:
                    await self.bot.send_message(user_id, f"{self.time_left//60 if self.time_left>=60 else self.time_left}s left to bid!")
            await asyncio.sleep(1)
            self.time_left -= 1
        # Timer ended, announce winner
        async with SessionLocal() as session:
            auction = await session.get(Auction, self.auction_id)
            last_bid = await session.scalar(Bid.select().where(Bid.auction_id == self.auction_id).order_by(Bid.amount.desc()))
            if last_bid:
                winner_id = last_bid.user_id
                for user_id in self.participants:
                    await self.bot.send_message(user_id, f"Auction ended! Winner: {winner_id}")
            else:
                for user_id in self.participants:
                    await self.bot.send_message(user_id, "Auction ended! No bids placed.")

    def reset(self):
        self.time_left = 300

    def stop(self):
        if self.task:
            self.task.cancel()
