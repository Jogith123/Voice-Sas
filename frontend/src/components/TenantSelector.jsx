import { Building2, ChevronDown, CheckCircle2 } from 'lucide-react'
import { useState } from 'react'

const COMPANY_COLORS = {
  '#f59e0b': 'from-amber-500 to-orange-500',
  '#3b82f6': 'from-blue-500 to-cyan-500',
  '#6366f1': 'from-indigo-500 to-purple-500',
  '#10b981': 'from-emerald-500 to-teal-500',
}

function getGradient(color) {
  return COMPANY_COLORS[color] || 'from-brand-500 to-purple-500'
}

export default function TenantSelector({ tenants, selected, onSelect }) {
  const [open, setOpen] = useState(false)

  if (!tenants || tenants.length === 0) {
    return (
      <div className="glass px-4 py-3 flex items-center gap-3 text-slate-400 text-sm">
        <Building2 size={16} />
        <span>No companies found</span>
      </div>
    )
  }

  return (
    <div className="relative">
      <button
        id="tenant-selector-btn"
        onClick={() => setOpen(!open)}
        className="glass-hover px-4 py-3 flex items-center gap-3 min-w-[220px] text-left"
      >
        {selected ? (
          <>
            <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${getGradient(selected.primary_color)} flex items-center justify-center flex-shrink-0`}>
              <Building2 size={14} className="text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-slate-100 truncate">{selected.name}</p>
              <p className="text-xs text-slate-500 truncate">{selected.slug}</p>
            </div>
          </>
        ) : (
          <>
            <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center flex-shrink-0">
              <Building2 size={14} className="text-slate-400" />
            </div>
            <span className="text-sm text-slate-400 flex-1">Select Company</span>
          </>
        )}
        <ChevronDown
          size={14}
          className={`text-slate-400 transition-transform duration-200 flex-shrink-0 ${open ? 'rotate-180' : ''}`}
        />
      </button>

      {open && (
        <div className="absolute top-full left-0 mt-2 w-full min-w-[280px] z-50 glass animate-slide-up overflow-hidden">
          <div className="p-1">
            {tenants.map((tenant) => (
              <button
                key={tenant.id}
                id={`tenant-option-${tenant.id}`}
                onClick={() => { onSelect(tenant); setOpen(false) }}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-white/[0.06] transition-colors text-left group"
              >
                <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${getGradient(tenant.primary_color)} flex items-center justify-center flex-shrink-0`}>
                  <Building2 size={14} className="text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-200 truncate">{tenant.name}</p>
                  <p className="text-xs text-slate-500 truncate">{tenant.slug}</p>
                </div>
                {selected?.id === tenant.id && (
                  <CheckCircle2 size={14} className="text-brand-400 flex-shrink-0" />
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {open && <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />}
    </div>
  )
}
