# stdlib

# third party

# relative
from ...serde.serializable import serializable
from ...server.credentials import SyftVerifyKey
from ...store.db.stash import ObjectStash
from ...store.document_store import PartitionKey
from ...store.document_store import PartitionSettings
from ...store.document_store_errors import NotFoundException
from ...store.document_store_errors import StashException
from ...types.result import as_result
from ...types.uid import UID
from ...util.telemetry import instrument
from .notifier import NotifierSettings

NamePartitionKey = PartitionKey(key="name", type_=str)
ActionIDsPartitionKey = PartitionKey(key="action_ids", type_=list[UID])


@instrument
@serializable(canonical_name="NotifierSQLStash", version=1)
class NotifierStash(ObjectStash[NotifierSettings]):
    settings: PartitionSettings = PartitionSettings(
        name=NotifierSettings.__canonical_name__, object_type=NotifierSettings
    )

    # TODO: should this method behave like a singleton?
    @as_result(StashException, NotFoundException)
    def get(self, credentials: SyftVerifyKey) -> NotifierSettings | None:
        """Get Settings"""
        # actually get latest settings
        result = self.get_all(credentials, limit=1).unwrap()
        if len(result) > 0:
            return result[0]
        return None
