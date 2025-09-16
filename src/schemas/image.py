from pydantic import BaseModel


class Image(BaseModel):

    image_url: str
    image_url_cropped: str
    image_url_small: str