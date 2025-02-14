import logging

import modal  # deptry: ignore

from codegen.extensions.events.linear import Linear

logger = logging.getLogger(__name__)


class CodegenApp(modal.App):
    linear: Linear

    def __init__(self, name, modal_api_key, image: modal.Image):
        self._modal_api_key = modal_api_key
        self._image = image
        self._name = name

        super().__init__(name=name, image=image)

        # Expose a attribute that provides the event decorator for different providers.
        self.linear = Linear(self)
