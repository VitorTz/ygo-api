from pydantic import BaseModel
from enum import Enum, auto


class Image(BaseModel):

    image_url: str
    image_url_cropped: str
    image_url_small: str


class ImageType(Enum):

    Normal = auto()
    Cropped = auto()
    Small = auto()

    @staticmethod
    def to_string(image_type: 'ImageType') -> str | None:
        match image_type:
            case ImageType.Normal:
                return "normal"
            case ImageType.Cropped:
                return "cropped"
            case ImageType.Small:
                return "small"
            case _:
                return None