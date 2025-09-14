from multiprocessing.pool import ThreadPool
from abc import ABC, abstractmethod
from botocore.config import Config
from dotenv import load_dotenv
from random import randint
from pathlib import Path
import boto3
import uuid
import sys
import os


load_dotenv()


S3 = boto3.client(
    service_name="s3",
    endpoint_url=f"https://{os.getenv("R2_ACCOUNT_ID")}.r2.cloudflarestorage.com",
    aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3v4"),
    region_name="enam"
)


class S3Exception(Exception):

    def __init__(self, message: str):
        super().__init__(f"[S3 EXCEPTION] => {message}")


class S3Client(ABC):

    @abstractmethod
    def __init__(self, prefix: str, bucket: str):
        self.__bucket = bucket
        self.__prefix = prefix
        self.__s3 = S3

    def generate_uuid(self, s: str) -> uuid.UUID:
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, s))

    def upload(self, file: Path, name: str) -> str | None:
        if not file.exists() or not file.is_file():
            raise S3Exception(f"[{file} IS NOT A FILE OR NOT EXISTS]")
        try:
            self.__s3.upload_file(file, self.__bucket, name)
            return self.__prefix + name
        except Exception as e:
            raise S3Exception(f"[file: {file}] [name: {name}] | {e}")

    def delete_folder(self, prefix: str):
        paginator = self.__s3.get_paginator("list_objects_v2")
        delete_us = dict(Objects=[])

        for page in paginator.paginate(Bucket=self.__bucket, Prefix=prefix):
            if "Contents" in page:
                for obj in page["Contents"]:
                    delete_us["Objects"].append({"Key": obj["Key"]})
                
                if len(delete_us["Objects"]) >= 1000:
                    S3.delete_objects(Bucket=self.__bucket, Delete=delete_us)
                    print(f"[DELETED] [{len(delete_us['Objects'])}]")
                    delete_us = dict(Objects=[])
        
        if delete_us["Objects"]:
            S3.delete_objects(Bucket=self.__bucket, Delete=delete_us)
            print(f"[DELETED] [{len(delete_us['Objects'])}]")

    def close(self) -> None:
        self.__s3.close()


class YgoS3(S3Client):

    def __init__(self):
        super().__init__(bucket = os.getenv("R2_BUCKET_NAME"), prefix=os.getenv("R2_PREFIX"))

    def upload_card(self, card_id: int, type: str, file: Path) -> str | None:
        name = f"ygo/cards/{type}/{str(card_id)[0]}/{card_id}-{self.generate_uuid(str(card_id))}{file.suffix}"
        return self.upload(file, name)
    
