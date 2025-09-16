from pydantic import BaseModel


class CardPrice(BaseModel):

    card_id: int
    amazon_price: int
    cardmarket_price: int
    coolstuffinc_price: int
    ebay_price: int
    tcgplayer_price: int