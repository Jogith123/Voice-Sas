import { useState, useEffect, useCallback, useRef } from 'react'
import {
  Phone, Users, CheckCircle2, XCircle, AlertTriangle,
  Clock, HelpCircle, Radio, Building2, RefreshCw, Wifi, WifiOff
} from 'lucide-react'
import TenantSelector from './components/TenantSelector'
import StatsCard from './components/StatsCard'
import LeadDirectory from './components/LeadDirectory'
import CampaignTrigger from './components/CampaignTrigger'
import { getTenants, getLeads, getCampaignStats } from './api/client'

const POLL_INTERVAL = 5000

export default function App() {
  const [tenants, setTenants] = useState([])
  const [selectedTenant, setSelectedTenant] = useState(null)
  const [leads, setLeads] = useState([])
  const [stats, setStats] = useState(null)
  const [leadsLoading, setLeadsLoading] = useState(false)
  const [leadsError, setLeadsError] = useState(null)
  const [polling, setPolling] = useState(false)
  const [connected, setConnected] = useState(true)
  const pollRef = useRef(null)

  useEffect(() => {
    getTenants()
      .then(data => {
        setTenants(data)
        if (data.length > 0) setSelectedTenant(data[0])
      })
      .catch(() => setConnected(false))
  }, [])

  const loadLeads = useCallback(async (tenantId) => {
    if (!tenantId) return
    setLeadsLoading(true)
    setLeadsError(null)
    try {
      const [leadsData, statsData] = await Promise.all([
        getLeads(tenantId),
        getCampaignStats(tenantId),
      ])
      setLeads(leadsData)
      setStats(statsData)
      setConnected(true)
    } catch (e) {
      setLeadsError('Failed to load leads. Check your connection.')
      setConnected(false)
    } finally {
      setLeadsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (selectedTenant) {
      loadLeads(selectedTenant.id)
    }
  }, [selectedTenant, loadLeads])

  useEffect(() => {
    const hasActiveCalls = leads.some(l =>
      l.status === 'CALL_INITIATED' || l.status === 'PENDING'
    ) && polling

    if (hasActiveCalls && selectedTenant) {
      const interval = setInterval(() => {
        loadLeads(selectedTenant.id)
      }, POLL_INTERVAL)
      pollRef.current = interval
      return () => clearInterval(interval)
    } else {
      clearInterval(pollRef.current)
    }
  }, [leads, polling, selectedTenant, loadLeads])

  function handleCampaignStarted() {
    setPolling(true)
    setTimeout(() => loadLeads(selectedTenant?.id), 2000)
  }

  const pendingCount = stats?.PENDING ?? leads.filter(l => l.status === 'PENDING').length

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-white/[0.06] bg-surface-950/80 backdrop-blur-xl sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-600 to-purple-600 flex items-center justify-center glow-brand">
              <Phone size={16} className="text-white" />
            </div>
            <div>
              <h1 className="font-bold text-slate-100 leading-tight">
                Voice<span className="text-gradient">AI</span>
              </h1>
              <p className="text-[10px] text-slate-500 leading-tight">Multi-Tenant Orchestrator</p>
            </div>
          </div>

          <div className="flex-1 max-w-xs">
            <TenantSelector
              tenants={tenants}
              selected={selectedTenant}
              onSelect={(t) => { setSelectedTenant(t); setPolling(false) }}
            />
          </div>

          <div className="flex items-center gap-3">
            {polling && (
              <div className="flex items-center gap-1.5 text-xs text-blue-400 glass px-3 py-1.5 rounded-full animate-fade-in">
                <Radio size={11} className="animate-pulse" />
                <span className="hidden sm:inline">Live</span>
              </div>
            )}
            <div className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full glass ${connected ? 'text-emerald-400' : 'text-rose-400'}`}>
              {connected ? <Wifi size={11} /> : <WifiOff size={11} />}
              <span className="hidden sm:inline">{connected ? 'Connected' : 'Offline'}</span>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 py-6 space-y-6">

        {!selectedTenant && (
          <div className="glass p-12 flex flex-col items-center justify-center text-center animate-fade-in">
            <div className="w-16 h-16 rounded-2xl bg-brand-500/10 flex items-center justify-center mb-4">
              <Building2 size={28} className="text-brand-400" />
            </div>
            <h2 className="text-xl font-semibold text-slate-200 mb-2">Select a Company</h2>
            <p className="text-sm text-slate-500 max-w-sm">
              Choose a tenant from the dropdown above to view their leads and manage campaigns.
            </p>
          </div>
        )}

        {selectedTenant && (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              <StatsCard label="Total Leads" value={stats?.total} icon={Users} color="slate" />
              <StatsCard label="Pending" value={stats?.PENDING} icon={Clock} color="slate" />
              <StatsCard label="Calling" value={stats?.CALL_INITIATED} icon={Phone} color="blue" />
              <StatsCard label="Qualified" value={stats?.QUALIFIED} icon={CheckCircle2} color="emerald" />
              <StatsCard label="Not Interested" value={stats?.NOT_INTERESTED} icon={XCircle} color="rose" />
              <StatsCard label="Needs Review" value={stats?.NEEDS_REVIEW} icon={HelpCircle} color="amber" />
            </div>

            <CampaignTrigger
              company={selectedTenant}
              pendingCount={pendingCount}
              onCampaignStarted={handleCampaignStarted}
            />

            <LeadDirectory
              leads={leads}
              company={selectedTenant}
              loading={leadsLoading}
              error={leadsError}
              onRefresh={() => loadLeads(selectedTenant.id)}
            />
          </>
        )}
      </main>

      <footer className="border-t border-white/[0.04] py-4 text-center">
        <p className="text-xs text-slate-700">
          VoiceAI Orchestrator · Powered by LangGraph + Vapi AI + MongoDB
        </p>
      </footer>
    </div>
  )
}
