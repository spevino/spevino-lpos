"use client";

import { useEffect, useState } from 'react';
import { ShieldAlert, Search, Filter, Calendar, ExternalLink } from 'lucide-react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { formatDate } from '@/lib/utils';
import { cn } from '@/lib/utils';

export default function EventsPage() {
  const [events, setEvents] = useState<any[]>([]);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    // Mock data
    setEvents([
      { id: '1', store: 'QuickMart #42', camera: 'Entrance', type: 'shoplifting_suspected', confidence: 0.89, description: 'Suspected concealment in Aisle 4', created_at: new Date().toISOString() },
      { id: '2', store: 'QuickMart #42', camera: 'Aisle 3', type: 'motion_anomaly', confidence: 0.75, description: 'Movement detected in staff area', created_at: new Date(Date.now() - 3600000).toISOString() },
      { id: '3', store: 'Shell Station - Oak Dr', camera: 'Checkout', type: 'shoplifting_suspected', confidence: 0.92, description: 'Quick movement towards exit', created_at: new Date(Date.now() - 7200000).toISOString() },
      { id: '4', store: 'QuickMart #42', camera: 'Register 1', type: 'cash_register_theft', confidence: 0.83, description: 'Unauthorized void without customer present', created_at: new Date(Date.now() - 9000000).toISOString() },
      { id: '5', store: 'QuickMart #42', camera: 'Back Office', type: 'restricted_area_breach', confidence: 0.98, description: 'Unauthorized entry into back office', created_at: new Date(Date.now() - 10800000).toISOString() },
      { id: '6', store: 'QuickMart #42', camera: 'Entrance', type: 'object_left', confidence: 0.65, description: 'Bag left unattended near door', created_at: new Date(Date.now() - 86400000).toISOString() },
      { id: '7', store: 'Shell Station - Oak Dr', camera: 'Storage', type: 'restricted_area_breach', confidence: 0.94, description: 'Person detected in restricted storage zone', created_at: new Date(Date.now() - 14400000).toISOString() },
    ]);
  }, []);

  const filteredEvents = filter === 'all' 
    ? events 
    : events.filter(e => e.type === filter);

  const eventTypes = [
    { id: 'all', label: 'All Events' },
    { id: 'shoplifting_suspected', label: 'Shoplifting' },
    { id: 'restricted_area_breach', label: 'Restricted Area' },
    { id: 'cash_register_theft', label: 'Cash Theft' },
    { id: 'motion_anomaly', label: 'Motion' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold">Event History</h1>
          <p className="text-slate-400 text-sm mt-1">Review and manage surveillance alerts</p>
        </div>
        <div className="flex space-x-3">
          <button className="flex items-center px-4 py-2 bg-slate-800 border border-slate-700 hover:bg-slate-700 text-white rounded-lg transition-colors text-sm font-medium">
            <Calendar className="h-4 w-4 mr-2" />
            Last 24 Hours
          </button>
        </div>
      </div>

      <div className="flex overflow-x-auto pb-2 space-x-2 scrollbar-hide">
        {eventTypes.map((type) => (
          <button
            key={type.id}
            onClick={() => setFilter(type.id)}
            className={cn(
              "px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap border transition-all",
              filter === type.id
                ? "bg-blue-600 border-blue-600 text-white shadow-lg shadow-blue-500/20"
                : "bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-300"
            )}
          >
            {type.label}
          </button>
        ))}
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-800/50 border-b border-slate-800 text-slate-400">
                <th className="px-6 py-4 text-xs font-semibold uppercase tracking-wider">Time</th>
                <th className="px-6 py-4 text-xs font-semibold uppercase tracking-wider">Location</th>
                <th className="px-6 py-4 text-xs font-semibold uppercase tracking-wider">Type</th>
                <th className="px-6 py-4 text-xs font-semibold uppercase tracking-wider">Confidence</th>
                <th className="px-6 py-4 text-xs font-semibold uppercase tracking-wider">Description</th>
                <th className="px-6 py-4 text-xs font-semibold uppercase tracking-wider">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {filteredEvents.length > 0 ? (
                filteredEvents.map((event) => (
                  <tr key={event.id} className="hover:bg-slate-800/30 transition-colors group">
                    <td className="px-6 py-4 text-sm text-slate-300 whitespace-nowrap">
                      {formatDate(event.created_at)}
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-slate-200">{event.store}</div>
                      <div className="text-xs text-slate-500">{event.camera}</div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={cn(
                        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
                        event.type === 'shoplifting_suspected' ? 'bg-red-500/10 text-red-500' :
                        event.type === 'restricted_area_breach' ? 'bg-orange-500/10 text-orange-500' :
                        event.type === 'cash_register_theft' ? 'bg-purple-500/10 text-purple-500' :
                        event.type === 'motion_anomaly' ? 'bg-amber-500/10 text-amber-500' :
                        'bg-blue-500/10 text-blue-500'
                      )}>
                        {event.type.replace('_', ' ').toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2">
                        <div className="flex-1 h-1.5 w-12 bg-slate-800 rounded-full overflow-hidden">
                          <div 
                            className={cn(
                              "h-full rounded-full",
                              event.confidence > 0.85 ? "bg-green-500" : event.confidence > 0.7 ? "bg-amber-500" : "bg-slate-500"
                            )}
                            style={{ width: `${event.confidence * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-slate-400">{(event.confidence * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-400 max-w-xs truncate">
                      {event.description}
                    </td>
                    <td className="px-6 py-4">
                      <Link 
                        href={`/events/${event.id}`}
                        className="text-blue-500 hover:text-blue-400 text-sm font-medium flex items-center transition-colors"
                      >
                        Review
                        <ExternalLink className="h-3 w-3 ml-1 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                      </Link>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-slate-500 italic">
                    No events found for this filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
