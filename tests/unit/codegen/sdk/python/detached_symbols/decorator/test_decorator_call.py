from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session


def test_decorator_call_1(tmpdir) -> None:
    content = """
@my_app.route(
    "/api/v1/<uuid:user_uuid>/upload", methods=["POST"]
)
class ExampleUserUpload(Resource):
    def post(self, user_uuid: str):
        ...
"""
    with get_codebase_graph_session(tmpdir=tmpdir, files={"decorator.py": content}) as ctx:
        file = ctx.get_file("decorator.py")
        cls = file.get_class("ExampleUserUpload")
        assert len(cls.decorators) == 1
        decorator = cls.decorators[0]
        assert decorator.call.full_name == "my_app.route"
        assert decorator.call.args[0].value == '"/api/v1/<uuid:user_uuid>/upload"'
        assert decorator.call.args[1].name == "methods"
        assert decorator.call.args[1].value == '["POST"]'


def test_decorator_call_2(tmpdir) -> None:
    content = """
@my_app.route(
    "/user/<uuid:document_uuid>", methods=["POST"]
)
class DocumentUpload(Resource):
    @my_app.something_else()
    def post(self, document_uuid: str):
        ...
"""
    with get_codebase_graph_session(tmpdir=tmpdir, files={"decorator.py": content}) as ctx:
        file = ctx.get_file("decorator.py")
        cls = file.get_class("DocumentUpload")
        assert len(cls.decorators) == 1
        decorator = cls.decorators[0]
        assert decorator.call.full_name == "my_app.route"
        assert decorator.call.args[0].value == '"/user/<uuid:document_uuid>"'
        assert decorator.call.args[1].name == "methods"
        assert decorator.call.args[1].value == '["POST"]'


def test_decorator_call_args(tmpdir) -> None:
    content = """
@my_app.route("/get_user_data")
class GetUserData(Resource):
    def post(self) -> Response:
        ...
"""
    with get_codebase_graph_session(tmpdir=tmpdir, files={"decorator.py": content}) as ctx:
        file = ctx.get_file("decorator.py")
        cls = file.get_class("GetUserData")
        assert len(cls.decorators) == 1
        decorator = cls.decorators[0]
        assert decorator.call.full_name == "my_app.route"
        assert decorator.call.get_arg_by_parameter_name("method") is None
        assert decorator.call.args[0].value == '"/get_user_data"'
