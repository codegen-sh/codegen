from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_function_is_jsx(tmpdir) -> None:
    # language=typescript jsx
    content = """
const regularFunction = () => {
    return null;
}

const MyComponent = (): JSX.Element => {
    return <div>Hello</div>;
}

const ConditionalComponent = ({ show }) => {
    if (show) {
        return <div>Visible</div>;
    } else {
        return null
    }
}

function standardFunction() {
    return 42;
}

const ComponentWithProps = ({ name, onClick }) => {
    return (
        <button onClick={onClick}>
            Hello {name}
        </button>
    );
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": content}) as codebase:
        regular = codebase.get_symbol("regularFunction")
        assert not regular.is_jsx

        component = codebase.get_symbol("MyComponent")
        assert component.is_jsx

        conditional = codebase.get_symbol("ConditionalComponent")
        assert conditional.is_jsx

        standard = codebase.get_symbol("standardFunction")
        assert not standard.is_jsx

        with_props = codebase.get_symbol("ComponentWithProps")
        assert with_props.is_jsx


def test_non_jsx_functions(tmpdir) -> None:
    # language=typescript jsx
    content = """
export const dataLoader = async ({ request }) => {
    const data = await fetchData(request);
    return {
        items: data.items,
        meta: {
            total: data.total,
            page: data.page
        }
    };
};

function useCustomHook() {
    const [value, setValue] = useState(null);

    useEffect(() => {
        if (!value) return;

        const handler = async () => {
            const result = await processValue(value);
            setValue(result);
        };

        handler();
    }, [value]);

    return value;
}
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": content}) as codebase:
        file = codebase.get_file("test.tsx")
        jsx_functions = [func for func in file.functions if func.is_jsx and func.name is not None]
        assert len(jsx_functions) == 0
