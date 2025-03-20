import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_move_component_with_dependencies(tmpdir) -> None:
    """Tests moving a component with dependencies to another file"""
    src_filename = "src.tsx"
    # language=typescript jsx
    src_content = """
import { ExternalComponent } from 'external-package';

export const ComponentA = () => {
    return (<ExternalComponent />);
}

export const ComponentB = () => {
    return (<ComponentA />);
}

const ComponentC = () => {
    return (<ComponentB />);
}

export const ComponentD = () => {}
"""

    dst_filename = "dst.tsx"
    # language=typescript jsx
    dst_content = """
const placeholder = () => null;
"""
    adj_filename = "adj.tsx"
    # language=typescript jsx
    adj_content = """
import { ComponentA } from 'src'

const ComponentE = () => {
    return (<ComponentA />);
}
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={src_filename: src_content, dst_filename: dst_content, adj_filename: adj_content}) as codebase:
        component_a = codebase.get_symbol("ComponentA")
        component_b = codebase.get_symbol("ComponentB")
        component_d = codebase.get_symbol("ComponentD")
        dst_file = codebase.get_file(dst_filename)

        # Move components with different strategies
        component_a.move_to_file(dst_file, include_dependencies=True, strategy="update_all_imports")
        component_b.move_to_file(dst_file, include_dependencies=True, strategy="add_back_edge")
        component_d.move_to_file(dst_file, include_dependencies=True, strategy="add_back_edge")
        codebase.commit()

        dst_file = codebase.get_file(dst_filename)
        src_file = codebase.get_file(src_filename)
        adj_file = codebase.get_file(adj_filename)

        # Verify ComponentA move
        assert "const ComponentA" not in src_file.content
        assert "import { ComponentA } from 'dst'" in src_file.content
        assert "const ComponentA = () => {" in dst_file.content
        assert "import { ExternalComponent }" in dst_file.content
        assert "import { ComponentA } from 'dst'" in adj_file.content

        # Verify ComponentB move
        assert "const ComponentB" not in src_file.content
        assert "export { ComponentB } from 'dst'" in src_file.content
        assert "const ComponentB = () => {" in dst_file.content
        assert "export { ComponentB }" in src_file.content

        # Verify ComponentD move
        assert "const ComponentD" not in src_file.content
        assert "export { ComponentD } from 'dst'" in src_file.content


@pytest.mark.skip(reason="This test is failing because of the way we handle re-exports. Address in CG-10686")
def test_remove_unused_exports(tmpdir) -> None:
    """Tests removing unused exports when moving components between files"""
    # ========== [ BEFORE ] ==========
    # language=typescript jsx
    SRC_CONTENT = """
export default function MainComponent() {
  const [state, setState] = useState<StateType | null>()
  return (<div>
            <div>
                <SubComponent/>
            </div>
          </div>)
}

function SubComponent({ props }: SubComponentProps) {
  return (
    <HelperComponent size='s'/>
  )
}

function HelperComponent({ props }: HelperComponentProps) {
  return (
    <SharedComponent size='l'/>
  )
}

export function SharedComponent({ props }: SharedComponentProps) {
  return (
    <div> <StateComponent/> </div>
  )
}

export function StateComponent({ props }: StateComponentProps) {
    return (
        <div> State </div>
    )
}

export function UnusedComponent({ props }: UnusedProps) {
    return (
        <div> Unused </div>
    )
}
"""
    # language=typescript jsx
    ADJ_CONTENT = """
import MainComponent from 'Component'
import { SharedComponent } from 'Component'
import { StateComponent } from 'utils'

function Container(props: ContainerProps) {
    return (<Wrapper components={[MainComponent, SharedComponent]}/>)
}
"""
    # language=typescript jsx
    MISC_CONTENT = """
export { UnusedComponent } from 'Component'
function Helper({ props }: HelperProps) {}

export { Helper }
"""
    # language=typescript jsx
    IMPORT_CONTENT = """
import { UnusedComponent } from 'misc'
"""

    # ========== [ AFTER ] ==========
    # language=typescript jsx
    EXPECTED_SRC_CONTENT = """
import { SubComponent } from 'new';

export default function MainComponent() {
  const [state, setState] = useState<StateType | null>()
  return (<div>
            <div>
                <SubComponent/>
            </div>
          </div>)
}

export function UnusedComponent({ props }: UnusedProps) {
    return (
        <div> Unused </div>
    )
}
"""
    # language=typescript jsx
    EXPECTED_NEW_CONTENT = """
export function SubComponent({ props }: SubComponentProps) {
  return (
    <HelperComponent size='s'/>
  )
}

function HelperComponent({ props }: HelperComponentProps) {
  return (
    <SharedComponent size='l'/>
  )
}

export function SharedComponent({ props }: SharedComponentProps) {
  return (
    <div> <StateComponent/> </div>
  )
}
"""
    # language=typescript jsx
    EXPECTED_ADJ_CONTENT = """
import MainComponent from 'Component'
import { SharedComponent } from 'new'
import { StateComponent } from 'utils'

function Container(props: ContainerProps) {
    return (<Wrapper components={[MainComponent, SharedComponent]}/>)
}
"""
    # language=typescript jsx
    EXPECTED_MISC_CONTENT = """
function Helper({ props }: HelperProps) {}
"""

    files = {"Component.tsx": SRC_CONTENT, "adjacent.tsx": ADJ_CONTENT, "misc.tsx": MISC_CONTENT, "import.tsx": IMPORT_CONTENT}

    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
        src_file = codebase.get_file("Component.tsx")
        adj_file = codebase.get_file("adjacent.tsx")
        misc_file = codebase.get_file("misc.tsx")
        new_file = codebase.create_file("new.tsx")

        sub_component = src_file.get_symbol("SubComponent")
        sub_component.move_to_file(new_file)

        codebase.commit()

        # Remove unused exports from all affected files
        new_file.remove_unused_exports()
        src_file.remove_unused_exports()
        misc_file.remove_unused_exports()

    assert src_file.content.strip() == EXPECTED_SRC_CONTENT.strip()
    assert new_file.content.strip() == EXPECTED_NEW_CONTENT.strip()
    assert adj_file.content.strip() == EXPECTED_ADJ_CONTENT.strip()
    assert misc_file.content.strip() == EXPECTED_MISC_CONTENT.strip()
