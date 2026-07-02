import { useState } from 'react'
import { Phone, Mail, ChevronRight, RotateCcw, Loader2, AlertTriangle, Search, UserPlus } from 'lucide-react'
import LeadStatusBadge from './LeadStatusBadge'
import CallLogModal from './CallLogModal'

function formatDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  const now = new Date()
  const diff = now - d
  if (diff < 60000) return 'just now'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

export default function LeadDirectory({ leads, company, loading, error, onRefresh }) {
  const [selectedLead, setSelectedLead] = useState(null)
  const [search, setSearch] = useState('')

  const filtered = leads.filter(l =>
    l.name.toLowerCase().includes(search.toLowerCase()) ||
    l.phone.includes(search) ||
    (l.email || '').toLowerCase().includes(search.toLowerCase())
  )

  const needsReview = filtered.filter(l => l.status === 'NEEDS_REVIEW')

  return (
    <div className="glass flex flex-col" style={{ minHeight: 0 }}>
      <div className="p-5 border-b border-white/[0.06]">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="font-semibold text-slate-100">Lead Directory</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              {leads.length} lead{leads.length !== 1 ? 's' : ''}
              {company ? ` · ${company.name}` : ''}
            </p>
          </div>
          <button
            id="refresh-leads-btn"
            onClick={onRefresh}
            disabled={loading}
            className="btn-secondary text-xs"
          >
            {loading ? <Loader2 size={13} className="animate-spin" /> : <RotateCcw size={13} />}
            Refresh
          </button>
        </div>

        {needsReview.length > 0 && (
          <div className="flex items-center gap-2 px-3 py-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 mb-3">
            <AlertTriangle size={13} className="text-amber-400 flex-shrink-0" />
            <p className="text-xs text-amber-300">
              <span className="font-semibold">{needsReview.length} lead{needsReview.length > 1 ? 's' : ''}</span> need human review — AI confidence was low
            </p>
          </div>
        )}

        <div className="relative">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            id="lead-search-input"
            type="text"
            placeholder="Search by name, phone, or email..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="input pl-8 text-xs"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto custom-scroll">
        {loading && leads.length === 0 ? (
          <div className="flex items-center justify-center py-16 text-slate-500">
            <Loader2 size={20} className="animate-spin mr-2" />
            <span className="text-sm">Loading leads...</span>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center py-16 text-rose-400">
            <AlertTriangle size={16} className="mr-2" />
            <span className="text-sm">{error}</span>
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-slate-500">
            <UserPlus size={32} className="mb-3 opacity-40" />
            <p className="text-sm font-medium">No leads found</p>
            <p className="text-xs mt-1 opacity-60">
              {search ? 'Try a different search term' : 'Add leads to get started'}
            </p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-surface-900/90 backdrop-blur-sm">
              <tr className="border-b border-white/[0.04]">
                <th className="text-left text-xs text-slate-500 font-medium px-5 py-3">Lead</th>
                <th className="text-left text-xs text-slate-500 font-medium px-3 py-3 hidden sm:table-cell">Phone</th>
                <th className="text-left text-xs text-slate-500 font-medium px-3 py-3">Status</th>
                <th className="text-left text-xs text-slate-500 font-medium px-3 py-3 hidden md:table-cell">Updated</th>
                <th className="px-3 py-3 w-8" />
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.03]">
              {filtered.map((lead) => (
                <tr
                  key={lead.id}
                  id={`lead-row-${lead.id}`}
                  onClick={() => setSelectedLead(lead)}
                  className={`
                    group cursor-pointer hover:bg-white/[0.03] transition-colors
                    ${lead.status === 'NEEDS_REVIEW' ? 'bg-amber-500/[0.03]' : ''}
                  `}
                >
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-600/40 to-purple-600/40 border border-white/10 flex items-center justify-center text-xs font-semibold text-slate-300 flex-shrink-0">
                        {lead.name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <p className="font-medium text-slate-200 text-sm leading-tight">{lead.name}</p>
                        {lead.email && (
                          <p className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
                            <Mail size={10} />
                            {lead.email}
                          </p>
                        )}
                      </div>
                    </div>
                  </td>

                  <td className="px-3 py-3.5 hidden sm:table-cell">
                    <p className="text-slate-400 text-xs font-mono">{lead.phone}</p>
                  </td>

                  <td className="px-3 py-3.5">
                    <LeadStatusBadge status={lead.status} />
                  </td>

                  <td className="px-3 py-3.5 hidden md:table-cell">
                    <p className="text-xs text-slate-600">{formatDate(lead.updated_at)}</p>
                  </td>

                  <td className="px-3 py-3.5">
                    <ChevronRight
                      size={14}
                      className="text-slate-600 group-hover:text-slate-400 transition-colors"
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {selectedLead && (
        <CallLogModal
          lead={selectedLead}
          company={company}
          onClose={() => setSelectedLead(null)}
          onReset={onRefresh}
        />
      )}
    </div>
  )
}
