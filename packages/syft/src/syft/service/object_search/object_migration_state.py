# stdlib
from typing import List
from typing import Optional

# third party
from result import Result

# relative
from ...node.credentials import SyftVerifyKey
from ...serde.serializable import serializable
from ...store.document_store import BaseStash
from ...store.document_store import DocumentStore
from ...store.document_store import PartitionKey
from ...store.document_store import PartitionSettings
from ...types.syft_object import SYFT_OBJECT_VERSION_1
from ...types.syft_object import SyftObject
from ..action.action_permissions import ActionObjectPermission
from ..user.user import User


@serializable()
class SyftObjectMigrationState(SyftObject):
    __canonical_name__ = "SyftObjectMigrationState"
    __version__ = SYFT_OBJECT_VERSION_1

    canonical_name: str
    current_version: int


KlassNamePartitionKey = PartitionKey(key="canonical_name", type_=str)


class SyftMigrationStateStash(BaseStash):
    object_type = SyftObjectMigrationState
    settings: PartitionSettings = PartitionSettings(
        name=User.__canonical_name__,
        object_type=SyftObjectMigrationState,
    )

    def __init__(self, store: DocumentStore) -> None:
        super().__init__(store=store)

    def set(
        self,
        credentials: SyftVerifyKey,
        syft_object_metadata: SyftObjectMigrationState,
        add_permissions: Optional[List[ActionObjectPermission]] = None,
    ) -> Result[SyftObjectMigrationState, str]:
        res = self.check_type(syft_object_metadata, self.object_type)
        # we dont use and_then logic here as it is hard because of the order of the arguments
        if res.is_err():
            return res
        return super().set(
            credentials=credentials, obj=res.ok(), add_permissions=add_permissions
        )

    def get_by_name(
        self, canonical_name: str, credentials: SyftVerifyKey
    ) -> Result[SyftObjectMigrationState, str]:
        qks = KlassNamePartitionKey.with_obj(canonical_name)
        return self.query_one(credentials=credentials, qks=qks)