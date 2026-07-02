import { useState } from 'react'
import { X, Phone, MessageSquare, Brain, RotateCcw, Loader2, Clock, ChevronRight } from 'lucide-react'
import LeadStatusBadge from './LeadStatusBadge'
import { getLeadCallLog, resetLead, testWebhook } from '../api/client'

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  })
}

export default function CallLogModal({ lead, company, onClose, onReset }) {
  const [callLog, setCallLog] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [testLoading, setTestLoading] = useState(false)
  const [resetLoading, setResetLoading] = useState(false)

  async function loadCallLog() {
    setLoading(true)
    setError(null)
    try {
      const log = await getLeadCallLog(lead.id)
      setCallLog(log)
    } catch (e) {
      setError(e.response?.status === 404 ? 'No call log yet for this lead.' : 'Failed to load call log.')
    } finally {
      setLoading(false)
    }
  }

  async function handleTestWebhook() {
    setTestLoading(true)
    try {
      await testWebhook(lead.id, company.id)
      
      setTimeout(() => {
        onReset?.()
        onClose()
      }, 3000)
    } catch {
      alert('Test webhook failed')
    } finally {
      setTestLoading(false)
    }
  }

  async function handleReset() {
    setResetLoading(true)
    try {
      await resetLead(lead.id)
      onReset?.()
      onClose()
    } catch {
      alert('Reset failed')
    } finally {
      setResetLoading(false)
    }
  }

  return (
    <div className="modal-backdrop fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="modal-content glass w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="flex items-start justify-between p-6 border-b border-white/[0.06]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm">
              {lead.name.charAt(0).toUpperCase()}
            </div>
            <div>
              <h2 className="font-semibold text-slate-100">{lead.name}</h2>
              <p className="text-sm text-slate-500">{lead.phone}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <LeadStatusBadge status={lead.status} />
            <button id="modal-close-btn" onClick={onClose} className="btn-secondary p-2 rounded-lg">
              <X size={14} />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto custom-scroll p-6 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="glass p-3 rounded-xl">
              <p className="text-xs text-slate-500 mb-1">Email</p>
              <p className="text-sm text-slate-300">{lead.email || '—'}</p>
            </div>
            <div className="glass p-3 rounded-xl">
              <p className="text-xs text-slate-500 mb-1">Call ID</p>
              <p className="text-sm text-slate-300 font-mono truncate">{lead.call_id || '—'}</p>
            </div>
            <div className="glass p-3 rounded-xl col-span-2">
              <p className="text-xs text-slate-500 mb-1">Notes</p>
              <p className="text-sm text-slate-300">{lead.notes || '—'}</p>
            </div>
          </div>

          <div className="flex gap-2 flex-wrap">
            <button
              id="load-call-log-btn"
              onClick={loadCallLog}
              disabled={loading}
              className="btn-secondary text-xs"
            >
              {loading ? <Loader2 size={13} className="animate-spin" /> : <MessageSquare size={13} />}
              View Call Log
            </button>

            <button
              id="test-webhook-btn"
              onClick={handleTestWebhook}
              disabled={testLoading}
              className="btn-secondary text-xs"
              title="Simulate a completed Vapi call with a qualified transcript"
            >
              {testLoading ? <Loader2 size={13} className="animate-spin" /> : <Phone size={13} />}
              Simulate Call
            </button>

            <button
              id="reset-lead-btn"
              onClick={handleReset}
              disabled={resetLoading}
              className="btn-danger text-xs"
            >
              {resetLoading ? <Loader2 size={13} className="animate-spin" /> : <RotateCcw size={13} />}
              Reset to Pending
            </button>
          </div>

          {error && (
            <div className="glass p-4 rounded-xl border-amber-500/20 bg-amber-500/5">
              <p className="text-sm text-amber-400">{error}</p>
            </div>
          )}

          {callLog && (
            <div className="space-y-3 animate-slide-up">
              <div className="glass p-4 rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 text-sm font-medium text-slate-300">
                    <Brain size={14} className="text-brand-400" />
                    LLM Analysis
                  </div>
                  <div className="flex items-center gap-2">
                    <LeadStatusBadge status={callLog.outcome} />
                    {callLog.confidence != null && (
                      <span className="text-xs text-slate-500">
                        {Math.round(callLog.confidence * 100)}% confidence
                      </span>
                    )}
                  </div>
                </div>
                {callLog.llm_reasoning && (
                  <p className="text-sm text-slate-400 mt-2 leading-relaxed">{callLog.llm_reasoning}</p>
                )}
              </div>

              {callLog.summary && (
                <div className="glass p-4 rounded-xl">
                  <p className="text-xs text-slate-500 mb-2 font-medium uppercase tracking-wide">Summary</p>
                  <p className="text-sm text-slate-300 leading-relaxed">{callLog.summary}</p>
                </div>
              )}

              {callLog.transcript && (
                <div className="glass p-4 rounded-xl">
                  <p className="text-xs text-slate-500 mb-3 font-medium uppercase tracking-wide">Transcript</p>
                  <pre className="text-xs text-slate-400 whitespace-pre-wrap leading-relaxed font-mono overflow-auto max-h-60 custom-scroll">
                    {callLog.transcript}
                  </pre>
                </div>
              )}

              <div className="flex items-center gap-2 text-xs text-slate-600">
                <Clock size={11} />
                <span>Call logged at {formatDate(callLog.created_at)}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
