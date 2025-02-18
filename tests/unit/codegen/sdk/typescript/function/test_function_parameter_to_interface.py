from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.typescript.file import TSFile


def test_convert_simple_props_to_interface(tmpdir):
    # language=typescript
    content = """
function Button(props: {
    text: string,
    onClick: () => void,
    disabled?: boolean
}) {
    return <button>{props.text}</button>;
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.tsx": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.tsx")
        component = file.functions[0]
        component.parameters[0].convert_to_interface()

    # language=typescript
    assert (
        file.content
        == """
interface ButtonProps {
    text: string;
    onClick: () => void;
    disabled?: boolean;
}

function Button(props: ButtonProps) {
    return <button>{props.text}</button>;
}
    """
    )


def test_convert_props_to_interface_with_complex_types(tmpdir):
    # language=typescript
    content = """
function DataGrid(props: {
    columns: Array<{id: string, title: string, width?: number}>,
    rows: Record<string, any>[],
    onSort?: (column: string) => void,
    defaultSort?: { field: string, direction: 'asc' | 'desc' }
}) {
    return <div>{/* implementation */}</div>;
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.tsx": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.tsx")
        component = file.functions[0]
        component.parameters[0].convert_to_interface()

    # language=typescript
    assert (
        file.content
        == """
interface DataGridProps {
    columns: Array<{id: string, title: string, width?: number}>;
    rows: Record<string, any>[];
    onSort?: (column: string) => void;
    defaultSort?: { field: string, direction: 'asc' | 'desc' };
}

function DataGrid(props: DataGridProps) {
    return <div>{/* implementation */}</div>;
}
    """
    )


def test_convert_props_to_interface_with_generics(tmpdir):
    # language=typescript
    content = """
function List<T>(props: {
    items: T[],
    renderItem: (item: T, index: number) => React.ReactNode,
    keyExtractor: (item: T) => string,
    ListEmptyComponent?: React.ComponentType
}) {
    return <div>{/* implementation */}</div>;
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.tsx": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.tsx")
        component = file.functions[0]
        assert component.type_parameters
        component.parameters[0].convert_to_interface()

    # language=typescript
    assert (
        file.content
        == """
interface ListProps<T> {
    items: T[];
    renderItem: (item: T, index: number) => React.ReactNode;
    keyExtractor: (item: T) => string;
    ListEmptyComponent?: React.ComponentType;
}

function List<T>(props: ListProps<T>) {
    return <div>{/* implementation */}</div>;
}
    """
    )


def test_convert_props_to_interface_with_extends(tmpdir):
    # language=typescript
    content = """
function CustomButton(props: {
    variant: 'primary' | 'secondary',
    size: 'small' | 'medium' | 'large',
    isLoading?: boolean
} & React.ButtonHTMLAttributes<HTMLButtonElement>) {
    return <button {...props}>{/* implementation */}</button>;
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.tsx": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.tsx")
        component = file.functions[0]
        component.parameters[0].convert_to_interface()

    # language=typescript
    assert (
        file.content
        == """
interface CustomButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant: 'primary' | 'secondary';
    size: 'small' | 'medium' | 'large';
    isLoading?: boolean;
}

function CustomButton(props: CustomButtonProps) {
    return <button {...props}>{/* implementation */}</button>;
}
    """
    )
