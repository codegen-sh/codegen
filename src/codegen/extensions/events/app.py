import logging

import modal  # deptry: ignore

from codegen.extensions.events.github import GitHub
from codegen.extensions.events.linear import Linear
from codegen.extensions.events.slack import Slack

logger = logging.getLogger(__name__)


class CodegenApp(modal.App):
    linear: Linear
    slack: Slack
    github: GitHub

    def __init__(self, name: str, modal_api_key: str, image: modal.Image):
        self._modal_api_key = modal_api_key
        self._image = image
        self._name = name

        super().__init__(name=name, image=image)

        # Expose attributes that provide event decorators for different providers.
        self.linear = Linear(self)
        self.slack = Slack(self)
        self.github = GitHub(self)
