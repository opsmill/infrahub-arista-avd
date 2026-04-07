from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class FabricGeneratorQuery(BaseModel):
    network_fabric: FabricGeneratorQueryNetworkFabric = Field(alias="NetworkFabric")


class FabricGeneratorQueryNetworkFabric(BaseModel):
    edges: list[FabricGeneratorQueryNetworkFabricEdges]


class FabricGeneratorQueryNetworkFabricEdges(BaseModel):
    node: FabricGeneratorQueryNetworkFabricEdgesNode | None


class FabricGeneratorQueryNetworkFabricEdgesNode(BaseModel):
    id: str
    name: FabricGeneratorQueryNetworkFabricEdgesNodeName | None
    amount_of_super_spines: FabricGeneratorQueryNetworkFabricEdgesNodeAmountOfSuperSpines | None
    super_spine_switch_template: (
        FabricGeneratorQueryNetworkFabricEdgesNodeSuperSpineSwitchTemplate
    )
    mgmt_gateway: FabricGeneratorQueryNetworkFabricEdgesNodeMgmtGateway | None
    asn_pool: FabricGeneratorQueryNetworkFabricEdgesNodeAsnPool
    node_id_pool: FabricGeneratorQueryNetworkFabricEdgesNodeNodeIdPool
    mgmt_pool: FabricGeneratorQueryNetworkFabricEdgesNodeMgmtPool


class FabricGeneratorQueryNetworkFabricEdgesNodeName(BaseModel):
    value: str | None


class FabricGeneratorQueryNetworkFabricEdgesNodeAmountOfSuperSpines(BaseModel):
    value: Any | None


class FabricGeneratorQueryNetworkFabricEdgesNodeSuperSpineSwitchTemplate(BaseModel):
    node: FabricGeneratorQueryNetworkFabricEdgesNodeSuperSpineSwitchTemplateNode | None


class FabricGeneratorQueryNetworkFabricEdgesNodeSuperSpineSwitchTemplateNode(BaseModel):
    typename__: Literal[
        "CoreObjectTemplate", "TemplateComputePhysicalServer", "TemplateDcimDevice"
    ] = Field(alias="__typename")
    id: str | None


class FabricGeneratorQueryNetworkFabricEdgesNodeMgmtGateway(BaseModel):
    value: str | None


class FabricGeneratorQueryNetworkFabricEdgesNodeAsnPool(BaseModel):
    node: FabricGeneratorQueryNetworkFabricEdgesNodeAsnPoolNode | None


class FabricGeneratorQueryNetworkFabricEdgesNodeAsnPoolNode(BaseModel):
    id: str


class FabricGeneratorQueryNetworkFabricEdgesNodeNodeIdPool(BaseModel):
    node: FabricGeneratorQueryNetworkFabricEdgesNodeNodeIdPoolNode | None


class FabricGeneratorQueryNetworkFabricEdgesNodeNodeIdPoolNode(BaseModel):
    id: str


class FabricGeneratorQueryNetworkFabricEdgesNodeMgmtPool(BaseModel):
    node: FabricGeneratorQueryNetworkFabricEdgesNodeMgmtPoolNode | None


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
