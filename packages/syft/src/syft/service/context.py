# stdlib
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

# third party
from typing_extensions import Self

# relative
from ..abstract_node import AbstractNode
from ..node.credentials import SyftVerifyKey
from ..node.credentials import UserLoginCredentials
from ..serde.serializable import serializable
from ..store.document_store import BaseStash
from ..types.syft_object import Context
from ..types.syft_object import SYFT_OBJECT_VERSION_1
from ..types.syft_object import SyftBaseObject
from ..types.syft_object import SyftObject
from ..types.uid import UID
from .user.user_roles import ROLE_TO_CAPABILITIES
from .user.user_roles import ServiceRole
from .user.user_roles import ServiceRoleCapability


@serializable(attrs=["authentication", "kv_store"])
class UserSession(SyftObject):
    # version
    __canonical_name__ = "UserSession"
    __version__ = SYFT_OBJECT_VERSION_1

    authentication: Dict[str, str] = {}
    kv_store: Dict[str, Any] = {}
    verify_key: Optional[SyftVerifyKey] = None
    stash: Optional[BaseStash] = None

    def __getitem__(self, key: str) -> Any:
        return self.get_key(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.set_key(key, value)

    def get_key(self, key: str) -> Optional[str]:
        user = self.get_user_session()
        self.kv_store = user.kv_store
        return self.kv_store.get(key, None)

    def set_key(self, key: str, value: str) -> None:
        self.kv_store[key] = value
        self.update_user_session()

    def get_auth(self, key: str) -> Optional[str]:
        user = self.get_user_session()
        self.authentication = user.authentication
        return self.authentication.get(key, None)

    def set_auth(self, key: str, value: str) -> None:
        self.authentication[key] = value
        self.update_user_session()

    def get_user(self) -> Any:
        result = self.stash.get_by_verify_key(
            credentials=self.verify_key, verify_key=self.verify_key
        )
        if result.is_ok():
            user = result.ok()
            if user:
                return user
        return None

    def get_user_session(self) -> Self:
        user = self.get_user()
        if user:
            if user.session:
                return user.session
            return self
        return None

    def update_user_session(self) -> None:
        user = self.get_user()
        if user.session:
            user.session.authentication = self.authentication
            user.session.kv_store = self.kv_store
        else:
            user.session = self
        self.stash.update(credentials=self.verify_key, user=user)


class NodeServiceContext(Context, SyftObject):
    __canonical_name__ = "NodeServiceContext"
    __version__ = SYFT_OBJECT_VERSION_1
    id: Optional[UID]
    node: Optional[AbstractNode]


class AuthedServiceContext(NodeServiceContext):
    __canonical_name__ = "AuthedServiceContext"
    __version__ = SYFT_OBJECT_VERSION_1

    credentials: SyftVerifyKey
    role: ServiceRole = ServiceRole.NONE
    session: Optional[UserSession]

    def capabilities(self) -> List[ServiceRoleCapability]:
        return ROLE_TO_CAPABILITIES.get(self.role, [])


class UnauthedServiceContext(NodeServiceContext):
    __canonical_name__ = "UnauthedServiceContext"
    __version__ = SYFT_OBJECT_VERSION_1

    login_credentials: UserLoginCredentials
    node: Optional[AbstractNode]
    role: ServiceRole = ServiceRole.NONE


class ChangeContext(SyftBaseObject):
    node: Optional[AbstractNode] = None
    approving_user_credentials: Optional[SyftVerifyKey]
    requesting_user_credentials: Optional[SyftVerifyKey]

    @staticmethod
    def from_service(context: AuthedServiceContext) -> Self:
        return ChangeContext(
            node=context.node, approving_user_credentials=context.credentials
        )
