"use client";

import { Background, Controls, MarkerType, MiniMap, Position, ReactFlow, type Edge, type Node } from "@xyflow/react";
import { useMemo } from "react";
import type { Business, ResearchReport } from "@/lib/api";

const nodeStyle = {
  border: "1px solid rgba(255,255,255,0.78)",
  borderRadius: 22,
  background: "rgba(255,255,255,0.84)",
  boxShadow: "0 18px 45px rgba(15,23,42,0.09)",
  color: "#172033",
  fontSize: 12,
  padding: 0,
  width: 190,
};

function short(value: unknown, fallback = "Unknown") {
  const text = value == null || value === "" ? fallback : String(value);
  return text.length > 54 ? `${text.slice(0, 51)}...` : text;
}

function node(id: string, label: string, type: string, x: number, y: number): Node {
  return {
    id,
    type: "default",
    position: { x, y },
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
    data: {
      label: (
        <div className="rounded-[22px] px-4 py-3">
          <span className="block text-[10px] font-semibold uppercase tracking-[0.16em] text-muted">{type}</span>
          <strong className="mt-1 block text-sm leading-5 text-ink">{label}</strong>
        </div>
      ),
    },
    style: nodeStyle,
  };
}

function edge(id: string, from: string, to: string, label: string): Edge {
  return {
    id,
    source: from,
    target: to,
    label,
    type: "smoothstep",
    markerEnd: { type: MarkerType.ArrowClosed, color: "#3730a3" },
    style: { stroke: "#3730a3", strokeOpacity: 0.45, strokeWidth: 1.8 },
    labelStyle: { fill: "#64748b", fontSize: 10, fontWeight: 600 },
    labelBgStyle: { fill: "rgba(242,248,252,0.82)" },
  };
}

function firstArray(value: unknown): Array<Record<string, unknown>> {
  return Array.isArray(value) ? value.filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object") : [];
}

export function IntelligenceGraph({ business, report }: { business?: Business; report?: ResearchReport }) {
  const { nodes, edges } = useMemo(() => {
    if (!business) return { nodes: [], edges: [] };

    const graphNodes: Node[] = [];
    const graphEdges: Edge[] = [];
    const businessId = `business-${business.id}`;
    graphNodes.push(node(businessId, short(business.name, "Selected business"), "Business", 0, 180));

    const evidence = firstArray(business.evidence).slice(0, 6);
    evidence.forEach((item, index) => {
      const field = short(item.field || item.name || `Field ${index + 1}`);
      const value = short(item.value || item.evidence_value || "Value pending");
      const source = short(item.source || item.source_type || "Source");
      const fieldId = `field-${index}`;
      const sourceId = `source-${index}`;
      graphNodes.push(node(fieldId, `${field}: ${value}`, "Evidence", 290, 44 + index * 86));
      graphNodes.push(node(sourceId, source, "Source", 590, 44 + index * 86));
      graphEdges.push(edge(`has-field-${index}`, businessId, fieldId, "VERIFIED_FIELD"));
      graphEdges.push(edge(`verified-by-${index}`, fieldId, sourceId, "VERIFIED_BY"));
    });

    firstArray(business.conflicts).slice(0, 3).forEach((item, index) => {
      const conflictId = `conflict-${index}`;
      graphNodes.push(node(conflictId, `${short(item.field || "Conflict")}: ${short(item.value1)} / ${short(item.value2)}`, "Conflict", 290, 610 + index * 86));
      graphEdges.push(edge(`conflicts-${index}`, businessId, conflictId, "CONFLICTS_WITH"));
    });

    (business.analyst_quality_flags || []).slice(0, 4).forEach((flag, index) => {
      const flagId = `flag-${index}`;
      graphNodes.push(node(flagId, flag.replaceAll("_", " "), "Quality flag", 590, 610 + index * 86));
      graphEdges.push(edge(`flagged-${index}`, businessId, flagId, "HAS_FLAG"));
    });

    const pairs = firstArray(report?.similar_pairs).slice(0, 3);
    pairs.forEach((pair, index) => {
      const similarId = `similar-${index}`;
      const label = short(pair.business_2 || pair.business_name || pair.name || pair.pair || "Similar business");
      graphNodes.push(node(similarId, label, "Relationship", 890, 130 + index * 120));
      graphEdges.push(edge(`similar-${index}`, businessId, similarId, "SIMILAR_TO"));
    });

    const cluster = business.market_cluster || business.market_position;
    if (cluster) {
      graphNodes.push(node("cluster", short(cluster), "Cluster", 890, 500));
      graphEdges.push(edge("cluster-edge", businessId, "cluster", "IN_CLUSTER"));
    }

    return { nodes: graphNodes, edges: graphEdges };
  }, [business, report]);

  return (
    <section className="premium-panel rounded-[32px] p-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Evidence graph</p>
          <h2 className="font-display text-3xl font-semibold tracking-tight text-ink">Relationship Workspace</h2>
        </div>
        <span className="premium-chip rounded-full px-3 py-1 text-xs font-semibold">{nodes.length} nodes / {edges.length} edges</span>
      </div>
      <div className="mt-5 h-[520px] overflow-hidden rounded-[28px] border border-white/70 bg-white/45">
        {business ? (
          <ReactFlow nodes={nodes} edges={edges} fitView minZoom={0.45} maxZoom={1.35} defaultViewport={{ x: 30, y: 20, zoom: 0.72 }}>
            <Background color="#cbd5e1" gap={28} size={1} />
            <MiniMap pannable zoomable nodeColor={() => "#3730a3"} maskColor="rgba(242,248,252,0.72)" />
            <Controls showInteractive={false} />
          </ReactFlow>
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-muted">Run research to render the evidence and relationship graph.</div>
        )}
      </div>
    </section>
  );
}
