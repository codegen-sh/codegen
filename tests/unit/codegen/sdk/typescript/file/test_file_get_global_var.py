from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_get_global_var_excludes_component_var(tmpdir) -> None:
    ts_code = """
const MyComponent = (props) => {
    const {a, b, c} = props;
    return <>Hello World</>;
};
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": ts_code}) as ctx:
        file = ctx.get_file("test.tsx")

        # =====[ Count symbols ]=====
        symbols = file.symbols
        assert len(symbols) == 1
        assert set(x.name for x in symbols) == {"MyComponent"}
        func = file.get_function("MyComponent")
        assert func.name == "MyComponent"
        # a is not a global var and should not be found
        gvar = file.get_global_var("a")
        assert gvar is None


def test_get_global_var_excludes_class_var(tmpdir) -> None:
    ts_code = """
export class CopyButton extends React.Component<CopyButtonProps, CopyButtonState> {
    static defaultProps = {
        onCopy: void {},
        onCopyText: 'Copied',
        value: '',
        type: 'button'
    };
    private timeout?: number;
    state: CopyButtonState = {
        hasCopiedVale: false
    };
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": ts_code}) as ctx:
        file = ctx.get_file("test.tsx")
        cls = file.get_class("CopyButton")
        assert cls is not None
        assert cls.name == "CopyButton"
        gvar = file.get_global_var("timeout")
        assert gvar is None
