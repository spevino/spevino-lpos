"use client";

import { useEffect, useState } from 'react';
import { Store, Plus, Search, MapPin, ChevronRight } from 'lucide-react';
import Link from 'next/link';
import { api } from '@/lib/api';

export default function StoresPage() {
  const [stores, setStores] = useState<any[]>([]);

  useEffect(() => {
    // Mock data
    setStores([
      { id: '1', name: 'QuickMart #42', address: '123 Main St, Austin TX', camera_count: 4, status: 'Active' },
      { id: '2', name: 'Shell Station - Oak Dr', address: '456 Oak Dr, Austin TX', camera_count: 8, status: 'Active' },
      { id: '3', name: 'Corner Store 7', address: '789 Pine St, Austin TX', camera_count: 2, status: 'Warning' },
    ]);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Stores</h1>
          <p className="text-slate-400 text-sm mt-1">Manage your monitored locations</p>
        </div>
        <button className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
          <Plus className="h-5 w-5 mr-2" />
          Add Store
        </button>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500" />
        <input 
          type="text" 
          placeholder="Search stores..." 
          className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-10 pr-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {stores.map((store) => (
          <Link key={store.id} href={`/stores/${store.id}`}>
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-slate-700 transition-all group">
              <div className="flex justify-between items-start mb-4">
                <div className="p-3 bg-blue-500/10 rounded-lg">
                  <Store className="h-6 w-6 text-blue-500" />
                </div>
                <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full ${
                  store.status === 'Active' ? 'bg-green-500/10 text-green-500' : 'bg-amber-500/10 text-amber-500'
                }`}>
                  {store.status}
                </span>
              </div>
              <h3 className="text-lg font-semibold group-hover:text-blue-500 transition-colors">{store.name}</h3>
              <div className="flex items-center text-slate-400 text-sm mt-2">
                <MapPin className="h-4 w-4 mr-1" />
                {store.address}
              </div>
              <div className="mt-6 pt-6 border-t border-slate-800 flex justify-between items-center">
                <div className="text-sm">
                  <span className="font-semibold text-slate-200">{store.camera_count}</span>
                  <span className="text-slate-500 ml-1">Cameras</span>
                </div>
                <div className="flex items-center text-blue-500 text-sm font-medium">
                  View Detail
                  <ChevronRight className="h-4 w-4 ml-1" />
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
