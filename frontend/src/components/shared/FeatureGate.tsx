import React from 'react';
import { Lock, ArrowUpCircle } from 'lucide-react';
import { useLicense } from '@/hooks/useLicense';
import { cn } from '@/lib/utils';
import Link from 'next/link';
import { getNextTier, TIERS } from '@/lib/subscription';

interface FeatureGateProps {
  feature: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
  className?: string;
}

export default function FeatureGate({ feature, children, fallback, className }: FeatureGateProps) {
  const { hasFeature, license, loading } = useLicense();

  if (loading) return <div className="animate-pulse bg-slate-800 h-24 rounded-xl" />;

  const isLocked = !hasFeature(feature);

  if (isLocked) {
    if (fallback) return <>{fallback}</>;

    const nextTier = getNextTier(license?.tier || 'solo');
    const nextTierInfo = nextTier ? TIERS[nextTier] : null;

    return (
      <div className={cn(
        "relative overflow-hidden rounded-xl border border-slate-800 bg-slate-900/50 p-8 text-center",
        className
      )}>
        <div className="absolute inset-0 bg-slate-950/40 backdrop-blur-[2px] flex items-center justify-center">
          <div className="max-w-md px-6">
            <div className="mx-auto w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center mb-4">
              <Lock className="h-6 w-6 text-slate-400" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Feature Locked</h3>
            <p className="text-sm text-slate-400 mb-6">
              This feature is available on the {nextTierInfo?.name || 'Enterprise'} plan and above. 
              Upgrade your subscription to unlock it.
            </p>
            <Link 
              href="/settings/license"
              className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
            >
              <ArrowUpCircle className="h-4 w-4 mr-2" />
              View Upgrade Options
            </Link>
          </div>
        </div>
        <div className="opacity-10 pointer-events-none select-none">
          {children}
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
