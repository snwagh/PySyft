# stdlib
from urllib.parse import urlparse

# syft absolute
import syft as sy
from syft.orchestra import ServerHandle

# relative
from ..sim.core import SimulatorContext


def server_info(client: sy.DatasiteClient) -> str:
    url = getattr(client.connection, "url", "python")
    return f"{client.name}(url={url}, side={client.metadata.server_side_type})"


def launch_server(
    ctx: SimulatorContext,
    server_url: str,
    server_name: str,
    server_side_type: str | None = "high",
) -> ServerHandle | None:
    ctx.logger.info(f"Launching python server '{server_name}' at {server_url}")
    parsed_url = urlparse(server_url)
    port = parsed_url.port
    return sy.orchestra.launch(
        name=server_name,
        server_side_type=server_side_type,
        reset=True,
        dev_mode=True,
        port=port,
        create_producer=True,
        n_consumers=1,
    )
