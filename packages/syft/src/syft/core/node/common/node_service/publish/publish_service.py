# stdlib
from typing import Dict as TypeDict
from typing import List as TypeList
from typing import Optional
from typing import Type

# third party
from nacl.signing import VerifyKey

# relative
# syft relative
from ......core.adp.publish import publish
from ......lib.python import List
from ......logger import traceback_and_raise
from ..publish.publish_messages import PublishScalarsAction
from .....common.uid import UID
from .....store.storeable_object import StorableObject
from .....tensor.tensor import PassthroughTensor
from ....abstract.node import AbstractNode
from ....common.node_service.node_service import ImmediateNodeServiceWithoutReply


class PublishScalarsService(ImmediateNodeServiceWithoutReply):
    @staticmethod
    def process(
        node: AbstractNode, msg: PublishScalarsAction, verify_key: VerifyKey
    ) -> None:
        # get scalar objects from store
        results = List()
        for publish_id in msg.publish_ids_at_location:
            try:
                publish_object = node.store[publish_id]

                if isinstance(publish_object.data, PassthroughTensor):
                    result = publish_object.data.publish(acc=node.acc, sigma=msg.sigma)
                else:
                    result = publish([publish_object.data], node.acc, msg.sigma)
                results.append(result)
            except Exception as e:
                log = (
                    f"Unable to Get Object with ID {publish_id} from store. "
                    + f"Possible dangling Pointer. {e}"
                )
                traceback_and_raise(Exception(log))

        # give the caller permission to download this
        read_permissions: TypeDict[VerifyKey, UID] = {verify_key: None}
        search_permissions: TypeDict[VerifyKey, Optional[UID]] = {verify_key: None}

        if len(results) == 1:
            results = results[0]

        storable = StorableObject(
            id=msg.id_at_location,
            data=results,
            description=f"Approved AutoDP Result: {msg.id_at_location}",
            read_permissions=read_permissions,
            search_permissions=search_permissions,
        )

        node.store[msg.id_at_location] = storable

    @staticmethod
    def message_handler_types() -> TypeList[Type[PublishScalarsAction]]:
        return [PublishScalarsAction]
