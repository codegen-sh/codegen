import os
from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.typescript.file import TSFile


def test_declassify_class_component(tmpdir):
    # language=typescript
    content = """
import React from "react";

type Props = {
  by: number;
};

type State = {
  counter: number;
};

export class C extends React.Component<Props, State> {
  static defaultProps = {
    by: 1
  };

  constructor(props) {
    super(props);
    this.state = {
      counter: 0
    };
  }

  render() {
    return (
      <>
        <button onClick={() => this.onClick()}>
          {this.state.counter}
        </button>
        <p>Current step: {this.props.by}</p>
      </>
    );
  }

  onClick() {
    this.setState({ counter: this.state.counter + this.props.by });
  }
}
    """
    os.chdir(tmpdir)  # TODO: CG-10643

    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.tsx": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.tsx")
        component = file.get_class("C")
        component.source = component.class_component_to_function_component()

    # language=typescript
    assert (
        file.content
        == """
import React from "react";

type Props = {
  by: number;
};

type State = {
  counter: number;
};

export const C: React.FC<Props> = props => {
  const {
    by = 1
  } = props;

  const [counter, setCounter] = React.useState(0);

  function onClick() {
    setCounter(counter + by);
  }

  return <>
    <button onClick={() => onClick()}>
      {counter}
    </button>
    <p>Current step: {by}</p>
  </>;
};
    """
    )
