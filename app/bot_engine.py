import docker

from common.configs import BOT_TOKEN, MONGODB_DB_NAME, MONGODB_HOST, MONGODB_PASSWORD, MONGODB_USERNAME, \
    BOT_ENGINE_IMAGE, DOCKER_NETWORK, BOT_USERNAME
from common.logger import module_logger

logger = module_logger(__name__)


class BotEngineUpdate:
    def __init__(self):
        self.bot_username = BOT_USERNAME
        self.container_name = 'product-bot_container'

    def _prepare_bot(self):
        logger.info('preparing Bot to launch')

        data = {
            'TELEGRAM_BOT': BOT_TOKEN,
            'MONGODB_USERNAME': MONGODB_USERNAME,
            'MONGODB_PASSWORD': MONGODB_PASSWORD,
            'MONGODB_HOST': MONGODB_HOST,
            'MONGODB_DB_NAME': MONGODB_DB_NAME
        }
        logger.debug(f'Bot Engine Upload Payload {data}')
        self.env = data

    def restart_bot_engine(self):
        logger.info('Restarting Bot')
        try:
            client = docker.from_env()
            self._prepare_bot()
            container = client.containers.get(self.container_name)
            container.remove(force=True)
            client.containers.run(
                name=self.container_name,
                image=BOT_ENGINE_IMAGE,
                environment=self.env,
                network=DOCKER_NETWORK,
                detach=True,
                restart_policy={"Name": "always"}
            )
            client.close()
            logger.info('Bot Engine Restarted')
        except docker.errors.ImageNotFound as docker_error:
            logger.error(f'{docker_error}')
        except Exception as e:
            logger.error(f'{e}')
            raise e
