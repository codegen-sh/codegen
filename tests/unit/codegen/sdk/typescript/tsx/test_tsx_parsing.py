from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.sdk.typescript.detached_symbols.jsx.element import JSXElement
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_basic_component_parsing(tmpdir) -> None:
    # language=typescript jsx
    file = """
import React from 'react';

interface ComponentProps {
  prop1: string;
}

function TestComponent({ prop1 }: ComponentProps): React.ReactElement {
  return (
    <div>
      <h1>{prop1}</h1>
      <p>Some text</p>
    </div>
  );
}

export default TestComponent;
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": file}) as ctx:
        file = ctx.get_file("test.tsx")
        component = file.get_symbol("TestComponent")
        assert len(component.parameters) == 1

        param = component.parameters[0]
        assert param.name == "prop1"

        assert len(param.parent_function.code_block.get_variable_usages(param.name)) == 1


def test_component_with_props_destructuring(tmpdir) -> None:
    # language=typescript jsx
    content = """
function TestComponent(props: {
    prop1: boolean
    prop2?: () => void
    prop3?: () => void
}) {
    const { prop1, prop2, prop3 } = props
    return (
        <Wrapper
            prop1={prop1}
            prop2={prop2}
            prop3={prop3}
            render={wrapperProps => (
                <Child {...wrapperProps}>
                    <div data-testid="content" />
                </Child>
            )}
        />
    )
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, files={"test.tsx": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as ctx:
        file = ctx.get_file("test.tsx")
        component = file.get_function("TestComponent")
        assert component.is_jsx


def test_tsx_file_type_validation(tmpdir) -> None:
    ts_file_name = "test.ts"
    tsx_file_name = "test.tsx"
    origin_file_name = "origin.tsx"
    # language=typescript jsx
    origin_file_content = """
function TestComponent(props: {
    prop1: boolean
    prop2?: () => void
    prop3?: () => void
}) {
    const { prop1, prop2, prop3 } = props
    return (
        <Wrapper
            prop1={prop1}
            prop2={prop2}
            prop3={prop3}
            render={wrapperProps => (
                <Child {...wrapperProps}>
                    <div data-testid="content" />
                </Child>
            )}
        />
    )
}
"""
    files = {ts_file_name: "", tsx_file_name: "", origin_file_name: origin_file_content}
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as ctx:
        ts_file = ctx.get_file(ts_file_name)
        tsx_file = ctx.get_file(tsx_file_name)
        origin_file = ctx.get_file(origin_file_name)

        test_component = origin_file.get_symbol("TestComponent")

        try:
            test_component.move_to_file(ts_file)
            assert False
        except ValueError as e:
            assert str(e) == "Symbol TestComponent cannot be added to this file type."

        test_component.move_to_file(tsx_file)

    assert "export function TestComponent" in tsx_file.content


def test_jsx_element_attributes(tmpdir) -> None:
    # language=typescript jsx
    file = """
import React from 'react';

interface ComponentProps {
  prop1: string;
  prop2: number;
}

function TestComponent({ prop1, prop2 }: ComponentProps): React.ReactElement {
  return (
    <div key={prop2} className="test-class">
      <h1>{prop1}</h1>
      <p>Some text</p>
    </div>
  );
}
"""

    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": file}) as ctx:
        file = ctx.get_file("test.tsx")
        assert len(file.jsx_elements) == 3

        component = file.get_symbol("TestComponent")

        root_element = component.jsx_elements[0]
        assert root_element.name == "div"
        assert isinstance(root_element, JSXElement)
        assert len(root_element.props) == 2
        assert root_element.get_prop("key").value == "{prop2}"
        assert root_element.get_prop("className").value == '"test-class"'
        assert root_element.get_prop("nonexistent") is None

        key_prop = root_element.props[0]
        assert key_prop.source == "key={prop2}"
        assert key_prop.name == "key"
        assert key_prop.value == "{prop2}"
        assert key_prop.expression is not None
        assert key_prop.expression.source == "{prop2}"
        assert key_prop.expression.statement.source == "prop2"

        class_prop = root_element.props[1]
        assert class_prop.source == 'className="test-class"'
        assert class_prop.name == "className"
        assert class_prop.value == '"test-class"'
        assert class_prop.expression is None


def test_complex_jsx_expressions(tmpdir) -> None:
    # language=typescript jsx
    file = """
import React from 'react';

interface ComponentProps {
  prop1: string;
  prop2: string;
  prop3: boolean;
}

const TestComponent: React.FC<ComponentProps> = ({ prop1, prop2, prop3 }) => {
  return (
    <>
      <h2>Title</h2>
      <div className="container">
        <p>First: {prop1}</p>
        <p>Second: {prop2}</p>
        <p data-flag={prop3.toString()}>
          Status: {prop3 ? 'Active' : 'Inactive'}
        </p>
        <div className={`${prop3} ... ${prop1 ? "a" : prop2}`} />
      </div>
    </>
  );
};

export default TestComponent;
"""

    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": file}) as ctx:
        file = ctx.get_file("test.tsx")
        component = file.get_symbol("TestComponent")
        assert len(component.jsx_elements) == 7

        root = component.jsx_elements[0]
        assert root.name is None
        assert len(root.jsx_elements) == 6

        text_element = root.jsx_elements[2]
        assert text_element.name == "p"
        assert text_element.source == "<p>First: {prop1}</p>"
        assert len(text_element.props) == 0
        assert len(text_element.jsx_elements) == 0
        assert len(text_element.expressions) == 1
        assert text_element.expressions[0].source == "{prop1}"
        assert text_element.expressions[0].statement.source == "prop1"

        conditional_element = root.jsx_elements[4]
        assert conditional_element.name == "p"
        assert len(conditional_element.props) == 1
        assert conditional_element.props[0].name == "data-flag"
        assert conditional_element.props[0].value == "{prop3.toString()}"
        assert conditional_element.props[0].expression is not None
        assert conditional_element.props[0].expression.source == "{prop3.toString()}"
        assert conditional_element.props[0].expression.statement.source == "prop3.toString()"
        assert len(conditional_element.expressions) == 2
        assert conditional_element.expressions[0].source == "{prop3.toString()}"
        assert conditional_element.expressions[1].source == "{prop3 ? 'Active' : 'Inactive'}"

        template_element = root.jsx_elements[5]
        assert template_element.name == "div"
        assert len(template_element.props) == 1
        assert template_element.props[0].name == "className"
        assert template_element.props[0].value == '{`${prop3} ... ${prop1 ? "a" : prop2}`}'
        assert template_element.props[0].expression is not None
        assert template_element.props[0].expression.source == '{`${prop3} ... ${prop1 ? "a" : prop2}`}'
        assert template_element.props[0].expression.statement.source == '`${prop3} ... ${prop1 ? "a" : prop2}`'
        assert len(template_element.expressions) == 1


def test_nested_jsx_element_parsing(tmpdir) -> None:
    # language=typescript jsx
    file = """
import React from 'react';

function TestComponent(): React.ReactElement {
  return (
    <outer className="wrapper">
      <middle>
        <inner>Content</inner>
      </middle>
    </outer>
  );
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": file}) as ctx:
        file = ctx.get_file("test.tsx")
        component = file.get_symbol("TestComponent")

        assert len(component.jsx_elements) == 3

        outer = component.jsx_elements[0]
        assert outer.name == "outer"
        assert len(outer.props) == 1
        assert outer.props[0].name == "className"
        assert outer.props[0].value == '"wrapper"'

        middle = outer.jsx_elements[0]
        assert middle.name == "middle"
        assert len(middle.jsx_elements) == 1

        inner = middle.jsx_elements[0]
        assert inner.name == "inner"
        assert inner.source == "<inner>Content</inner>"
