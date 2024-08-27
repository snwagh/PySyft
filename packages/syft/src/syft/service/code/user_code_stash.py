# stdlib

# relative
from ...serde.serializable import serializable
from ...server.credentials import SyftVerifyKey
from ...store.db.stash import ObjectStash
from ...store.document_store import PartitionSettings
from ...store.document_store_errors import NotFoundException
from ...store.document_store_errors import StashException
from ...types.result import as_result
from ...util.telemetry import instrument
from .user_code import UserCode


@instrument
@serializable(canonical_name="UserCodeSQLStash", version=1)
class UserCodeStash(ObjectStash[UserCode]):
    settings: PartitionSettings = PartitionSettings(
        name=UserCode.__canonical_name__, object_type=UserCode
    )

    @as_result(StashException, NotFoundException)
    def get_by_code_hash(self, credentials: SyftVerifyKey, code_hash: str) -> UserCode:
        return self.get_one_by_field(
            credentials=credentials,
            field_name="code_hash",
            field_value=code_hash,
        ).unwrap()

    @as_result(StashException)
    def get_by_service_func_name(
        self, credentials: SyftVerifyKey, service_func_name: str
    ) -> list[UserCode]:
        return self.get_all_by_field(
            credentials=credentials,
            field_name="service_func_name",
            field_value=service_func_name,
        ).unwrap()
