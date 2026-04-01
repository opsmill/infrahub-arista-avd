from typing import Any, NamedTuple

from infrahub_sdk.transforms import InfrahubTransform

from solution_ai_dc.protocols import LocationRack, DcimDevice, DcimInterface, DcimConnector, NetworkPod, ComputePhysicalServer

from .fabric_cabling_plan_query import FabricCablingPlanQuery


class ProcessedInputData(NamedTuple):
    link_ids: list[str]
    pod_ids: list[str]
    device_ids: list[str]
    rack_ids: list[str]
    interface_ids: list[str]


class CablingPlan(InfrahubTransform):
    query = "cabling_plan"

    def generate_csv(self, links: list[DcimConnector]) -> str:
        csv_data: list[list[str]] = []

        header: str = ",".join(  # noqa: FLY002
            [
                "Source Rack",
                "Source Device",
                "Source Interface",
                "Destination Rack",
                "Destination Device",
                "Destination Interface",
            ]
        )
        for link in links:
            [src_interface, dst_interface] = link.connected_endpoints.peers
            print(link.id, src_interface.peer, dst_interface.peer)
            if not dst_interface.peer.device.id:
                continue
            csv_data.append(
                [
                    src_interface.peer.device.peer.rack.peer.name.value
                    if src_interface.peer.device.peer.rack.initialized
                    else "",
                    src_interface.peer.device.peer.name.value,
                    src_interface.peer.name.value,
                    dst_interface.peer.device.peer.rack.peer.name.value
                    if dst_interface.peer.device.peer.rack.initialized
                    else "",
                    dst_interface.peer.device.peer.name.value,
                    dst_interface.peer.name.value,
                ]
            )

        rows = "\n".join([",".join(entry) for entry in csv_data])
        return header + "\n" + rows

    def process_transform_input_data(self, data: FabricCablingPlanQuery) -> ProcessedInputData:
        link_ids: list[str] = []
        pod_ids: list[str] = []
        device_ids: list[str] = []
        rack_ids: list[str] = []
        interface_ids: list[str] = []
        pod_nodes = data.network_fabric.edges[0].node.children.edges

        for pod_node in pod_nodes:
            pod = pod_node.node
            pod_ids.append(pod.id)
            for device_node in pod.devices.edges:
                device = device_node.node
                device_ids.append(device.id)

                if device.rack.node:
                    rack_ids.append(device.rack.node.id)

                for interface_node in device.interfaces.edges:
                    interface = interface_node.node
                    interface_ids.append(interface.id)
                    if interface.connector.node is not None:
                        link_ids.append(interface.connector.node.id)

        return ProcessedInputData(link_ids, pod_ids, device_ids, rack_ids, interface_ids)

    async def transform(self, data: dict[str, Any]) -> str:
        data: FabricCablingPlanQuery = FabricCablingPlanQuery(**data)
        link_ids, pod_ids, device_ids, rack_ids, interface_ids = self.process_transform_input_data(data=data)

        links: list[DcimConnector] = await self.client.filters(DcimConnector, ids=link_ids, include=["connected_endpoints"])

        # populate SDK client store with all relevant objects
        await self.client.filters(DcimDevice, ids=device_ids, include=["interfaces", "rack"])
        await self.client.filters(DcimInterface, ids=interface_ids, include=["connector", "device"])
        await self.client.filters(LocationRack, ids=rack_ids, include=["devices"])

        return self.generate_csv(links)
