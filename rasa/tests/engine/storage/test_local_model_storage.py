from datetime import datetime
from pathlib import Path

import freezegun
import pytest
from _pytest.tmpdir import TempPathFactory

import rasa.shared.utils.io
from rasa.engine.graph import SchemaNode, GraphSchema, GraphModelConfiguration
from rasa.engine.storage.local_model_storage import LocalModelStorage
from rasa.engine.storage.storage import ModelStorage
from rasa.engine.storage.resource import Resource
from rasa.shared.core.domain import Domain
from rasa.shared.importers.autoconfig import TrainingType
from tests.engine.graph_components_test_classes import PersistableTestComponent


def test_write_to_and_read(default_model_storage: ModelStorage):
    test_filename = "file.txt"
    test_file_content = "hi"

    test_sub_filename = "sub_file"
    test_sub_dir_name = "sub_directory"
    test_sub_file_content = "sub file"

    resource = Resource("some_node123")

    # Fill model storage for resource
    with default_model_storage.write_to(resource) as resource_directory:
        file = resource_directory / test_filename
        file.write_text(test_file_content)

        sub_directory = resource_directory / test_sub_dir_name
        sub_directory.mkdir()
        file_in_sub_directory = sub_directory / test_sub_filename
        file_in_sub_directory.write_text(test_sub_file_content)

    # Read written resource data from model storage to see whether all expected
    # content is there
    with default_model_storage.read_from(resource) as resource_directory:
        assert (resource_directory / test_filename).read_text() == test_file_content
        assert (
            resource_directory / test_sub_dir_name / test_sub_filename
        ).read_text() == test_sub_file_content


def test_read_from_not_existing_resource(default_model_storage: ModelStorage):
    with default_model_storage.write_to(Resource("resource1")) as temporary_directory:
        file = temporary_directory / "file.txt"
        file.write_text("test")

    with pytest.raises(ValueError):
        with default_model_storage.read_from(Resource("a different resource")) as _:
            pass


def test_create_model_package(
    tmp_path_factory: TempPathFactory, domain: Domain,
):
    train_model_storage = LocalModelStorage(
        tmp_path_factory.mktemp("train model storage")
    )

    train_schema = GraphSchema(
        {
            "train": SchemaNode(
                needs={},
                uses=PersistableTestComponent,
                fn="train",
                constructor_name="create",
                config={"some_config": 123455, "some more config": [{"nested": "hi"}]},
            ),
            "load": SchemaNode(
                needs={"resource": "train"},
                uses=PersistableTestComponent,
                fn="run_inference",
                constructor_name="load",
                config={},
                is_target=True,
            ),
        }
    )

    predict_schema = GraphSchema(
        {
            "run": SchemaNode(
                needs={},
                uses=PersistableTestComponent,
                fn="run",
                constructor_name="load",
                config={"some_config": 123455, "some more config": [{"nested": "hi"}]},
            ),
        }
    )

    # Fill model Storage
    with train_model_storage.write_to(Resource("resource1")) as directory:
        file = directory / "file.txt"
        file.write_text("test")

    # Package model
    persisted_model_dir = tmp_path_factory.mktemp("persisted models")
    archive_path = persisted_model_dir / "my-model.tar.gz"

    trained_at = datetime.utcnow()
    with freezegun.freeze_time(trained_at):
        train_model_storage.create_model_package(
            archive_path,
            GraphModelConfiguration(
                train_schema, predict_schema, TrainingType.BOTH, None, None, "nlu"
            ),
            domain,
        )

    # Unpack and inspect packaged model
    load_model_storage_dir = tmp_path_factory.mktemp("load model storage")

    just_packaged_metadata = LocalModelStorage.metadata_from_archive(archive_path)

    (load_model_storage, packaged_metadata,) = LocalModelStorage.from_model_archive(
        load_model_storage_dir, archive_path
    )

    assert just_packaged_metadata.trained_at == packaged_metadata.trained_at

    assert packaged_metadata.train_schema == train_schema
    assert packaged_metadata.predict_schema == predict_schema
    assert packaged_metadata.domain.as_dict() == domain.as_dict()

    assert packaged_metadata.rasa_open_source_version == rasa.__version__
    assert packaged_metadata.trained_at == trained_at
    assert packaged_metadata.model_id
    assert packaged_metadata.project_fingerprint

    persisted_resources = load_model_storage_dir.glob("*")
    assert list(persisted_resources) == [Path(load_model_storage_dir, "resource1")]


def test_create_package_with_non_existing_parent(tmp_path: Path):
    storage = LocalModelStorage.create(tmp_path)
    model_file = tmp_path / "new" / "sub" / "dir" / "file.tar.gz"

    storage.create_model_package(
        model_file,
        GraphModelConfiguration(
            GraphSchema({}), GraphSchema({}), TrainingType.BOTH, None, None, "nlu"
        ),
        Domain.empty(),
    )

    assert model_file.is_file()


def test_create_model_package_with_non_empty_model_storage(tmp_path: Path):
    # Put something in the future model storage directory
    (tmp_path / "somefile.json").touch()

    with pytest.raises(ValueError):
        # Unpacking into an already filled `ModelStorage` raises an exception.
        _ = LocalModelStorage.from_model_archive(tmp_path, Path("does not matter"))


def test_create_model_package_with_non_existing_dir(
    tmp_path: Path, default_model_storage: ModelStorage
):
    path = tmp_path / "some_dir" / "another" / "model.tar.gz"
    default_model_storage.create_model_package(
        path,
        GraphModelConfiguration(
            GraphSchema({}), GraphSchema({}), TrainingType.BOTH, None, None, "nlu"
        ),
        Domain.empty(),
    )

    assert path.exists()
