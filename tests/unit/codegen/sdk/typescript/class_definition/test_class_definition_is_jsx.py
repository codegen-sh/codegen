from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_class_without_parents(tmpdir) -> None:
    file_content = """
class MyClass {
  constructor() {}
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file_content}) as ctx:
        file = ctx.get_file("test.ts")
        my_class = file.get_class("MyClass")
        assert not my_class.is_jsx


def test_class_with_non_jsx_parent(tmpdir) -> None:
    file_content = """
class BaseClass {}
class MyClass extends BaseClass {
  constructor() {}
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file_content}) as ctx:
        file = ctx.get_file("test.ts")
        my_class = file.get_class("MyClass")
        assert not my_class.is_jsx


def test_class_with_jsx_parent(tmpdir) -> None:
    file_content = """
import React from 'react';
class MyComponent extends React.Component {
  constructor() {}
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": file_content}) as ctx:
        file = ctx.get_file("test.tsx")
        my_component = file.get_class("MyComponent")
        assert my_component.is_jsx


def test_class_with_jsx_parent_module_import(tmpdir) -> None:
    file_content = """
import {Component} from 'react';
class MyComponent extends Component {
  constructor() {}
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": file_content}) as ctx:
        file = ctx.get_file("test.tsx")
        my_component = file.get_class("MyComponent")
        assert my_component.is_jsx


def test_class_with_pure_jsx_parent(tmpdir) -> None:
    file_content = """
import React from 'react';
class MyComponent extends React.PureComponent {
  constructor() {}
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": file_content}) as ctx:
        file = ctx.get_file("test.tsx")
        my_component = file.get_class("MyComponent")
        assert my_component.is_jsx


def test_class_with_multiple_parents(tmpdir) -> None:
    file_content = """
class Interface1 {}
class Interface2 {}
class MyComponent extends React.Component, Interface1, Interface2 {
  constructor() {}
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": file_content}) as ctx:
        file = ctx.get_file("test.tsx")
        my_component = file.get_class("MyComponent")
        assert my_component.is_jsx


def test_class_with_interface_implementation(tmpdir) -> None:
    file_content = """
interface MyInterface {}
class MyComponent extends React.Component implements MyInterface {
  constructor() {}
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": file_content}) as ctx:
        file = ctx.get_file("test.tsx")
        my_component = file.get_class("MyComponent")
        assert my_component.is_jsx


def test_class_with_mixin(tmpdir) -> None:
    file_content = """
function mixin(Base) {
  return class extends Base {
    constructor() {
      super();
    }
  };
}
class MyComponent extends mixin(React.Component) {
  constructor() {}
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": file_content}) as ctx:
        file = ctx.get_file("test.tsx")
        my_component = file.get_class("MyComponent")
        assert my_component.is_jsx
