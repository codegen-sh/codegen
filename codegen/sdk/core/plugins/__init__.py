from codegen.sdk.core.plugins.axios import AxiosApiFinder
from codegen.sdk.core.plugins.flask import FlaskApiFinder
from codegen.sdk.core.plugins.modal import ModalApiFinder

PLUGINS = [
    FlaskApiFinder(),
    AxiosApiFinder(),
    ModalApiFinder(),
]
