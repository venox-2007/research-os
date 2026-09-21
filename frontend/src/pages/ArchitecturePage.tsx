import React from 'react';

export const ArchitecturePage: React.FC = () => {
  const STAGES = [
    {
      num: '01',
      title: 'Question Formulation',
      component: 'FastAPI Input Route & Pydantic Validation',
      desc: 'Normalizes and structures open-ended research queries with domain disciplines and resource constraints.',
      tag: '₹0 / Local',
    },
    {
      num: '02',
      title: 'Deterministic Orchestration',
      component: 'LangGraph State Machine',
      desc: 'Plans multi-hop tasks, schedules retrieval sub-goals, and orchestrates state transitions without random chat loops.',
      tag: 'Deterministic DAG',
    },
    {
      num: '03',
      title: 'Literature Acquisition',
      component: 'arXiv API & PDF Ingestion Engine',
      desc: 'Queries free arXiv endpoints, downloads raw preprints, extracts text sections, and parses tabular structures.',
      tag: 'Free arXiv API',
    },
    {
      num: '04',
      title: 'Hybrid RAG & Indexing',
      component: 'FAISS Dense + BM25 Okapi + RRF (k=60)',
      desc: 'Merges semantic vector embeddings with keyword BM25 indices using Reciprocal Rank Fusion to maximize recall.',
      tag: 'Local In-Memory',
    },
    {
      num: '05',
      title: 'Evidence Verification',
      component: 'Grounding DAG & Provenance Audit',
      desc: 'Binds every retrieved fact to exact document, section, and page coordinates with extraction confidence scores.',
      tag: 'Traceable Audit',
    },
    {
      num: '06',
      title: 'Safe Experiment Sandbox',
      component: 'Isolated Execution Engine',
      desc: 'Executes verified benchmark routines (e.g. ranking evaluation, chunk ablation) in an isolated process with timeout guards.',
      tag: 'Local Sandbox',
    },
    {
      num: '07',
      title: 'Research Synthesis',
      component: 'Local LLM / Provider-Agnostic Engine',
      desc: 'Composes structured scientific report sections, reconciling empirical metrics and literature findings.',
      tag: 'Ollama / Mock / Free',
    },
    {
      num: '08',
      title: 'Citation Audit & Guardrails',
      component: 'Strict Deterministic Verifier',
      desc: 'Re-verifies all cited claims against ingested corpora; flags or purges ungrounded assertions to guarantee 0 hallucinations.',
      tag: 'Zero Hallucination',
    },
  ];

  const TECH_STACK = [
    { layer: 'Frontend Dashboard', tech: 'React 18 + TypeScript + Vite + Tailwind CSS', cost: '₹0.00' },
    { layer: 'Backend API Service', tech: 'FastAPI + Uvicorn + Pydantic v2', cost: '₹0.00' },
    { layer: 'Agent Orchestration', tech: 'LangGraph Stateful Workflow DAG', cost: '₹0.00' },
    { layer: 'Hybrid RAG Index', tech: 'FAISS-CPU + Rank-BM25 + RRF', cost: '₹0.00' },
    { layer: 'Academic Acquisition', tech: 'arXiv Public API + PyPDF / PDFPlumber', cost: '₹0.00' },
    { layer: 'Experiment Runtime', tech: 'Local Subprocess Sandbox with AST & Resource Limits', cost: '₹0.00' },
    { layer: 'Data & Evidence Store', tech: 'SQLite3 + In-Memory Evidence DAG', cost: '₹0.00' },
    { layer: 'Language Models', tech: 'Local Ollama (Llama 3 / Mistral) / Local Mocks', cost: '₹0.00' },
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="pb-4 border-b border-slate-800">
        <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
          <span>System Architecture & ₹0 Cost Specifications</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          End-to-end design of the ResearchOS autonomous research engineer stack.
        </p>
      </div>

      {/* Top Value Proposition Card */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
        <h2 className="text-sm font-semibold text-slate-100 mb-2">
          Autonomous AI Research Engineer Core Architecture
        </h2>
        <p className="text-xs text-slate-300 font-serif leading-relaxed max-w-4xl">
          ResearchOS is an autonomous research system engineered to plan, discover, retrieve, verify, benchmark, and synthesize scientific knowledge into publication-ready research reports with verifiable provenance. Unlike unconstrained conversational agents, ResearchOS enforces strict deterministic state progression through LangGraph and guarantees zero hallucinations through coordinate-level citation verification.
        </p>
      </div>

      {/* 8-Stage Pipeline Grid */}
      <div>
        <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold mb-4">
          Eight-Stage Deterministic Workflow
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {STAGES.map((s) => (
            <div
              key={s.num}
              className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 flex flex-col justify-between hover:border-slate-700 transition"
            >
              <div>
                <div className="flex items-center justify-between text-xs mb-2">
                  <span className="font-mono text-emerald-400 font-bold text-sm">
                    {s.num}
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                    {s.tag}
                  </span>
                </div>
                <h4 className="text-xs font-bold text-slate-100 mb-1">
                  {s.title}
                </h4>
                <div className="text-[11px] font-mono text-cyan-400 mb-2">
                  {s.component}
                </div>
                <p className="text-xs text-slate-400 font-serif leading-relaxed">
                  {s.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Stack & Cost Breakdown Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
        <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-800">
          <span className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold">
            Technology Stack & Cost Audit
          </span>
          <span className="font-mono text-xs text-emerald-400 font-bold">
            Total Operational Cost: ₹0.00 / $0.00
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 text-[11px]">
                <th className="py-2.5 px-3">System Layer</th>
                <th className="py-2.5 px-3">Selected Technology</th>
                <th className="py-2.5 px-3 text-right">Cost (INR/USD)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {TECH_STACK.map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-950/40 transition">
                  <td className="py-2.5 px-3 text-slate-200 font-semibold">{row.layer}</td>
                  <td className="py-2.5 px-3 text-slate-300">{row.tech}</td>
                  <td className="py-2.5 px-3 text-right text-emerald-400 font-bold">{row.cost}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
