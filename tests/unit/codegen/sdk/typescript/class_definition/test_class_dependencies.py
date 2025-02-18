import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


@pytest.mark.skip(reason="CG-9539 TODO @caroljung")
def test_class_dependencies(tmpdir) -> None:
    # language=typescript
    content = """
import { Component } from 'framework';
import { Helper } from './helper';
import { IConfig } from './types';
import { formatData } from './utils';

interface Props {
    data: IConfig;
}

export class ExampleClass extends Component<Props> {
    state = {
        processed: null
    };

    handleData = (config: IConfig | null) => {
        if (!config) {
            return;
        }
        const formatted = formatData(config);
        this.setState({ processed: formatted });
    };

    render() {
        const { data } = this.props;
        return (
            <div>
                <Helper data={data} onProcess={this.handleData} />
            </div>
        );
    }
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": content}) as ctx:
        file = ctx.get_file("test.tsx")
        cls = file.get_class("ExampleClass")
        deps = cls.dependencies

        # Verify class dependencies are correctly identified
        assert len(deps) > 0
        assert "Props" in [x.name for x in deps]
        assert "Helper" in [x.name for x in deps]
        assert "formatData" in [x.name for x in deps]
        assert "IConfig" in [x.name for x in deps]
        assert "Component" in [x.name for x in deps]
