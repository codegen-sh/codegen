from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.sdk.core.assignment import Assignment
from codegen.sdk.core.function import Function
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_parse_global_vars(tmpdir) -> None:
    content = """
let a = 5;
const b = 10;
var c = d;
    """
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")
        global_vars = file.global_vars
        assert len(global_vars) == 3
        assert set([x.name for x in global_vars]) == {"a", "b", "c"}

        # =====[ a ]=====
        a = file.get_symbol("a")
        assert a is not None
        assert isinstance(a, Assignment)
        assert a.value == "5"

        # =====[ b ]=====
        b = file.get_symbol("b")
        assert b is not None
        assert isinstance(b, Assignment)
        assert b.value == "10"

        # =====[ c ]=====
        c = file.get_symbol("c")
        assert c is not None
        assert isinstance(c, Assignment)
        assert c.value == "d"


def test_tsx_get_object(tmpdir) -> None:
    file = """
export const arrowFunction = () => null;

const regularFunction = function () {
    return null
}

const Component: React.FC<Props> = (props) => {
    return <div>Content</div>;
}

const localObject = {
    method: () => null
}

export const exportedObject = {
    method: () => null,
    ref: arrowFunction,
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": file}) as ctx:
        file = ctx.get_file("test.tsx")

        # =====[ arrowFunction ]=====
        arrow_func = file.get_symbol("arrowFunction")
        assert arrow_func is not None
        assert isinstance(arrow_func, Function)
        assert len(arrow_func.symbol_usages) > 0

        # =====[ regularFunction ]=====
        regular_func = file.get_symbol("regularFunction")
        assert regular_func is not None
        assert isinstance(regular_func, Function)
        assert len(regular_func.symbol_usages) == 0

        # =====[ Component ]=====
        component = file.get_symbol("Component")
        assert component is not None
        assert isinstance(component, Function)
        assert component.is_jsx

        # =====[ localObject ]=====
        symbol = file.get_symbol("localObject")
        assert symbol is not None
        assert isinstance(symbol, Assignment)

        # =====[ exportedObject ]=====
        symbol = file.get_symbol("exportedObject")
        assert symbol is not None
        assert isinstance(symbol, Assignment)
        assert len(symbol.dependencies) == 1


def test_tsx_component_usages(tmpdir) -> None:
    file = """
import React from 'react';

type ComponentProps = { value: string }

function TestComponent({
  onSave,
  onClose,
}: ComponentProps) {
  return (
    <div>
      <button
        onClick={() =>
          onSave({
            value: 'test',
          })
        }
      >
        Save
      </button>
      <button onClick={onClose}>Close</button>
    </div>
  )
}

const componentConfig = {
  icon: 'icon',
  color: 'primary',
  getProps: (props) => {
    return {
      title: 'Title',
      description: props.value,
    }
  },
  getModalProps: (params) => ({
    title: 'Modal Title',
    children: <TestComponent {...params} />,
  }),
  menuItem: {
    label: 'Menu Item',
  },
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": file}) as ctx:
        file = ctx.get_file("test.tsx")
        component = file.get_symbol("TestComponent")
        assert len(component.symbol_usages) > 0
