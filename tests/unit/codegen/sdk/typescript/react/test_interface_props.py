from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.typescript.file import TSFile


def test_convert_props_to_interface_with_proptypes_oneof(tmpdir):
    # language=typescript
    content = """
import { PropTypes } from 'react';

const Component = ({ type, message, action }) => {
    return <div>{/* implementation */}</div>;
};

Component.propTypes = {
    type: PropTypes.oneOf(['success', 'warning', 'error']),
    message: PropTypes.string,
    action: PropTypes.oneOfType([
        PropTypes.func,
        PropTypes.shape({
            label: PropTypes.string,
            onClick: PropTypes.func
        })
    ])
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.tsx": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.tsx")
        component = file.functions[0]
        component.convert_props_to_interface()

    # language=typescript
    assert (
        file.content
        == """
interface ComponentProps {
    type?: 'success' | 'warning' | 'error';
    message?: string;
    action?: CallableFunction | {
        label?: string;
        onClick?: CallableFunction;
    };
}

const Component = ({ type, message, action }: ComponentProps) => {
    return <div>{/* implementation */}</div>;
};
    """
    )


def test_convert_class_props_to_interface_with_proptypes_oneof(tmpdir):
    # language=typescript
    content = """
import { PropTypes } from 'react';

class Component extends React.Component {
    render() {
        return <div>{/* implementation */}</div>;
    }
}

Component.propTypes = {
    type: PropTypes.oneOf(['success', 'warning', 'error']),
    message: PropTypes.string,
    action: PropTypes.oneOfType([
        PropTypes.func,
        PropTypes.shape({
            label: PropTypes.string,
            onClick: PropTypes.func
        })
    ])
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.tsx": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.tsx")
        component = file.classes[0]
        component.convert_props_to_interface()

    # language=typescript
    assert (
        file.content
        == """
interface ComponentProps {
    type?: 'success' | 'warning' | 'error';
    message?: string;
    action?: CallableFunction | {
        label?: string;
        onClick?: CallableFunction;
    };
}

class Component extends React.Component<ComponentProps> {
    render() {
        return <div>{/* implementation */}</div>;
    }
}
    """
    )


def test_convert_simple_function_props_to_interface(tmpdir):
    # language=typescript
    content = """
import React, { PropTypes } from 'react';

const Component = ({ label, onClick, disabled }) => {
    return <button onClick={onClick} disabled={disabled}>{label}</button>;
};

Component.propTypes = {
    label: PropTypes.string.isRequired,
    onClick: PropTypes.func.isRequired,
    disabled: PropTypes.bool
};
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.tsx": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.tsx")
        component = file.functions[0]
        component.convert_props_to_interface()

    # language=typescript
    assert (
        file.content
        == """
interface ComponentProps {
    label: string;
    onClick: CallableFunction;
    disabled?: boolean;
}

const Component = ({ label, onClick, disabled }: ComponentProps) => {
    return <button onClick={onClick} disabled={disabled}>{label}</button>;
};
    """
    )


def test_convert_complex_function_props_to_interface(tmpdir):
    # language=typescript
    content = """
import React, { PropTypes } from 'react';

const Component = ({ data, columns, sorting, pagination, onSort, onPageChange }) => {
    return <div>{/* implementation */}</div>;
};

Component.propTypes = {
    data: PropTypes.arrayOf(PropTypes.object).isRequired,
    columns: PropTypes.arrayOf(PropTypes.shape({
        id: PropTypes.string.isRequired,
        title: PropTypes.string.isRequired,
        width: PropTypes.oneOfType([
            PropTypes.number,
            PropTypes.string
        ]),
        formatter: PropTypes.func
    })).isRequired,
    sorting: PropTypes.shape({
        column: PropTypes.string,
        direction: PropTypes.oneOf(['asc', 'desc'])
    }),
    pagination: PropTypes.shape({
        currentPage: PropTypes.number.isRequired,
        pageSize: PropTypes.number.isRequired,
        totalItems: PropTypes.number.isRequired
    }),
    onSort: PropTypes.func,
    onPageChange: PropTypes.func.isRequired
};
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.tsx": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.tsx")
        component = file.functions[0]
        component.convert_props_to_interface()

    # language=typescript
    assert (
        file.content
        == """
interface ComponentProps {
    data: object[];
    columns: {
        id: string;
        title: string;
        width?: number | string;
        formatter?: CallableFunction;
    }[];
    sorting?: {
        column?: string;
        direction?: 'asc' | 'desc';
    };
    pagination?: {
        currentPage: number;
        pageSize: number;
        totalItems: number;
    };
    onSort?: CallableFunction;
    onPageChange: CallableFunction;
}

const Component = ({ data, columns, sorting, pagination, onSort, onPageChange }: ComponentProps) => {
    return <div>{/* implementation */}</div>;
};
    """
    )


def test_convert_simple_class_props_to_interface(tmpdir):
    # language=typescript
    content = """
import React, { PropTypes } from 'react';

class Component extends React.Component {
    render() {
        return <div>{/* implementation */}</div>;
    }
}

Component.propTypes = {
    isOn: PropTypes.bool.isRequired,
    label: PropTypes.string,
    onChange: PropTypes.func.isRequired,
    size: PropTypes.oneOf(['small', 'medium', 'large'])
};
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.tsx": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.tsx")
        component = file.classes[0]
        component.convert_props_to_interface()

    # language=typescript
    assert (
        file.content
        == """
import React from 'react';

interface ComponentProps {
    isOn: boolean;
    label?: string;
    onChange: CallableFunction;
    size?: 'small' | 'medium' | 'large';
}

class Component extends React.Component<ComponentProps> {
    render() {
        return <div>{/* implementation */}</div>;
    }
}
    """
    )


def test_convert_function_props_with_inferred_parameters_to_interface(tmpdir):
    # language=typescript
    content = """
import React, { PropTypes } from 'react';

function parseIntValue(value: string): number {
    return parseInt(value);
}

const Component = ({ onValueChange, onValidate }) => {
    const handleChange = (e) => {
        const value = parseIntValue(e.target.value);
        onValueChange(value);
    };

    const handleValidate = (text: string) => {
        onValidate?.(text);
    };

    return <input onChange={handleChange} onBlur={(e) => handleValidate(e.target.value)} />;
};

Component.propTypes = {
    onValueChange: PropTypes.func.isRequired,
    onValidate: PropTypes.func
};
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.tsx": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.tsx")
        component = file.functions[-1]
        component.convert_props_to_interface()

    # language=typescript
    assert (
        file.content
        == """
function parseIntValue(value: string): number {
    return parseInt(value);
}

interface ComponentProps {
    onValueChange: CallableFunction;
    onValidate?: CallableFunction;
}

const Component = ({ onValueChange, onValidate }: ComponentProps) => {
    const handleChange = (e) => {
        const value = parseIntValue(e.target.value);
        onValueChange(value);
    };

    const handleValidate = (text: string) => {
        onValidate?.(text);
    };

    return <input onChange={handleChange} onBlur={(e) => handleValidate(e.target.value)} />;
};
    """
    )


def test_convert_class_props_with_inferred_parameters_to_interface(tmpdir):
    # language=typescript
    content = """
import React, { PropTypes } from 'react';

class Component extends React.Component {
    handleTextChange = (e) => {
        const text = e.target.value;
        this.props.onTextChange(text);
    };

    handleValidate = (count: number) => {
        this.props.onValidate?.(count);
    };

    render() {
        return <input
            onChange={this.handleTextChange}
            onBlur={() => this.handleValidate(this.props.value.length)}
        />;
    }
}

Component.propTypes = {
    onTextChange: PropTypes.func.isRequired,
    onValidate: PropTypes.func,
    value: PropTypes.string.isRequired
};
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.tsx": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.tsx")
        component = file.classes[0]
        component.convert_props_to_interface()

    # language=typescript
    assert (
        file.content
        == """
import React from 'react';

interface ComponentProps {
    onTextChange: CallableFunction;
    onValidate?: CallableFunction;
    value: string;
}

class Component extends React.Component<ComponentProps> {
    handleTextChange = (e) => {
        const text = e.target.value;
        this.props.onTextChange(text);
    };

    handleValidate = (count: number) => {
        this.props.onValidate?.(count);
    };

    render() {
        return <input
            onChange={this.handleTextChange}
            onBlur={() => this.handleValidate(this.props.value.length)}
        />;
    }
}
    """
    )


def test_convert_props_to_interface_with_any_params(tmpdir):
    # language=typescript
    content = """
import { PropTypes } from 'react';

const Component = ({ data, onProcess }) => {
    onProcess(data);
    return <div>{/* implementation */}</div>;
};

Component.propTypes = {
    data: PropTypes.any,
    onProcess: PropTypes.func
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.tsx": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.tsx")
        component = file.functions[0]
        component.convert_props_to_interface()

    # language=typescript
    assert (
        file.content
        == """
interface ComponentProps {
    data?: any;
    onProcess?: CallableFunction;
}

const Component = ({ data, onProcess }: ComponentProps) => {
    onProcess(data);
    return <div>{/* implementation */}</div>;
};
    """
    )


def test_convert_class_props_to_interface_with_any_params(tmpdir):
    # language=typescript
    content = """
import React, { PropTypes } from 'react';

class Component extends React.Component {
    render() {
        this.props.onComplete(this.props.input);
        return <div>{/* implementation */}</div>;
    }
}

Component.propTypes = {
    input: PropTypes.any.isRequired,
    config: PropTypes.any,
    onComplete: PropTypes.func.isRequired
};
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.tsx": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.tsx")
        component = file.classes[0]
        component.convert_props_to_interface()

    # language=typescript
    assert (
        file.content
        == """
import React from 'react';

interface ComponentProps {
    input: any;
    config?: any;
    onComplete: CallableFunction;
}

class Component extends React.Component<ComponentProps> {
    render() {
        this.props.onComplete(this.props.input);
        return <div>{/* implementation */}</div>;
    }
}
    """
    )


def test_convert_complex_class_props_to_interface(tmpdir):
    # language=typescript
    content = """
import React, { PropTypes } from "react";

class Component extends React.Component {
    render() {
        return <div>{/* implementation */}</div>;
    }
}

Component.propTypes = {
    schema: PropTypes.shape({
        fields: PropTypes.arrayOf(PropTypes.shape({
            name: PropTypes.string.isRequired,
            type: PropTypes.oneOf(['text', 'number', 'select', 'checkbox']).isRequired,
            label: PropTypes.string.isRequired,
            validation: PropTypes.shape({
                required: PropTypes.bool,
                min: PropTypes.number,
                max: PropTypes.number,
                pattern: PropTypes.string
            }),
            options: PropTypes.arrayOf(PropTypes.shape({
                value: PropTypes.oneOfType([
                    PropTypes.string,
                    PropTypes.number
                ]).isRequired,
                label: PropTypes.string.isRequired
            }))
        })).isRequired
    }).isRequired,
    initialValues: PropTypes.object,
    onSubmit: PropTypes.func.isRequired,
    onValidate: PropTypes.func,
    customComponents: PropTypes.objectOf(PropTypes.func)
};
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.tsx": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.tsx")
        component = file.classes[0]
        component.convert_props_to_interface()

    # language=typescript
    assert (
        file.content
        == """
import React from "react";

interface ComponentProps {
    schema: {
        fields: {
            name: string;
            type: 'text' | 'number' | 'select' | 'checkbox';
            label: string;
            validation?: {
                required?: boolean;
                min?: number;
                max?: number;
                pattern?: string;
            };
            options?: {
                value: string | number;
                label: string;
            }[];
        }[];
    };
    initialValues?: object;
    onSubmit: CallableFunction;
    onValidate?: CallableFunction;
    customComponents?: {
        [key: string]: CallableFunction;
    };
}

class Component extends React.Component<ComponentProps> {
    render() {
        return <div>{/* implementation */}</div>;
    }
}
    """
    )


def test_convert_props_to_interface_with_nested_structures(tmpdir):
    # language=typescript
    content = """
import React, { PropTypes } from 'react';

const Component = ({ user, settings, onUpdate }) => {
    return <div>{/* implementation */}</div>;
};

Component.propTypes = {
    user: PropTypes.shape({
        id: PropTypes.string.isRequired,
        name: PropTypes.shape({
            first: PropTypes.string.isRequired,
            last: PropTypes.string.isRequired,
            title: PropTypes.oneOf(['Mr', 'Mrs', 'Ms', 'Dr'])
        }),
        contact: PropTypes.shape({
            email: PropTypes.string.isRequired,
            phones: PropTypes.arrayOf(PropTypes.shape({
                type: PropTypes.oneOf(['home', 'work', 'mobile']),
                number: PropTypes.string.isRequired
            }))
        })
    }).isRequired,
    settings: PropTypes.shape({
        theme: PropTypes.oneOf(['light', 'dark']),
        notifications: PropTypes.shape({
            email: PropTypes.bool,
            push: PropTypes.bool
        })
    }),
    onUpdate: PropTypes.func.isRequired
};

const OtherComponent = () => <div>Not converted</div>;
OtherComponent.propTypes = {
    foo: PropTypes.string
};
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.tsx": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.tsx")
        component = file.functions[0]
        component.convert_props_to_interface()

    # language=typescript
    assert (
        file.content
        == """
interface ComponentProps {
    user: {
        id: string;
        name?: {
            first: string;
            last: string;
            title?: 'Mr' | 'Mrs' | 'Ms' | 'Dr';
        };
        contact?: {
            email: string;
            phones?: {
                type?: 'home' | 'work' | 'mobile';
                number: string;
            }[];
        };
    };
    settings?: {
        theme?: 'light' | 'dark';
        notifications?: {
            email?: boolean;
            push?: boolean;
        };
    };
    onUpdate: CallableFunction;
}

const Component = ({ user, settings, onUpdate }: ComponentProps) => {
    return <div>{/* implementation */}</div>;
};

const OtherComponent = () => <div>Not converted</div>;
OtherComponent.propTypes = {
    foo: PropTypes.string
};
    """
    )


def test_convert_class_props_to_interface_with_nested_structures(tmpdir):
    # language=typescript
    content = """
import React, { PropTypes } from 'react';

class Component extends React.Component {
    render() {
        return <div>{/* implementation */}</div>;
    }
}

Component.propTypes = {
    user: PropTypes.shape({
        id: PropTypes.string.isRequired,
        name: PropTypes.shape({
            first: PropTypes.string.isRequired,
            last: PropTypes.string.isRequired,
            title: PropTypes.oneOf(['Mr', 'Mrs', 'Ms', 'Dr'])
        }),
        contact: PropTypes.shape({
            email: PropTypes.string.isRequired,
            phones: PropTypes.arrayOf(PropTypes.shape({
                type: PropTypes.oneOf(['home', 'work', 'mobile']),
                number: PropTypes.string.isRequired
            }))
        })
    }).isRequired,
    settings: PropTypes.shape({
        theme: PropTypes.oneOf(['light', 'dark']),
        notifications: PropTypes.shape({
            email: PropTypes.bool,
            push: PropTypes.bool
        })
    }),
    onUpdate: PropTypes.func.isRequired
};

class OtherComponent extends React.Component {
    render() {
        return <div>Not converted</div>;
    }
}
OtherComponent.propTypes = {
    foo: PropTypes.string
};
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.tsx": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.tsx")
        component = file.classes[0]
        component.convert_props_to_interface()

    # language=typescript
    assert (
        file.content
        == """
import React from 'react';

interface ComponentProps {
    user: {
        id: string;
        name?: {
            first: string;
            last: string;
            title?: 'Mr' | 'Mrs' | 'Ms' | 'Dr';
        };
        contact?: {
            email: string;
            phones?: {
                type?: 'home' | 'work' | 'mobile';
                number: string;
            }[];
        };
    };
    settings?: {
        theme?: 'light' | 'dark';
        notifications?: {
            email?: boolean;
            push?: boolean;
        };
    };
    onUpdate: CallableFunction;
}

class Component extends React.Component<ComponentProps> {
    render() {
        return <div>{/* implementation */}</div>;
    }
}

class OtherComponent extends React.Component {
    render() {
        return <div>Not converted</div>;
    }
}
OtherComponent.propTypes = {
    foo: PropTypes.string
};
    """
    )


def test_convert_props_to_interface_with_proptypes_node_and_element(tmpdir):
    # language=typescript
    content = """
import { PropTypes } from 'react';

const Component = ({ children, element }) => {
    return <div>{children}{element}</div>;
};

Component.propTypes = {
    children: PropTypes.node,
    element: PropTypes.element
}

class ClassComponent extends React.Component {
    render() {
        return <div>{this.props.children}{this.props.element}</div>;
    }
}

ClassComponent.propTypes = {
    children: PropTypes.node.isRequired,
    element: PropTypes.element.isRequired
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.tsx": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.tsx")

        # Convert function component
        func_component = file.functions[0]
        func_component.convert_props_to_interface()

        # Convert class component
        class_component = file.classes[0]
        class_component.convert_props_to_interface()

    # language=typescript
    assert (
        file.content
        == """
import React from 'react';

interface ComponentProps<T extends React.ReactNode> {
    children?: T;
    element?: React.ReactElement;
}

const Component = ({ children, element }: ComponentProps<React.ReactNode>) => {
    return <div>{children}{element}</div>;
};

interface ClassComponentProps<T extends React.ReactNode> {
    children: T;
    element: React.ReactElement;
}

class ClassComponent extends React.Component<ClassComponentProps<React.ReactNode>> {
    render() {
        return <div>{this.props.children}{this.props.element}</div>;
    }
}
    """
    )
