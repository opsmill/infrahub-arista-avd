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
    super_spine_switch_template: (
        "FabricGeneratorQueryNetworkFabricEdgesNodeSuperSpineSwitchTemplate"
    )
    mgmt_gateway: Optional["FabricGeneratorQueryNetworkFabricEdgesNodeMgmtGateway"]
    asn_pool: "FabricGeneratorQueryNetworkFabricEdgesNodeAsnPool"
    node_id_pool: "FabricGeneratorQueryNetworkFabricEdgesNodeNodeIdPool"
    mgmt_pool: "FabricGeneratorQueryNetworkFabricEdgesNodeMgmtPool"


class FabricGeneratorQueryNetworkFabricEdgesNodeName(BaseModel):
    value: Optional[str]


class FabricGeneratorQueryNetworkFabricEdgesNodeAmountOfSuperSpines(BaseModel):
    value: Optional[Any]


class FabricGeneratorQueryNetworkFabricEdgesNodeSuperSpineSwitchTemplate(BaseModel):
    node: Optional[
        "FabricGeneratorQueryNetworkFabricEdgesNodeSuperSpineSwitchTemplateNode"
    ]


class FabricGeneratorQueryNetworkFabricEdgesNodeSuperSpineSwitchTemplateNode(BaseModel):
    typename__: Literal["CoreObjectTemplate", "TemplateNetworkDevice"] = Field(
        alias="__typename"
    )
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


FabricGeneratorQuery.model_rebuild()
FabricGeneratorQueryNetworkFabric.model_rebuild()
FabricGeneratorQueryNetworkFabricEdges.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNode.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeSuperSpineSwitchTemplate.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeAsnPool.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeNodeIdPool.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeMgmtPool.model_rebuild()
