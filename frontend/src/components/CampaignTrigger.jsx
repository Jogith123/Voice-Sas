import { useState } from 'react'
import { Rocket, Loader2, CheckCircle2, AlertCircle } from 'lucide-react'
import { triggerCampaign } from '../api/client'

export default function CampaignTrigger({ company, pendingCount, onCampaignStarted }) {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  async function handleTrigger() {
    if (!company) return
    setLoading(true)
    setResult(null)
    setError(null)

    try {
      const data = await triggerCampaign(company.id)
      setResult(data)
      onCampaignStarted?.()
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to trigger campaign')
    } finally {
      setLoading(false)
    }
  }

  const disabled = !company || loading || pendingCount === 0

  return (
    <div className="glass p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-slate-200 text-sm">Outbound Campaign</h3>
          <p className="text-xs text-slate-500 mt-0.5">
            {pendingCount > 0
              ? `${pendingCount} pending lead${pendingCount !== 1 ? 's' : ''} ready to call`
              : 'No pending leads'}
          </p>
        </div>

        <button
          id="trigger-campaign-btn"
          onClick={handleTrigger}
          disabled={disabled}
          className="btn-primary"
        >
          {loading ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              Dispatching...
            </>
          ) : (
            <>
              <Rocket size={16} />
              Launch Campaign
            </>
          )}
        </button>
      </div>

      {result && (
        <div className="flex items-start gap-2 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 animate-slide-up">
          <CheckCircle2 size={14} className="text-emerald-400 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-emerald-300">{result.message}</p>
            {result.pending_leads && (
              <p className="text-xs text-emerald-500 mt-0.5">
                Dispatching calls to {result.pending_leads} lead{result.pending_leads !== 1 ? 's' : ''}
              </p>
            )}
          </div>
        </div>
      )}

      {error && (
        <div className="flex items-start gap-2 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 animate-slide-up">
          <AlertCircle size={14} className="text-rose-400 mt-0.5 flex-shrink-0" />
          <p className="text-sm text-rose-300">{error}</p>
        </div>
      )}

      {pendingCount === 0 && !loading && (
        <p className="text-xs text-slate-600 text-center">
          All leads have been contacted. Reset individual leads to re-campaign.
        </p>
      )}
    </div>
  )
}
