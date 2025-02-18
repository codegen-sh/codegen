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
        assert "import { ComponentB } from 'dst'" in src_file.content
        assert "const ComponentB = () => {" in dst_file.content
        assert "export { ComponentB }" in src_file.content

        # Verify ComponentD move
        assert "const ComponentD" not in src_file.content
        assert "export { ComponentD } from 'dst'" in src_file.content


def test_remove_unused_exports(tmpdir) -> None:
    """Tests removing unused exports when moving components between files"""
    src_filename = "Component.tsx"
    # language=typescript jsx
    src_content = """
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
    adj_filename = "adjacent.tsx"
    # language=typescript jsx
    adj_content = """
import MainComponent from 'Component'
import { SharedComponent } from 'Component'
import { StateComponent } from 'utils'

function Container(props: ContainerProps) {
    return (<Wrapper components={[MainComponent, SharedComponent]}/>)
}
"""
    misc_filename = "misc.tsx"
    # language=typescript jsx
    misc_content = """
export { UnusedComponent } from 'Component'
function Helper({ props }: HelperProps) {}

export { Helper }
"""
    import_filename = "import.tsx"
    # language=typescript jsx
    import_content = """
import { UnusedComponent } from 'misc'
"""

    files = {src_filename: src_content, adj_filename: adj_content, misc_filename: misc_content, import_filename: import_content}

    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
        src_file = codebase.get_file(src_filename)
        adj_file = codebase.get_file(adj_filename)
        misc_file = codebase.get_file(misc_filename)
        new_file = codebase.create_file("new.tsx")

        sub_component = src_file.get_symbol("SubComponent")
        sub_component.move_to_file(new_file)

        codebase.commit()

        # Remove unused exports from all affected files
        new_file.remove_unused_exports()
        src_file.remove_unused_exports()
        misc_file.remove_unused_exports()

    # Verify exports in new file
    assert "export function SubComponent" in new_file.content
    assert "function HelperComponent" in new_file.content
    assert "export function HelperComponent" not in new_file.content
    assert "export function SharedComponent" in new_file.content

    # Verify imports updated
    assert "import { SharedComponent } from 'new'" in adj_file.content

    # Verify original file exports
    assert "export default function MainComponent()" in src_file.content
    assert "function UnusedComponent" in src_file.content
    assert "export function UnusedComponent" not in src_file.content

    # Verify misc file exports cleaned up
    assert "export { Helper }" not in misc_file.content
    assert "export { UnusedComponent } from 'Component'" not in misc_file.content
