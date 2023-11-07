import os
import uuid
from typing import List

from fastapi import UploadFile

from common.logger import module_logger

MEDIA_DIR = 'media'
CHUNK_SIZE = 2 ** 20  # 1MB
logger = module_logger(__name__)


class FileWriter:

    @staticmethod
    async def chunked_copy(file: UploadFile, destination_path):
        await file.seek(0)
        with open(destination_path, "wb") as buffer:
            while True:
                contents = await file.read(CHUNK_SIZE)
                if not contents:
                    logger.info(f"Src completely consumed for {file.filename}")
                    break
                logger.info(f"Consumed {len(contents)} bytes from Src file")
                buffer.write(contents)

    async def save(self, files: List[UploadFile]):
        os.makedirs(MEDIA_DIR, exist_ok=True)
        paths = []
        for file in files:
            fullpath = os.path.join(MEDIA_DIR, f'{uuid.uuid4()}-{file.filename}')
            await self.chunked_copy(file, fullpath)
            paths.append(fullpath)
        return paths

    async def save_single(self, file: UploadFile):
        fullpath = os.path.join(MEDIA_DIR, f'{uuid.uuid4()}-{file.filename}')
        await self.chunked_copy(file, fullpath)
        return fullpath

    async def save_media_get_details(self, file: UploadFile):
        logger.info('Saving image while getting path and extension')
        file_type = None
        if 'image' in file.content_type:
            logger.info('uploaded file is an Image')
            file_type = 'image'
        elif 'video' in file.content_type:
            logger.info('uploaded file is a video')
            file_type = 'video'
        file_path = await self.save_single(file)
        return file_path, file_type

