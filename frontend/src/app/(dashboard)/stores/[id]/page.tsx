"use client";

import { useEffect, useState, use } from 'react';
import { 
  Camera, 
  Settings, 
  ShieldAlert, 
  ChevronLeft,
  Maximize2,
  RefreshCw,
  Play,
  Plus,
  AlertCircle,
  ArrowUpCircle
} from 'lucide-react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { formatDate, cn } from '@/lib/utils';
import { useLicense } from '@/hooks/useLicense';

export default function StoreDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { license } = useLicense();
  const [store, setStore] = useState<any>(null);
  const [cameras, setCameras] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);

  useEffect(() => {
    // Mock data
    setStore({ id, name: 'QuickMart #42', address: '123 Main St, Austin TX' });
    setCameras([
      { id: 'c1', name: 'Entrance', status: 'online', last_seen: new Date().toISOString() },
      { id: 'c2', name: 'Aisle 3 (Beverages)', status: 'online', last_seen: new Date().toISOString() },
      { id: 'c3', name: 'Checkout', status: 'online', last_seen: new Date().toISOString() },
      { id: 'c4', name: 'Back Door', status: 'offline', last_seen: new Date(Date.now() - 3600000).toISOString() },
    ]);
    setEvents([
      { id: '1', type: 'shoplifting_suspected', confidence: 0.89, description: 'Suspected concealment in Aisle 4', created_at: new Date().toISOString() },
      { id: '2', type: 'cash_register_theft', confidence: 0.83, description: 'Unauthorized void without customer present', created_at: new Date(Date.now() - 900000).toISOString() },
      { id: '3', type: 'restricted_area_breach', confidence: 0.95, description: 'Unauthorized person entered back office', created_at: new Date(Date.now() - 1800000).toISOString() },
      { id: '4', type: 'motion_anomaly', confidence: 0.75, description: 'Movement detected in staff area', created_at: new Date(Date.now() - 3600000).toISOString() },
    ]);
  }, [id]);

  const atLimit = license ? cameras.length >= license.max_cameras : false;

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <Link href="/stores" className="p-2 hover:bg-slate-800 rounded-lg transition-colors">
            <ChevronLeft className="h-6 w-6" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold">{store?.name}</h1>
            <p className="text-slate-400 text-sm">{store?.address}</p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
           <div className="text-right hidden md:block">
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Camera Usage</p>
              <p className="text-sm font-semibold">{cameras.length} / {license?.max_cameras || 0}</p>
           </div>
           <button 
             disabled={atLimit}
             className={cn(
               "flex items-center px-4 py-2 rounded-lg transition-colors text-sm font-bold",
               atLimit 
                 ? "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700" 
                 : "bg-blue-600 hover:bg-blue-700 text-white"
             )}
           >
             <Plus className="h-4 w-4 mr-2" />
             Add Camera
           </button>
        </div>
      </div>

      {atLimit && (
        <div className="bg-amber-500/10 border border-amber-500/20 p-4 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <AlertCircle className="h-5 w-5 text-amber-500" />
            <div>
              <p className="text-sm font-semibold text-amber-200">Camera Limit Reached</p>
              <p className="text-xs text-amber-400/80">You have used all {license?.max_cameras} cameras allowed in the {license?.tier_name} plan for this location.</p>
            </div>
          </div>
          <Link 
            href="/settings/license"
            className="flex items-center px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-bold transition-colors whitespace-nowrap"
          >
            <ArrowUpCircle className="h-4 w-4 mr-2" />
            Upgrade Plan
          </Link>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {cameras.map((camera) => (
              <div key={camera.id} className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden group">
                <div className="aspect-video bg-slate-800 relative flex items-center justify-center">
                  {camera.status === 'online' ? (
                    <div className="absolute inset-0 bg-slate-950 flex items-center justify-center">
                       {/* Mock video feed */}
                       <div className="text-slate-700 font-mono text-xs">RTSP STREAM: {camera.name}</div>
                       <div className="absolute top-3 left-3 flex items-center space-x-2">
                         <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                         <span className="text-[10px] font-bold text-white uppercase tracking-wider bg-black/40 px-1.5 py-0.5 rounded">Live</span>
                       </div>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center space-y-2 text-slate-500">
                      <Camera className="h-8 w-8" />
                      <span className="text-sm font-medium">Camera Offline</span>
                    </div>
                  )}
                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center space-x-4">
                    <button className="p-2 bg-white/10 hover:bg-white/20 rounded-full backdrop-blur-sm transition-colors">
                      <Maximize2 className="h-5 w-5 text-white" />
                    </button>
                    <button className="p-2 bg-white/10 hover:bg-white/20 rounded-full backdrop-blur-sm transition-colors">
                      <RefreshCw className="h-5 w-5 text-white" />
                    </button>
                  </div>
                </div>
                <div className="p-4 flex justify-between items-center bg-slate-900">
                  <div>
                    <h3 className="font-medium text-sm">{camera.name}</h3>
                    <p className="text-xs text-slate-500">
                      {camera.status === 'online' ? 'Online' : `Offline since ${formatDate(camera.last_seen)}`}
                    </p>
                  </div>
                  <button className="p-2 hover:bg-slate-800 rounded-lg transition-colors">
                    <Settings className="h-4 w-4 text-slate-400" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
            <div className="p-4 border-b border-slate-800 flex justify-between items-center">
              <h3 className="font-semibold">Store Alerts</h3>
              <ShieldAlert className="h-5 w-5 text-red-500" />
            </div>
            <div className="divide-y divide-slate-800">
              {events.map((event) => (
                <div key={event.id} className="p-4 hover:bg-slate-800/50 transition-colors">
                  <div className="flex justify-between items-start mb-2">
                    <span className={cn(
                      "text-[10px] font-bold uppercase px-1.5 py-0.5 rounded",
                      event.type === 'shoplifting_suspected' ? 'bg-red-500/10 text-red-500' :
                      event.type === 'restricted_area_breach' ? 'bg-orange-500/10 text-orange-500' :
                      event.type === 'cash_register_theft' ? 'bg-purple-500/10 text-purple-500' :
                      'bg-amber-500/10 text-amber-500'
                    )}>
                      {event.type.replace('_', ' ')}
                    </span>
                    <span className="text-[10px] text-slate-500">{formatDate(event.created_at)}</span>
                  </div>
                  <p className="text-xs text-slate-300 line-clamp-2 mb-3">{event.description}</p>
                  <button className="w-full py-1.5 bg-slate-800 hover:bg-slate-700 text-[10px] font-bold rounded transition-colors flex items-center justify-center">
                    <Play className="h-3 w-3 mr-1" />
                    View Clip
                  </button>
                </div>
              ))}
            </div>
            <div className="p-4 bg-slate-800/30 text-center">
              <Link href="/events" className="text-xs text-blue-500 font-medium hover:underline">
                View All Events
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
