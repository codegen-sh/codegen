from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_tsx_component_edit(tmpdir) -> None:
    file = """
import React from 'react';

interface FooBarProps {
  name: string;
}

function FooBar({ name }: FooBarProps): React.ReactElement {
  return (
    <div>
      <h1>Hello, {name}!</h1>
      <p>Welcome to my simple TSX component.</p>
      <img src='test' />
    </div>
  );
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": file}) as ctx:
        file = ctx.get_file("test.tsx")
        greeting = file.get_symbol("FooBar")

        # Edit the component
        p = greeting.get_component("p")
        p.insert_before("<h2>My new paragraph</h2>")
        p.insert_after("<h3>My new paragraph</h3>")
        p.edit("<h4>My new paragraph</h4>")
        ctx.commit_transactions()

        # Assert the changes
        assert "<h1>Hello, {name}!</h1>" in file.source
        assert "<h2>My new paragraph</h2>" in file.source
        assert "<h3>My new paragraph</h3>" in file.source
        assert "<h4>My new paragraph</h4>" in file.source
        assert "<p>Welcome to my simple TSX component.</p>" not in file.source


def test_tsx_component_set_name(tmpdir) -> None:
    file = """
import React from 'react';

interface FooBarProps {
  name: string;
}

function FooBar({ name }: FooBarProps): React.ReactElement {
  return (
    <div>
      <h1>Hello, {name}!</h1>
      <p>Welcome to my simple TSX component.</p>
      <img src='test' />
    </div>
  );
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": file}) as ctx:
        file = ctx.get_file("test.tsx")
        greeting = file.get_symbol("FooBar")

        # Edit the component
        div = greeting.get_component("div")
        div.set_name("div_2")
        p = greeting.get_component("p")
        p.set_name("h2")
        img = greeting.get_component("img")
        img.set_name("a")
        ctx.commit_transactions()

        # Assert the changes
        assert "<div_2>" in file.source
        assert "</div_2>" in file.source
        assert "<div>" not in file.source
        assert "</div>" not in file.source

        assert "<h2>Welcome to my simple TSX component.</h2>" in file.source
        assert "<p>Welcome to my simple TSX component.</p>" not in file.source

        assert "<a src='test' />" in file.source
        assert "<img src='test' />" not in file.source


def test_tsx_expression_edit(tmpdir) -> None:
    file = """
import React from 'react';

interface FooBarProps {
  name: string;
}

function FooBar({ name }: FooBarProps): React.ReactElement {
  return (
    <div>
      <h1>Hello, {name}!</h1>
      <p>Goodbye, {name}!</p>
    </div>
  );
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": file}) as ctx:
        file = ctx.get_file("test.tsx")
        greeting = file.get_symbol("FooBar")

        # Edit the component
        h1 = greeting.get_component("h1")
        expression = h1.expressions[0]
        expression.insert_before("Dr. ", newline=False)
        expression.edit("Who")
        expression.insert_after("!", newline=False)

        p = greeting.get_component("p")
        expression = p.expressions[0]
        expression.statement.edit("1 + name + 2")
        ctx.commit_transactions()

        # Assert the changes
        assert "<p>Goodbye, {1 + name + 2}!</p>" in file.source
        assert "<p>Goodbye, {name}!</p>" not in file.source

        assert "<h1>Hello, Dr. Who!!</h1>" in file.source
        assert "<h1>Hello, {name}!</h1>" not in file.source


def test_tsx_param_edit(tmpdir) -> None:
    file = """
import React from 'react';

interface FooBarProps {
  name: string;
}

function FooBar({ name }: FooBarProps): React.ReactElement {
  return (
    <div>
      <h1>Hello, {name}!</h1>
      <p>Goodbye, {name}!</p>
    </div>
  );
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": file}) as ctx:
        file = ctx.get_file("test.tsx")
        greeting = file.get_symbol("FooBar")

        # Edit the param
        name = greeting.get_parameter("name")
        name.rename("newName")
        ctx.commit_transactions()

        # Assert the changes
        assert "newName" in file.source
        assert "FooBar({ newName }: FooBarProps)" in file.source

        assert "<h1>Hello, {newName}!</h1>" in file.source
        assert "<h1>Hello, {name}!</h1>" not in file.source
        assert "<p>Goodbye, {newName}!</p>" in file.source
        assert "<p>Goodbye, {name}!</p>" not in file.source


def test_tsx_prop_edit(tmpdir) -> None:
    file = """
import React from 'react';

interface FooBarProps {
  name: string;
}

function FooBar({ name }: FooBarProps): React.ReactElement {
  return (
    <div>
      <h1 key="value" test={doAThing()}>Hello, {name}!</h1>
    </div>
  );
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": file}) as ctx:
        file = ctx.get_file("test.tsx")
        greeting = file.get_symbol("FooBar")

        # Edit the prop
        h1 = greeting.get_component("h1")
        prop1 = h1.props[0]
        prop1.set_name("key2")
        prop1.set_value('"value2"')
        prop2 = h1.props[1]
        prop2.set_name("test2")
        prop2.set_value("{doAnotherThing()}")
        ctx.commit_transactions()

        # Assert the changes
        assert '<h1 key2="value2" test2={doAnotherThing()}>Hello, {name}!</h1>' in file.source
        assert '<h1 key="value" test={doAThing()}>Hello, {name}!</h1>' not in file.source


def test_tsx_prop_add(tmpdir) -> None:
    file = """
import React from 'react';

interface FooBarProps {
  name: string;
}

function FooBar({ name }: FooBarProps): React.ReactElement {
  return (
    <div>
      <h1 key="value" test={doAThing()}>Hello, {name}!</h1>
    </div>
  );
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": file}) as ctx:
        file = ctx.get_file("test.tsx")
        greeting = file.get_symbol("FooBar")

        # Edit the prop
        h1 = greeting.get_component("h1")
        prop1 = h1.props[0]
        prop1.insert_before('key2="value2"', newline=False)
        prop2 = h1.props[1]
        prop2.insert_after("test2={doAnotherThing()}", newline=False)
        h1.add_prop("key3", "{123}")
        ctx.commit_transactions()

        # Assert the changes
        assert '<h1 key2="value2" key="value" test={doAThing()} test2={doAnotherThing()} key3={123}>Hello, {name}!</h1>' in file.source
        assert '<h1 key="value" test={doAThing()}>Hello, {name}!</h1>' not in file.source


def test_tsx_prop_add_empty(tmpdir) -> None:
    file = """
import React from 'react';

interface FooBarProps {
  name: string;
}

function FooBar({ name }: FooBarProps): React.ReactElement {
  return (
    <div>
      <h1>Hello, {name}!</h1>
    </div>
  );
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": file}) as ctx:
        file = ctx.get_file("test.tsx")
        greeting = file.get_symbol("FooBar")

        # Edit the prop
        h1 = greeting.get_component("h1")
        h1.add_prop("key", '"value"')
        h1.add_prop("test", "{doAThing()}")
        ctx.commit_transactions()

        # Assert the changes
        assert '<h1 key="value" test={doAThing()}>Hello, {name}!</h1>' in file.source
        assert "<h1>Hello, {name}!</h1>" not in file.source


def test_tsx_prop_remove(tmpdir) -> None:
    file = """
import React from 'react';

interface FooBarProps {
  name: string;
}

function FooBar({ name }: FooBarProps): React.ReactElement {
  return (
    <div>
      <h1 key="value" test={doAThing()}>Hello, {name}!</h1>
    </div>
  );
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": file}) as ctx:
        file = ctx.get_file("test.tsx")
        greeting = file.get_symbol("FooBar")

        # Edit the prop
        h1 = greeting.get_component("h1")
        prop1 = h1.props[0]
        prop1.remove()
        prop2 = h1.props[1]
        prop2.remove()
        ctx.commit_transactions()

        # Assert the changes
        assert "<h1>Hello, {name}!</h1>" in file.source
        assert '<h1 key="value" test={doAThing()}>Hello, {name}!</h1>' not in file.source


def test_tsx_move_component(tmpdir) -> None:
    original_file_name = "origin.tsx"
    original_file_content = """
function MainComponent({props}: MainComponentProps){
    return <FooBar
            key={propertyName}
            name={propertyName}
          />
}

function MyFooBar({ name }: MyFooBarProps) {
    return (<div></div>)
}

function FooBar({ component }: FooBarProps) {
  return (
    <MyStack>
      {orderBy(Object.entries(component.properties), ([propertyID]) => propertyID).map(
        ([propertyName, property]) => (
          <MyFooBar
            key={propertyName}
            name={propertyName}
          />
        )
      )}
    </MyStack>
  )
}
"""
    new_file_name = "new.tsx"
    new_file_content = ""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={original_file_name: original_file_content, new_file_name: new_file_content}) as ctx:
        original_file = ctx.get_file(original_file_name)
        foo_bar = original_file.get_symbol("FooBar")

        new_file = ctx.get_file(new_file_name)
        foo_bar.move_to_file(new_file)
        ctx.commit_transactions()

        assert "export function FooBar" in new_file.content
        assert "export function MyFooBar" in new_file.content

        assert "import { FooBar } from 'new'" in original_file.content
        assert "import { MyFooBar } from 'new'" not in original_file.content


def test_tsx_wrap(tmpdir) -> None:
    file = """
import React from 'react';

function FooBar(): React.ReactElement {
  return (
    <div>
      <h1>Hello, World!</h1>
    </div>
  );
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": file}) as ctx:
        file = ctx.get_file("test.tsx")
        foo_bar = file.get_symbol("FooBar")

        # Wrap the div element
        div = foo_bar.get_component("div")
        div.wrap('<section className="wrapper">', "</section>")
        ctx.commit_transactions()

        # Assert the changes
        new_file = ctx.get_file("test.tsx")
        expected_result = """
<section className="wrapper">
<div>
<h1>Hello, World!</h1>
</div>
</section>
"""
        assert expected_result in "\n".join([x.strip() for x in new_file.content.split("\n")])
