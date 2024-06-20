# stdlib
import re
from types import MethodType
from typing import Any

# relative
from ..types.dicttuple import DictTuple
from .abstract_node import NodeSideType  # noqa: F401
from .abstract_node import NodeType  # noqa: F401
from .client.client import connect  # noqa: F401
from .client.client import login  # noqa: F401
from .client.client import login_as_guest  # noqa: F401
from .client.client import register  # noqa: F401
from .client.domain_client import DomainClient  # noqa: F401
from .client.gateway_client import GatewayClient  # noqa: F401
from .client.registry import DomainRegistry  # noqa: F401
from .client.registry import EnclaveRegistry  # noqa: F401
from .client.registry import NetworkRegistry  # noqa: F401
from .client.search import Search  # noqa: F401
from .client.search import SearchResults  # noqa: F401
from .client.user_settings import UserSettings  # noqa: F401
from .client.user_settings import settings  # noqa: F401
from .custom_worker.config import DockerWorkerConfig  # noqa: F401
from .custom_worker.config import PrebuiltWorkerConfig  # noqa: F401
from .node.credentials import SyftSigningKey  # noqa: F401
from .node.domain import Domain  # noqa: F401
from .node.enclave import Enclave  # noqa: F401
from .node.gateway import Gateway  # noqa: F401
from .node.server import serve_node  # noqa: F401
from .node.server import serve_node as bind_worker  # noqa: F401
from .node.worker import Worker  # noqa: F401
from .orchestra import Orchestra as orchestra  # noqa: F401
from .protocol.data_protocol import bump_protocol_version  # noqa: F401
from .protocol.data_protocol import check_or_stage_protocol  # noqa: F401
from .protocol.data_protocol import get_data_protocol  # noqa: F401
from .protocol.data_protocol import stage_protocol_changes  # noqa: F401
from .serde import NOTHING  # noqa: F401
from .serde.deserialize import _deserialize as deserialize  # noqa: F401
from .serde.serializable import serializable  # noqa: F401
from .serde.serialize import _serialize as serialize  # noqa: F401
from .service.action.action_data_empty import ActionDataEmpty  # noqa: F401
from .service.action.action_object import ActionObject  # noqa: F401
from .service.action.plan import Plan  # noqa: F401
from .service.action.plan import planify  # noqa: F401
from .service.api.api import api_endpoint  # noqa: F401
from .service.api.api import api_endpoint_method  # noqa: F401
from .service.api.api import create_new_api_endpoint as TwinAPIEndpoint  # noqa: F401
from .service.code.user_code import UserCodeStatus  # noqa: F401; noqa: F401
from .service.code.user_code import syft_function  # noqa: F401; noqa: F401
from .service.code.user_code import syft_function_single_use  # noqa: F401; noqa: F401
from .service.data_subject import DataSubjectCreate as DataSubject  # noqa: F401
from .service.dataset.dataset import Contributor  # noqa: F401
from .service.dataset.dataset import CreateAsset as Asset  # noqa: F401
from .service.dataset.dataset import CreateDataset as Dataset  # noqa: F401
from .service.notification.notifications import NotificationStatus  # noqa: F401
from .service.policy.policy import CustomInputPolicy  # noqa: F401
from .service.policy.policy import CustomOutputPolicy  # noqa: F401
from .service.policy.policy import ExactMatch  # noqa: F401
from .service.policy.policy import SingleExecutionExactOutput  # noqa: F401
from .service.policy.policy import UserInputPolicy  # noqa: F401
from .service.policy.policy import UserOutputPolicy  # noqa: F401
from .service.project.project import ProjectSubmit as Project  # noqa: F401
from .service.request.request import SubmitRequest as Request  # noqa: F401
from .service.response import SyftError  # noqa: F401
from .service.response import SyftNotReady  # noqa: F401
from .service.response import SyftSuccess  # noqa: F401
from .service.user.roles import Roles as roles  # noqa: F401
from .service.user.user_service import UserService  # noqa: F401
from .types.syft_object import SyftObject
from .types.twin_object import TwinObject  # noqa: F401
from .types.uid import UID  # noqa: F401
from .util import filterwarnings  # noqa: F401
from .util import logger  # noqa: F401
from .util import options  # noqa: F401
from .util.autoreload import disable_autoreload  # noqa: F401
from .util.autoreload import enable_autoreload  # noqa: F401
from .util.telemetry import instrument  # noqa: F401
from .util.util import autocache  # noqa: F401
from .util.util import get_root_data_path  # noqa: F401


def _patch_ipython_sanitization() -> None:
    try:
        # third party
        from IPython import get_ipython
    except ImportError:
        return

    ip = get_ipython()
    if ip is None:
        return

    # stdlib
    from importlib import resources

    # third party
    import nh3

    # relative
    from .util.assets import load_css
    from .util.assets import load_js
    from .util.notebook_ui.styles import CSS_CODE
    from .util.notebook_ui.styles import FONT_CSS
    from .util.notebook_ui.styles import ITABLES_CSS
    from .util.notebook_ui.styles import JS_DOWNLOAD_FONTS

    tabulator_js = load_js("tabulator.min.js")
    tabulator_js = tabulator_js.replace(
        "define(t)", "define('tabulator-tables', [], t)"
    )

    SKIP_SANITIZE = [
        FONT_CSS,
        ITABLES_CSS,
        CSS_CODE,
        JS_DOWNLOAD_FONTS,
        tabulator_js,
        load_css("tabulator_pysyft.min.css"),
        load_js("table.js"),
    ]

    css_reinsert = f"""
<style>{FONT_CSS}</style>
<style>{ITABLES_CSS}</style>
{JS_DOWNLOAD_FONTS}
{CSS_CODE}
"""

    escaped_js_css = re.compile(
        "|".join(re.escape(substr) for substr in SKIP_SANITIZE),
        re.IGNORECASE | re.MULTILINE,
    )

    table_template = (
        resources.files("syft.assets.jinja").joinpath("table.jinja2").read_text()
    )
    table_template = table_template.strip()
    table_template = re.sub(r"\\{\\{.*?\\}\\}", ".*?", re.escape(table_template))
    escaped_template = re.compile(table_template, re.DOTALL | re.VERBOSE)

    def display_sanitized_html(obj: SyftObject | DictTuple) -> str | None:
        if hasattr(obj, "_repr_html_") and callable(obj._repr_html_):  # type: ignore
            _str = obj._repr_html_()  # type: ignore
            matching_template = escaped_template.findall(_str)
            _str = escaped_template.sub("", _str)
            _str = escaped_js_css.sub("", _str)
            _str = nh3.clean(_str)
            return f"{css_reinsert} {_str} {"\n".join(matching_template)}"
        return None

    def display_sanitized_md(obj: SyftObject) -> None:
        if hasattr(obj, "_repr_markdown_"):
            return nh3.clean(obj._repr_markdown_())

    ip.display_formatter.formatters["text/html"].for_type(
        SyftObject, display_sanitized_html
    )
    ip.display_formatter.formatters["text/html"].for_type(
        DictTuple, display_sanitized_html
    )
    ip.display_formatter.formatters["text/markdown"].for_type(
        SyftObject, display_sanitized_md
    )


def _patch_ipython_autocompletion() -> None:
    try:
        # third party
        from IPython import get_ipython
        from IPython.core.guarded_eval import EVALUATION_POLICIES
    except ImportError:
        return

    ipython = get_ipython()
    if ipython is None:
        return

    try:
        # this allows property getters to be used in nested autocomplete
        ipython.Completer.evaluation = "limited"
        ipython.Completer.use_jedi = False
        policy = EVALUATION_POLICIES["limited"]

        policy.allowed_getattr_external.update(
            [
                ("syft.client.api", "APIModule"),
                ("syft.client.api", "SyftAPI"),
            ]
        )
        original_can_get_attr = policy.can_get_attr

        def patched_can_get_attr(value: Any, attr: str) -> bool:
            attr_name = "__syft_allow_autocomplete__"
            # first check if exist to prevent side effects
            if hasattr(value, attr_name) and attr in getattr(value, attr_name, []):
                if attr in dir(value):
                    return True
                else:
                    return False
            else:
                return original_can_get_attr(value, attr)

        policy.can_get_attr = patched_can_get_attr
    except Exception:
        print("Failed to patch ipython autocompletion for syft property getters")

    try:
        # this constraints the completions for autocomplete.
        # if __syft_dir__ is defined we only autocomplete those properties
        original_attr_matches = ipython.Completer.attr_matches

        def patched_attr_matches(self, text: str) -> list[str]:  # type: ignore
            res = original_attr_matches(text)
            m2 = re.match(r"(.+)\.(\w*)$", self.line_buffer)
            if not m2:
                return res
            expr, _ = m2.group(1, 2)
            obj = self._evaluate_expr(expr)
            if isinstance(obj, SyftObject) and hasattr(obj, "__syft_dir__"):
                # here we filter all autocomplete results to only contain those
                # defined in __syft_dir__, however the original autocomplete prefixes
                # have the full path, while __syft_dir__ only defines the attr
                attrs = set(obj.__syft_dir__())
                new_res = []
                for r in res:
                    splitted = r.split(".")
                    if len(splitted) > 1:
                        attr_name = splitted[-1]
                        if attr_name in attrs:
                            new_res.append(r)
                return new_res
            else:
                return res

        ipython.Completer.attr_matches = MethodType(
            patched_attr_matches, ipython.Completer
        )
    except Exception:
        print("Failed to patch syft autocompletion for __syft_dir__")


def patch_ipython() -> None:
    _patch_ipython_sanitization()
    _patch_ipython_autocompletion()
