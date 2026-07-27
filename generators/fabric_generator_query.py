from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class FabricGeneratorQuery(BaseModel):
    network_fabric: "FabricGeneratorQueryNetworkFabric" = Field(alias="NetworkFabric")


class FabricGeneratorQueryNetworkFabric(BaseModel):
    edges: list["FabricGeneratorQueryNetworkFabricEdges"]


class FabricGeneratorQueryNetworkFabricEdges(BaseModel):
    node: Optional["FabricGeneratorQueryNetworkFabricEdgesNode"]


class FabricGeneratorQueryNetworkFabricEdgesNode(BaseModel):
    id: str
    name: Optional["FabricGeneratorQueryNetworkFabricEdgesNodeName"]
    amount_of_super_spines: Optional[
        "FabricGeneratorQueryNetworkFabricEdgesNodeAmountOfSuperSpines"
    ]
    underlay_routing_protocol: Optional[
        "FabricGeneratorQueryNetworkFabricEdgesNodeUnderlayRoutingProtocol"
    ]
    super_spine_switch_template: (
        "FabricGeneratorQueryNetworkFabricEdgesNodeSuperSpineSwitchTemplate"
    )
    mgmt_gateway: Optional["FabricGeneratorQueryNetworkFabricEdgesNodeMgmtGateway"]
    asn_pool: "FabricGeneratorQueryNetworkFabricEdgesNodeAsnPool"
    node_id_pool: "FabricGeneratorQueryNetworkFabricEdgesNodeNodeIdPool"
    mgmt_pool: "FabricGeneratorQueryNetworkFabricEdgesNodeMgmtPool"
    vtep_pool: "FabricGeneratorQueryNetworkFabricEdgesNodeVtepPool"
    loopback_pool: "FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPool"


class FabricGeneratorQueryNetworkFabricEdgesNodeName(BaseModel):
    value: Optional[str]


class FabricGeneratorQueryNetworkFabricEdgesNodeAmountOfSuperSpines(BaseModel):
    value: Optional[Any]


class FabricGeneratorQueryNetworkFabricEdgesNodeUnderlayRoutingProtocol(BaseModel):
    value: Optional[str]


class FabricGeneratorQueryNetworkFabricEdgesNodeSuperSpineSwitchTemplate(BaseModel):
    node: Optional[
        "FabricGeneratorQueryNetworkFabricEdgesNodeSuperSpineSwitchTemplateNode"
    ]


class FabricGeneratorQueryNetworkFabricEdgesNodeSuperSpineSwitchTemplateNode(BaseModel):
    typename__: Literal[
        "CoreObjectTemplate", "TemplateComputePhysicalServer", "TemplateDcimDevice"
    ] = Field(alias="__typename")
    id: Optional[str]


class FabricGeneratorQueryNetworkFabricEdgesNodeMgmtGateway(BaseModel):
    value: Optional[str]


class FabricGeneratorQueryNetworkFabricEdgesNodeAsnPool(BaseModel):
    node: Optional["FabricGeneratorQueryNetworkFabricEdgesNodeAsnPoolNode"]


class FabricGeneratorQueryNetworkFabricEdgesNodeAsnPoolNode(BaseModel):
    id: str


class FabricGeneratorQueryNetworkFabricEdgesNodeNodeIdPool(BaseModel):
    node: Optional["FabricGeneratorQueryNetworkFabricEdgesNodeNodeIdPoolNode"]


class FabricGeneratorQueryNetworkFabricEdgesNodeNodeIdPoolNode(BaseModel):
    id: str


class FabricGeneratorQueryNetworkFabricEdgesNodeMgmtPool(BaseModel):
    node: Optional["FabricGeneratorQueryNetworkFabricEdgesNodeMgmtPoolNode"]


class FabricGeneratorQueryNetworkFabricEdgesNodeMgmtPoolNode(BaseModel):
    id: str


class FabricGeneratorQueryNetworkFabricEdgesNodeVtepPool(BaseModel):
    node: Optional["FabricGeneratorQueryNetworkFabricEdgesNodeVtepPoolNode"]


class FabricGeneratorQueryNetworkFabricEdgesNodeVtepPoolNode(BaseModel):
    id: str
    resources: "FabricGeneratorQueryNetworkFabricEdgesNodeVtepPoolNodeResources"


class FabricGeneratorQueryNetworkFabricEdgesNodeVtepPoolNodeResources(BaseModel):
    edges: Optional[
        list["FabricGeneratorQueryNetworkFabricEdgesNodeVtepPoolNodeResourcesEdges"]
    ]


class FabricGeneratorQueryNetworkFabricEdgesNodeVtepPoolNodeResourcesEdges(BaseModel):
    node: Optional[
        "FabricGeneratorQueryNetworkFabricEdgesNodeVtepPoolNodeResourcesEdgesNode"
    ]


class FabricGeneratorQueryNetworkFabricEdgesNodeVtepPoolNodeResourcesEdgesNode(
    BaseModel
):
    typename__: Literal[
        "BuiltinIPPrefix", "InternalIPPrefixAvailable", "IpamPrefix"
    ] = Field(alias="__typename")
    id: Optional[str]


class FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPool(BaseModel):
    node: Optional["FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPoolNode"]


class FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPoolNode(BaseModel):
    id: str
    resources: "FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPoolNodeResources"


class FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPoolNodeResources(BaseModel):
    edges: Optional[
        list["FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPoolNodeResourcesEdges"]
    ]


class FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPoolNodeResourcesEdges(
    BaseModel
):
    node: Optional[
        "FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPoolNodeResourcesEdgesNode"
    ]


class FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPoolNodeResourcesEdgesNode(
    BaseModel
):
    typename__: Literal[
        "BuiltinIPPrefix", "InternalIPPrefixAvailable", "IpamPrefix"
    ] = Field(alias="__typename")
    id: Optional[str]


FabricGeneratorQuery.model_rebuild()
FabricGeneratorQueryNetworkFabric.model_rebuild()
FabricGeneratorQueryNetworkFabricEdges.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNode.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeSuperSpineSwitchTemplate.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeAsnPool.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeNodeIdPool.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeMgmtPool.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeVtepPool.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeVtepPoolNode.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeVtepPoolNodeResources.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeVtepPoolNodeResourcesEdges.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPool.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPoolNode.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPoolNodeResources.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPoolNodeResourcesEdges.model_rebuild()
