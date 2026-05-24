"use client";

import { useEffect, useState } from 'react';
import { 
  ShieldAlert, 
  Store as StoreIcon, 
  Camera as CameraIcon, 
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  Check,
  CreditCard,
  AlertTriangle
} from 'lucide-react';
import { api } from '@/lib/api';
import { formatDate, cn } from '@/lib/utils';
import { TIERS, FEATURE_LABELS } from '@/lib/subscription';
import { useLicense } from '@/hooks/useLicense';

export default function DashboardPage() {
  const { license, loading } = useLicense();
  const [stats, setStats] = useState<any>(null);
  const [recentEvents, setRecentEvents] = useState<any[]>([]);

  useEffect(() => {
    // Mock data for now since backend might not be fully up
    setStats({
      total_stores: 1, // Within Pro limit (1)
      active_cameras: 4, // Within Pro limit (6)
      alerts_24h: 24,
      system_health: '99.9%'
    });

    setRecentEvents([
      { id: '1', event_type: 'shoplifting_suspected', confidence: 0.89, description: 'Suspected concealment in Aisle 4', created_at: new Date().toISOString() },
      { id: '2', event_type: 'cash_register_theft', confidence: 0.83, description: 'Unauthorized void without customer present', created_at: new Date(Date.now() - 900000).toISOString() },
      { id: '3', event_type: 'restricted_area_breach', confidence: 0.95, description: 'Unauthorized person entered back office', created_at: new Date(Date.now() - 1800000).toISOString() },
      { id: '4', event_type: 'motion_anomaly', confidence: 0.75, description: 'Movement detected in staff area', created_at: new Date(Date.now() - 3600000).toISOString() },
    ]);
  }, []);

  if (loading) return <div className="animate-pulse space-y-8">
    <div className="grid grid-cols-4 gap-6"><div className="h-32 bg-slate-900 rounded-xl"/><div className="h-32 bg-slate-900 rounded-xl"/><div className="h-32 bg-slate-900 rounded-xl"/><div className="h-32 bg-slate-900 rounded-xl"/></div>
    <div className="grid grid-cols-3 gap-8"><div className="col-span-2 h-96 bg-slate-900 rounded-xl"/><div className="h-96 bg-slate-900 rounded-xl"/></div>
  </div>;

  const tierInfo = license ? TIERS[license.tier] : TIERS['solo'];

  return (
    <div className="space-y-8">
      {license?.status === 'grace' && (
        <div className="bg-blue-500/10 border border-blue-500/20 p-4 rounded-xl flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Activity className="h-5 w-5 text-blue-500" />
            <p className="text-sm text-blue-200">{license.message}</p>
          </div>
          <button className="text-xs font-bold uppercase tracking-wider bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg transition-colors">
            Activate License
          </button>
        </div>
      )}

      {license?.status === 'disabled' && (
        <div className="bg-red-500/10 border border-red-500/20 p-4 rounded-xl flex items-center space-x-3">
          <AlertTriangle className="h-5 w-5 text-red-500" />
          <p className="text-sm text-red-200">{license.message}</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Stores" 
          value={stats?.total_stores} 
          icon={StoreIcon} 
          trend={`${stats?.total_stores}/${license?.max_stores}`}
          trendUp={stats?.total_stores < license?.max_stores!} 
        />
        <StatCard 
          title="Cameras" 
          value={stats?.active_cameras} 
          icon={CameraIcon} 
          trend={`${stats?.active_cameras}/${license?.max_cameras}`}
          trendUp={stats?.active_cameras < license?.max_cameras!} 
        />
        <StatCard 
          title="Alerts (24h)" 
          value={stats?.alerts_24h} 
          icon={ShieldAlert} 
          trend="-5%" 
          trendUp={false} 
        />
        <StatCard 
          title="System Health" 
          value={stats?.system_health} 
          icon={Activity} 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
            <div className="p-6 border-b border-slate-800 flex justify-between items-center">
              <h3 className="font-semibold text-lg">Recent Alerts</h3>
              <button className="text-sm text-blue-500 hover:underline">View all</button>
            </div>
            <div className="divide-y divide-slate-800">
              {recentEvents.map((event) => (
                <div key={event.id} className="p-6 flex items-start space-x-4 hover:bg-slate-800/50 transition-colors">
                  <div className={cn(
                    "p-2 rounded-lg",
                    event.event_type === 'shoplifting_suspected' ? "bg-red-500/10 text-red-500" :
                    event.event_type === 'restricted_area_breach' ? "bg-orange-500/10 text-orange-500" :
                    event.event_type === 'cash_register_theft' ? "bg-purple-500/10 text-purple-500" :
                    "bg-amber-500/10 text-amber-500"
                  )}>
                    <ShieldAlert className="h-6 w-6" />
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between items-start">
                      <h4 className="font-medium">{event.event_type.replace('_', ' ').toUpperCase()}</h4>
                      <span className="text-xs text-slate-500">{formatDate(event.created_at)}</span>
                    </div>
                    <p className="text-sm text-slate-400 mt-1">{event.description}</p>
                    <div className="mt-2 flex items-center space-x-2">
                      <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                        Confidence: {(event.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  <button className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-xs font-medium rounded transition-colors">
                    Review
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-8">
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-semibold text-lg">Subscription</h3>
              <CreditCard className="h-5 w-5 text-slate-400" />
            </div>
            <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700 mb-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-300">Current Plan</span>
                <span className={cn(
                  "px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider text-white",
                  tierInfo.color
                )}>
                  {license?.tier_name}
                </span>
              </div>
              <p className="text-2xl font-bold">${license?.price}<span className="text-sm font-normal text-slate-500">/mo</span></p>
            </div>
            
            <div className="space-y-3">
              <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Features</h4>
              <ul className="space-y-2">
                {tierInfo.features.map((f, i) => (
                  <li key={i} className="flex items-start text-sm">
                    <Check className="h-4 w-4 text-green-500 mr-2 mt-0.5 shrink-0" />
                    <span className="text-slate-300">{FEATURE_LABELS[f] || f}</span>
                  </li>
                ))}
              </ul>
            </div>
            
            <button className="w-full mt-8 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-sm font-medium transition-colors">
              Manage Subscription
            </button>
          </div>

          <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
            <h3 className="font-semibold text-lg mb-6">Live Feed Summary</h3>
            <div className="space-y-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-slate-700 rounded overflow-hidden relative">
                      <div className="absolute inset-0 bg-gradient-to-tr from-blue-500/20 to-transparent" />
                    </div>
                    <div>
                      <p className="text-sm font-medium">Camera {i}</p>
                      <p className="text-xs text-slate-500">Main Entrance</p>
                    </div>
                  </div>
                  <span className="flex items-center text-xs text-green-500">
                    <span className="w-1.5 h-1.5 bg-green-500 rounded-full mr-2" />
                    Online
                  </span>
                </div>
              ))}
            </div>
            <button className="w-full mt-6 py-2 border border-slate-700 rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors">
              Manage All Cameras
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon: Icon, trend, trendUp }: any) {
  return (
    <div className="bg-slate-900 p-6 rounded-xl border border-slate-800">
      <div className="flex justify-between items-start">
        <div className="p-2 bg-slate-800 rounded-lg">
          <Icon className="h-6 w-6 text-blue-500" />
        </div>
        {trend && (
          <div className={cn(
            "flex items-center text-xs font-medium",
            trendUp === true ? "text-green-500" : trendUp === false ? "text-red-500" : "text-blue-500"
          )}>
            {trend}
            {trendUp === true && <ArrowUpRight className="ml-1 h-3 w-3" />}
            {trendUp === false && <ArrowDownRight className="ml-1 h-3 w-3" />}
          </div>
        )}
      </div>
      <div className="mt-4">
        <p className="text-sm text-slate-500 font-medium">{title}</p>
        <p className="text-2xl font-bold mt-1">{value}</p>
      </div>
    </div>
  );
}
