from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_usages_unpack(tmpdir) -> None:
    # language=typescript
    content = """
function foo() {
    return [1, 2];
}

const a = foo();
const [b, c] = foo();
const {d, e} = foo();
export const [f, g] = foo();
export const {h, i} = foo();
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        foo = file.get_function("foo")

        assert len(file.global_vars) == 9
        assert len(foo.symbol_usages) == 9
        assert {usage.name for usage in foo.symbol_usages} == {"a", "b", "c", "d", "e", "f", "g", "h", "i"}


def test_usages_in_if(tmpdir) -> None:
    # language=typescript
    content = """
function foo() {
    return [1, 2];
}

if (true) {
	const GLOBAL_VAR = foo();
} else if (false) {
    const GLOBAL_VAR_2 = foo();
} else {
    const GLOBAL_VAR_3 = foo();
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        foo = file.get_function("foo")

        assert len(file.global_vars) == 3
        assert len(foo.symbol_usages) == 3
        assert {usage.name for usage in foo.symbol_usages} == {"GLOBAL_VAR", "GLOBAL_VAR_2", "GLOBAL_VAR_3"}


def test_usages_in_test(tmpdir) -> None:
    # language=typescript jsx
    content = """
function TestComponent(props: {
    value: string
    onChange?: () => void
    onSubmit?: () => void
}) {
    const { value, onChange, onSubmit } = props

    return (
        <div>
            <input
                value={value}
                onChange={onChange}
                onSubmit={onSubmit}
            />
        </div>
    )
}

describe("TestComponent", () => {
    let onChange: jest.Mock
    let onSubmit: jest.Mock

    beforeEach(() => {
        onChange = jest.fn()
        onSubmit = jest.fn()
    })

    it("renders with props", () => {
        const { getByRole } = render(
            <TestComponent value="test" onChange={onChange} />
        )
        expect(getByRole("textbox")).toBeInTheDocument()
    })

    it("does not render when value missing", () => {
        const { queryByRole } = render(<TestComponent value="" />)
        expect(queryByRole("textbox")).toBeInTheDocument()
    })
})
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.tsx": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.tsx")
        component = file.get_function("TestComponent")
        assert component.is_jsx
        assert len(component.symbol_usages) > 0


def test_usages_in_other_component(tmpdir) -> None:
    # language=typescript jsx
    content = """
function ChildComponent({
    data,
    config,
    styles,
    variant,
}: {
    data: any
    config: Config
    styles: Styles
    variant: string
}) {
    const theme = useTheme()
    const { items } = data
    const isEnabled = config.enabled

    return (
        <div style={styles.container}>
            {variant === 'primary' ? (
                <div style={styles.content}>
                    <h1>{config.title}</h1>
                    <p>{config.description}</p>
                </div>
            ) : (
                <div style={styles.alternateContent}>
                    <h2>{config.subtitle}</h2>
                    <ul>
                        {items.map(item => (
                            <li key={item.id}>{item.text}</li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    )
}

function ParentComponent({
    data,
    config,
    styles
}: {
    data: any
    config: Config
    styles: Styles
}) {
    const [variant, setVariant] = useState('primary')

    return (
        <div>
            <select onChange={e => setVariant(e.target.value)}>
                <option value="primary">Primary</option>
                <option value="secondary">Secondary</option>
            </select>

            <ChildComponent
                data={data}
                config={config}
                styles={styles}
                variant={variant}
            />
        </div>
    )
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.tsx": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.tsx")
        component = file.get_function("ChildComponent")
        assert component.is_jsx
        assert len(component.symbol_usages) == 1
        assert component.symbol_usages[0].name == "ParentComponent"


def test_function_spread_and_f_string(tmpdir) -> None:
    # language=typescript
    file = """
export function child() {
    return {a: 1};
}

export async function parent1() {
    return {...child()};
}

export async function parent2() {
    return `${child()}`
}
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")

        # =====[ Test dependencies ]=====
        func = file.get_function("parent1")
        deps = func.dependencies
        assert len(deps) == 1
        assert deps[0].name == "child"
        assert len(func.function_calls) == 1

        # =====[ Test dependencies ]=====
        func = file.get_function("parent2")
        deps = func.dependencies
        assert len(deps) == 1
        assert deps[0].name == "child"
        assert len(func.function_calls) == 1

        # =====[ Usages ]====
        my_func = file.get_function("child")
        usages = my_func.symbol_usages
        assert len(usages) == 3
