import io
import json
from collections import defaultdict

import modal as modal_lib
from swebench.harness.constants import (
    SWEbenchInstance,
)
from swebench.harness.modal_eval.run_evaluation_modal import (
    ModalSandboxRuntime,
)
from swebench.harness.test_spec.test_spec import make_test_spec


class SnapshotManager:
    def get_snapshot_uid(self, example: SWEbenchInstance) -> str:
        msg = "Not implemented"
        raise NotImplementedError(msg)

    def save_snapshot_uid(self, example: SWEbenchInstance, snapshot_uid: str) -> None:
        msg = "Not implemented"
        raise NotImplementedError(msg)


class VolumeSnapshotManager(SnapshotManager):
    def __init__(self, volume_name: str = "swebench-agent-snapshot-volume"):
        self.snapshot_volume = modal_lib.Volume.from_name(volume_name, create_if_missing=True)
        self.snapshot_meta_file_path: str = "/root/snapshot_meta.json"

    def get_snapshot_uid(self, example: SWEbenchInstance) -> str:
        snapshot_meta = self.read_snapshot_meta()
        return snapshot_meta[example.repo][example.environment_setup_commit]

    def save_snapshot_uid(self, example: SWEbenchInstance, snapshot_uid: str) -> None:
        snapshot_meta = self.read_snapshot_meta()
        snapshot_meta[example.repo][example.environment_setup_commit] = snapshot_uid
        with self.snapshot_volume.batch_upload() as upload:
            upload.put_file(
                io.BytesIO(json.dumps(snapshot_meta).encode("utf-8")),
                self.snapshot_meta_file_path,
            )
        self.snapshot_volume.commit()

    def read_snapshot_meta(self) -> dict[str, dict[str, str]]:
        bytes_io = io.BytesIO()
        try:
            self.snapshot_volume.read_file_into_fileobj(self.snapshot_meta_file_path, bytes_io)
            snapshot_meta = json.loads(bytes_io.getvalue().decode("utf-8"))
        except FileNotFoundError:
            snapshot_meta = {}
        return defaultdict(lambda: defaultdict(lambda: None), snapshot_meta)


class ModalDictSnapshotManager(SnapshotManager):
    def __init__(self, name: str = "swebench-agent-snapshot-dict"):
        self.snapshot_dict = modal_lib.Dict.from_name(name, create_if_missing=True)

    def get_snapshot_uid(self, example: SWEbenchInstance) -> str | None:
        try:
            return self.snapshot_dict[(example.repo, example.environment_setup_commit)]
        except KeyError:
            return None

    def save_snapshot_uid(self, example: SWEbenchInstance, snapshot_uid: str) -> None:
        self.snapshot_dict[(example.repo, example.environment_setup_commit)] = snapshot_uid


class CGModalSandboxRuntime(ModalSandboxRuntime):
    def __init__(
        self,
        example: SWEbenchInstance,
        timeout: int | None = None,
        verbose: bool = True,
    ):
        self.example = example
        self.snapshot_manager = ModalDictSnapshotManager()
        self.test_spec = make_test_spec(example)
        self.sandbox = self._get_sandbox(timeout)
        self.verbose = verbose
        self._stream_tasks = []

        # Hack for pylint
        self.write_file("/sys/fs/cgroup/cpu/cpu.shares", "2048")

    @property
    def image(self) -> modal_lib.Image:
        return ModalSandboxRuntime.get_instance_image(self.test_spec)

    def _get_sandbox(self, timeout: int | None = None):
        """Populate sandbox ourselves"""
        uid = self.snapshot_manager.get_snapshot_uid(self.example)
        if uid is None:
            sandbox = super()._get_sandbox(timeout)
            snapshot = sandbox._experimental_snapshot()
            self.snapshot_manager.save_snapshot_uid(self.example, snapshot.object_id)
        else:
            return modal_lib.Sandbox._experimental_from_snapshot(uid)
