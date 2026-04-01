from typing import Any

from infrahub_sdk.transforms import InfrahubTransform

from .computed_interface_description_query import ComputedInterfaceDescriptionQuery


class ComputedInterfaceDescription(InfrahubTransform):
    query = "computed_interface_description"

    async def transform(self, data: dict[str, Any]) -> str:
        data: ComputedInterfaceDescriptionQuery = ComputedInterfaceDescriptionQuery(**data)

        src_interface = data.dcim_interface.edges[0].node.id
        dcim_connector = data.dcim_interface.edges[0].node.connector.node

        if not dcim_connector:
            return ""

        endpoint_edges = dcim_connector.connected_endpoints.edges

        for endpoint_node in endpoint_edges:
            if endpoint_node.node.id == src_interface:
                continue
            dst_interface = endpoint_node.node
            return f"-> {dst_interface.device.node.name.value} {dst_interface.name.value}"

        return ""
