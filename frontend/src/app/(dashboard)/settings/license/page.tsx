"use client";

import { useLicense } from '@/hooks/useLicense';
import { TIERS, TIER_ORDER, FEATURE_LABELS } from '@/lib/subscription';
import { cn } from '@/lib/utils';
import { Check, X, Shield, Star, Crown, Zap, Building2, Globe } from 'lucide-react';

const TIER_ICONS: Record<string, any> = {
  solo: Shield,
  pro: Star,
  business: Zap,
  enterprise: Building2,
  enterprise_plus: Crown,
};

export default function LicensePage() {
  const { license, loading } = useLicense();

  if (loading) return <div className="animate-pulse space-y-8">
    <div className="h-48 bg-slate-900 rounded-xl"/>
    <div className="grid grid-cols-5 gap-4"><div className="h-96 bg-slate-900 rounded-xl"/><div className="h-96 bg-slate-900 rounded-xl"/><div className="h-96 bg-slate-900 rounded-xl"/><div className="h-96 bg-slate-900 rounded-xl"/><div className="h-96 bg-slate-900 rounded-xl"/></div>
  </div>;

  return (
    <div className="space-y-12">
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-8 flex flex-col md:flex-row md:items-center justify-between gap-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Subscription & License</h1>
          <p className="text-slate-400">Manage your Spevino LP-OS plan and features.</p>
          
          <div className="mt-6 flex flex-wrap gap-4">
             <div className="px-4 py-2 bg-slate-800 rounded-lg border border-slate-700">
                <p className="text-xs text-slate-500 uppercase tracking-wider font-bold mb-1">Status</p>
                <div className="flex items-center space-x-2">
                   <div className={cn(
                      "w-2 h-2 rounded-full",
                      license?.is_active ? "bg-green-500" : "bg-red-500"
                   )} />
                   <span className="font-semibold capitalize">{license?.status}</span>
                </div>
             </div>
             <div className="px-4 py-2 bg-slate-800 rounded-lg border border-slate-700">
                <p className="text-xs text-slate-500 uppercase tracking-wider font-bold mb-1">Current Tier</p>
                <span className="font-semibold">{license?.tier_name}</span>
             </div>
             {license?.expiry && (
                <div className="px-4 py-2 bg-slate-800 rounded-lg border border-slate-700">
                   <p className="text-xs text-slate-500 uppercase tracking-wider font-bold mb-1">Expires On</p>
                   <span className="font-semibold">{new Date(license.expiry).toLocaleDateString()}</span>
                </div>
             )}
          </div>
        </div>
        
        <div className="flex flex-col gap-4">
           <button className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold transition-colors">
              Upgrade Subscription
           </button>
           <button className="px-6 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-xl font-bold border border-slate-700 transition-colors">
              Enter License Key
           </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {TIER_ORDER.map((tierKey) => {
          const tier = TIERS[tierKey];
          const isCurrent = license?.tier === tierKey;
          const Icon = TIER_ICONS[tierKey] || Shield;
          
          return (
            <div 
              key={tierKey} 
              className={cn(
                "relative flex flex-col bg-slate-900 rounded-2xl border transition-all duration-300",
                isCurrent 
                  ? "border-blue-500 ring-4 ring-blue-500/10 scale-105 z-10" 
                  : "border-slate-800 hover:border-slate-700"
              )}
            >
              {isCurrent && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-blue-500 text-white text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-widest">
                  Current Plan
                </div>
              )}
              
              <div className="p-6 border-b border-slate-800 text-center">
                <div className={cn(
                  "w-12 h-12 mx-auto rounded-xl flex items-center justify-center mb-4 text-white",
                  tier.color
                )}>
                  <Icon className="h-6 w-6" />
                </div>
                <h3 className="text-xl font-bold mb-1">{tier.name}</h3>
                <div className="flex items-baseline justify-center">
                  <span className="text-2xl font-bold">${tier.price}</span>
                  <span className="text-slate-500 text-sm ml-1">/mo</span>
                </div>
              </div>
              
              <div className="p-6 flex-1 space-y-6">
                <div className="space-y-2">
                  <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Capacity</p>
                  <div className="space-y-1">
                    <p className="text-sm text-slate-300">
                      <span className="font-semibold text-white">{tier.max_stores === 9999 ? 'Unlimited' : tier.max_stores}</span> {tier.max_stores === 1 ? 'Store' : 'Stores'}
                    </p>
                    <p className="text-sm text-slate-300">
                      <span className="font-semibold text-white">{tier.max_cameras === 9999 ? 'Unlimited' : tier.max_cameras}</span> {tier.max_cameras === 1 ? 'Camera' : 'Cameras'}
                    </p>
                  </div>
                </div>

                <div className="space-y-3">
                  <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Features</p>
                  <ul className="space-y-2">
                    {Object.keys(FEATURE_LABELS).map((featureKey) => {
                      const hasFeature = tier.features.includes(featureKey);
                      return (
                        <li key={featureKey} className="flex items-start text-xs">
                          {hasFeature ? (
                            <Check className="h-3.5 w-3.5 text-green-500 mr-2 mt-0.5 shrink-0" />
                          ) : (
                            <X className="h-3.5 w-3.5 text-slate-700 mr-2 mt-0.5 shrink-0" />
                          )}
                          <span className={hasFeature ? "text-slate-300" : "text-slate-600 line-through"}>
                            {FEATURE_LABELS[featureKey]}
                          </span>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              </div>
              
              <div className="p-6 pt-0 mt-auto">
                {!isCurrent ? (
                  <button className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-sm font-bold transition-colors">
                    {TIER_ORDER.indexOf(tierKey) < TIER_ORDER.indexOf(license?.tier || 'solo') ? 'Downgrade' : 'Upgrade'}
                  </button>
                ) : (
                  <div className="w-full py-2 bg-blue-500/10 text-blue-500 rounded-lg text-sm font-bold text-center border border-blue-500/20">
                    Active
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
      
      <div className="bg-slate-900 rounded-2xl border border-slate-800 p-8">
        <h2 className="text-xl font-bold mb-6">Frequently Asked Questions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
           <div className="space-y-2">
              <h4 className="font-semibold text-slate-200">How does the 14-day trial work?</h4>
              <p className="text-sm text-slate-400">Every new installation starts in a 14-day trial mode with basic detection features. After 14 days, CV detection and SMS alerts are paused until a valid license is activated.</p>
           </div>
           <div className="space-y-2">
              <h4 className="font-semibold text-slate-200">Can I upgrade or downgrade anytime?</h4>
              <p className="text-sm text-slate-400">Yes, you can change your plan at any time. When upgrading, new features are unlocked instantly. When downgrading, changes take effect at the end of your current billing cycle.</p>
           </div>
           <div className="space-y-2">
              <h4 className="font-semibold text-slate-200">What happens if I exceed my camera limit?</h4>
              <p className="text-sm text-slate-400">The system will prevent you from adding more cameras than your tier allows. You'll need to upgrade to a higher tier to monitor more cameras at your location.</p>
           </div>
           <div className="space-y-2">
              <h4 className="font-semibold text-slate-200">Does Spevino support on-prem deployment?</h4>
              <p className="text-sm text-slate-400">Yes, our Enterprise+ plan includes full on-premise deployment support and white-labeling for large retail chains.</p>
           </div>
        </div>
      </div>
    </div>
  );
}
