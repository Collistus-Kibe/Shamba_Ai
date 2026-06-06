from sqlalchemy.orm import Session
from app.models.models import MarketPrice
from typing import List, Optional

class MarketService:
    @staticmethod
    def get_prices(
        db: Session, 
        crop: Optional[str] = None, 
        region: Optional[str] = None
    ) -> List[MarketPrice]:
        query = db.query(MarketPrice)
        if crop:
            query = query.filter(MarketPrice.crop.ilike(f"%{crop}%"))
        if region:
            query = query.filter(MarketPrice.region.ilike(f"%{region}%"))
        return query.all()

    @staticmethod
    def seed_prices_if_empty(db: Session):
        """
        Seeds standard agricultural commodity price records if database is empty.
        """
        if db.query(MarketPrice).count() > 0:
            return
            
        prices = [
            MarketPrice(
                crop="Maize",
                region="Rift Valley",
                market_name="Eldoret Central",
                current_price=3800.0,
                currency="KES",
                price_unit="90kg Bag",
                trend_percentage=5.2,
                forecast_info="Upward trend expected to continue due to dry spell impacts on planting seasons."
            ),
            MarketPrice(
                crop="Maize",
                region="Nairobi",
                market_name="Nairobi Wakulima",
                current_price=3450.0,
                currency="KES",
                price_unit="90kg Bag",
                trend_percentage=2.1,
                forecast_info="Stable prices with high supply volumes incoming from cross-border trade."
            ),
            MarketPrice(
                crop="Beans (Rosecoco)",
                region="Nairobi",
                market_name="Nairobi Wakulima",
                current_price=8200.0,
                currency="KES",
                price_unit="90kg Bag",
                trend_percentage=-1.5,
                forecast_info="Marginal price contraction as secondary harvests arrive in the market."
            ),
            MarketPrice(
                crop="Beans (Rosecoco)",
                region="Nyanza",
                market_name="Kisumu Jubilee",
                current_price=8400.0,
                currency="KES",
                price_unit="90kg Bag",
                trend_percentage=0.5,
                forecast_info="Prices remain high due to localized heavy rain patterns affecting logistics."
            ),
            MarketPrice(
                crop="Tomatoes",
                region="Nairobi",
                market_name="Wakulima Market",
                current_price=4500.0,
                currency="KES",
                price_unit="64kg Crate",
                trend_percentage=0.0,
                forecast_info="Prices are holding steady. Expected to remain unchanged for the next 2 weeks."
            ),
            MarketPrice(
                crop="Coffee (Arabica)",
                region="Central",
                market_name="Nairobi Coffee Exchange",
                current_price=12500.0,
                currency="KES",
                price_unit="50kg Bag",
                trend_percentage=4.8,
                forecast_info="International demand triggers price hikes. Yield quality premium is increasing."
            ),
            MarketPrice(
                crop="Soybeans",
                region="Rift Valley",
                market_name="Nakuru Wholesale",
                current_price=6200.0,
                currency="KES",
                price_unit="90kg Bag",
                trend_percentage=1.8,
                forecast_info="Animal feed manufacturers driving steady buy cycles. Good outlook for soy farmers."
            )
        ]
        
        try:
            db.add_all(prices)
            db.commit()
            print("Successfully seeded crop market prices.")
        except Exception as e:
            db.rollback()
            print(f"Error seeding market prices: {e}")
            raise e
