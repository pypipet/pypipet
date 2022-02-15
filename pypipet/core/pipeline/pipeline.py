
from .action import ActionMap

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class Pipeline():
    def __init__(self, data: list, actions: list):
        self.actions = actions
        self.data = data

    def run(self):
        for action in self.actions:
            if action.name == 'external':
                self.data = action.run_external_func(self.data, action.params)
            else:
                print('pipeline action', action.name)
                data = ActionMap.mapping(self.data, action)
                self.data = data

   

