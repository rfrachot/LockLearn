from datasets.tools.validate_resources import validate


def test_resource_registries_are_consistent() -> None:
    validate()
