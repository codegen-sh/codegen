from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session, get_codebase_session
from codegen.sdk.core.function import Function
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_function_parameters_multiline(tmpdir) -> None:
    FILENAME = "function_test.ts"
    # language=typescript
    FILE_CONTENT = """
function foo(
  a,
  b: int,
  c?,
  d?: any,
  e = 1,
  f: int = 2,
  g: string = 'default'
) {}

function bar(...args, ...kwargs) {}
"""

    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILENAME: FILE_CONTENT}) as codebase:
        #
        # Function foo
        #
        function_symbol = codebase.get_symbol("foo")

        assert len(function_symbol.parameters) == 7

        # a
        assert function_symbol.parameters[0].name == "a"
        assert not function_symbol.parameters[0].is_typed
        assert not function_symbol.parameters[0].type
        assert function_symbol.parameters[0].default is None

        # b
        assert function_symbol.parameters[1].name == "b"
        assert function_symbol.parameters[1].is_typed
        assert function_symbol.parameters[1].type == "int"
        assert function_symbol.parameters[1].type == "int"
        assert function_symbol.parameters[1].default is None

        # c
        assert function_symbol.parameters[2].name == "c"
        assert not function_symbol.parameters[2].is_typed
        assert not function_symbol.parameters[2].type
        assert function_symbol.parameters[2].default is None

        # d
        assert function_symbol.parameters[3].name == "d"
        assert function_symbol.parameters[3].is_typed
        assert function_symbol.parameters[3].type == "any"
        assert function_symbol.parameters[3].type == "any"
        assert function_symbol.parameters[3].default is None

        # e
        assert function_symbol.parameters[4].name == "e"
        assert not function_symbol.parameters[4].is_typed
        assert not function_symbol.parameters[4].type
        assert function_symbol.parameters[4].default == "1"

        # f
        assert function_symbol.parameters[5].name == "f"
        assert function_symbol.parameters[5].is_typed
        assert function_symbol.parameters[5].type == "int"
        assert function_symbol.parameters[5].type == "int"
        assert function_symbol.parameters[5].default == "2"

        # g
        assert function_symbol.parameters[6].name == "g"
        assert function_symbol.parameters[6].is_typed
        assert function_symbol.parameters[6].type == "string"
        assert function_symbol.parameters[6].type == "string"
        assert function_symbol.parameters[6].default == "'default'"

        # TODO: *args and **kwargs are not yet supported!
        # #
        # # Function bar
        # #
        # function_symbol = codebase.get_symbol("bar")

        # assert len(function_symbol.parameters) == 2

        # # First Parameter
        # assert function_symbol.parameters[0].name == "args"
        # assert function_symbol.parameters[1].name == "kwargs"


def test_tsx_component_default_params(tmpdir) -> None:
    file = """
const Child = () => <div>Child</div>;

const Parent = ({ renderChild = Child }) => {
    return null;
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": file}) as ctx:
        file = ctx.get_file("test.tsx")
        child = file.get_symbol("Child")
        assert child is not None
        assert child.is_jsx
        assert len(child.symbol_usages) > 0
        parent = file.get_symbol("Parent")
        assert parent is not None
        assert isinstance(parent, Function)
        assert len(parent.dependencies) > 0


def test_tsx_component_parameters(tmpdir) -> None:
    file = """
function DefaultLoading() {
  return <LoadingSkeleton />
}

export function AsyncComponent<TData>({
  call,
  renderLoading: Loading = DefaultLoading,
  renderError,
  children,
}: AsyncComponentProps<TData>): ReactElement {
  const [retrying, setRetrying] = useState(false)
  const { data, loading, error, fetch } = useAsyncData(call)

  if (error || retrying) {
    return renderErrorNotice(error, renderError, retry, retrying)
  }

  if (loading || !data) {
    return <Loading />
  }

  const content = children({ data })

  return <Fragment>{content}</Fragment>

  async function retry() {
    setRetrying(true)

    try {
      await fetch()
    } finally {
      setRetrying(false)
    }
  }
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": file}) as ctx:
        file = ctx.get_file("test.tsx")
        component = file.get_symbol("DefaultLoading")
        assert component is not None
        assert component.is_jsx
        assert len(component.symbol_usages) == 1
