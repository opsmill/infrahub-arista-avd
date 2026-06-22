import operator
from typing import Any

from infrahub_sdk.transforms import InfrahubTransform

from .fabric_cabling_plan_query import FabricCablingPlanQuery


class CablingPlan(InfrahubTransform):
    query = "cabling_plan"

    def _collect_link_ids(self, data: FabricCablingPlanQuery) -> list[str]:
        """Collect all link/connector IDs from the fabric hierarchy."""
        link_ids: list[str] = []
        fabric = data.network_fabric.edges[0].node

        for pod_edge in fabric.children.edges:
            pod = pod_edge.node

            # Devices directly under pod (spines, super-spines)
            for device_edge in pod.devices.edges:
                device = device_edge.node
                for iface_edge in device.interfaces.edges:
                    iface = iface_edge.node
                    connector = getattr(iface, "connector", None)
                    if connector and connector.node is not None:
                        link_ids.append(connector.node.id)

            # Devices under racks (leafs, l2leafs)
            racks = getattr(pod, "racks", None)
            if racks:
                for rack_edge in racks.edges:
                    for device_edge in rack_edge.node.devices.edges:
                        device = device_edge.node
                        ifaces = getattr(device, "interfaces", None)
                        if not ifaces:
                            continue
                        for iface_edge in ifaces.edges:
                            iface = iface_edge.node
                            connector = getattr(iface, "connector", None)
                            if connector and connector.node is not None:
                                link_ids.append(connector.node.id)

        return list(set(link_ids))  # dedupe

    async def _fetch_links_with_details(self, link_ids: list[str]) -> list[dict[str, Any]]:
        """Fetch all links with full endpoint details via GraphQL."""
        if not link_ids:
            return []

        # Query links in batches to avoid query size limits
        all_rows: list[dict[str, Any]] = []
        batch_size = 50

        for i in range(0, len(link_ids), batch_size):
            batch = link_ids[i : i + batch_size]
            query = """
            query($ids: [ID!]) {
                NetworkLink(ids: $ids) {
                    edges {
                        node {
                            id
                            connected_endpoints {
                                edges {
                                    node {
                                        __typename
                                        ... on InterfacePhysical {
                                            name { value }
                                            device {
                                                node {
                                                    ... on DcimDevice {
                                                        name { value }
                                                        rack { node { name { value } } }
                                                    }
                                                }
                                            }
                                        }
                                        ... on DcimInterface {
                                            name { value }
                                            device {
                                                node {
                                                    ... on DcimDevice {
                                                        name { value }
                                                        rack { node { name { value } } }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            """
            result = await self.client.execute_graphql(query=query, variables={"ids": batch})

            for edge in result.get("NetworkLink", {}).get("edges", []):
                link = edge["node"]
                endpoints = link.get("connected_endpoints", {}).get("edges", [])
                if len(endpoints) != 2:
                    continue

                src = endpoints[0]["node"]
                dst = endpoints[1]["node"]

                src_name = (src.get("name") or {}).get("value", "")
                dst_name = (dst.get("name") or {}).get("value", "")

                src_device = (src.get("device") or {}).get("node") or {}
                dst_device = (dst.get("device") or {}).get("node") or {}

                src_dev_name = (src_device.get("name") or {}).get("value", "")
                dst_dev_name = (dst_device.get("name") or {}).get("value", "")

                src_rack = (src_device.get("rack") or {}).get("node") or {}
                dst_rack = (dst_device.get("rack") or {}).get("node") or {}

                src_rack_name = (src_rack.get("name") or {}).get("value", "")
                dst_rack_name = (dst_rack.get("name") or {}).get("value", "")

                if src_dev_name and dst_dev_name:
                    all_rows.append(
                        {
                            "src_rack": src_rack_name,
                            "src_device": src_dev_name,
                            "src_interface": src_name,
                            "dst_rack": dst_rack_name,
                            "dst_device": dst_dev_name,
                            "dst_interface": dst_name,
                        }
                    )

        return all_rows

    async def transform(self, data: dict[str, Any]) -> str:
        data: FabricCablingPlanQuery = FabricCablingPlanQuery(**data)
        link_ids = self._collect_link_ids(data)

        rows = await self._fetch_links_with_details(link_ids)

        # Sort by source device then interface
        rows.sort(key=operator.itemgetter("src_device", "src_interface"))

        header = "Source Rack,Source Device,Source Interface,Destination Rack,Destination Device,Destination Interface"
        csv_rows = [
            f"{r['src_rack']},{r['src_device']},{r['src_interface']},{r['dst_rack']},{r['dst_device']},{r['dst_interface']}"
            for r in rows
        ]

        return header + "\n" + "\n".join(csv_rows)
