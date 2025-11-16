from abc import ABC


class Service(ABC):
    def __init__(self, logger):
        self.logger = logger
        self.name = self.__class__.__name__

    async def initialize(self):
        self.logger.info(f"Initializing service: {self.name}")

    async def start(self):
        self.logger.info(f"Starting service: {self.name}")

    async def stop(self):
        self.logger.info(f"Stopping service: {self.name}")
