"use client";

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { TierName } from '@/lib/subscription';

export interface LicenseData {
  status: 'active' | 'expired' | 'grace' | 'invalid' | 'disabled';
  tier: TierName;
  tier_name: string;
  price: number;
  is_active: boolean;
  can_detect: boolean;
  can_alert: boolean;
  max_stores: number;
  max_cameras: number;
  features: string[];
  message?: string;
  grace_days_remaining?: number;
  customer?: string;
  expiry?: string;
}

export function useLicense() {
  const [license, setLicense] = useState<LicenseData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLicense = async () => {
    try {
      setLoading(true);
      // In a real app, this would be: const data = await api.get('/license');
      // For now, we'll mock the response based on the lead's message
      const mockData: LicenseData = {
        status: 'active',
        tier: 'pro',
        tier_name: 'Pro',
        price: 149,
        is_active: true,
        can_detect: true,
        can_alert: true,
        max_stores: 1,
        max_cameras: 6,
        features: ["dashboard", "concealment_detection", "trajectory_detection", "object_abandonment", "sms_alerts", "restricted_area_detection", "wrong_way_flow"],
        message: "✓ System active and licensed."
      };
      
      // Simulate network delay
      await new Promise(resolve => setTimeout(resolve, 500));
      setLicense(mockData);
    } catch (err) {
      setError('Failed to fetch license information');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLicense();
  }, []);

  const hasFeature = (feature: string) => {
    return license?.features.includes(feature) || false;
  };

  return { license, loading, error, hasFeature, refresh: fetchLicense };
}
