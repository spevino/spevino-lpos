export type TierName = 'solo' | 'pro' | 'growth' | 'business' | 'enterprise' | 'global';

export interface TierInfo {
  id: TierName;
  name: string;
  max_stores: number;
  max_cameras: number;
  features: string[];
  price: number;
  color: string;
}

export const FEATURE_LABELS: Record<string, string> = {
  dashboard: 'Real-time Dashboard',
  concealment_detection: 'Concealment Detection',
  trajectory_detection: 'Trajectory Analysis',
  object_abandonment: 'Object Abandonment',
  sms_alerts: 'SMS Alerts',
  restricted_area_detection: 'Restricted Area Breach',
  wrong_way_flow: 'Wrong-way Flow',
  register_theft_detection: 'Cash Register Theft',
  multi_store: 'Multi-store Dashboard',
  api_access: 'API Access',
  custom_detection_zones: 'Custom Detection Zones',
  employee_badge_integration: 'Employee Badge Integration',
  dedicated_support: 'Dedicated Support',
  advanced_analytics: 'Advanced AI Analytics',
  custom_integrations: 'Custom Integrations',
  on_prem_deployment: 'On-prem Deployment',
  sla: 'Service Level Agreement',
  white_label: 'White-label Interface',
  multi_language: 'Multi-language Support',
  global_compliance: 'Global Compliance (GDPR/CCPA)',
  global_data_centers: 'Global Data Centers',
  '24_7_support': '24/7 Multilingual Support',
  custom_model_training: 'Custom Model Training',
};

export const TIERS: Record<TierName, TierInfo> = {
  solo: {
    id: 'solo',
    name: 'Solo',
    max_stores: 1,
    max_cameras: 4,
    features: ['dashboard', 'concealment_detection', 'trajectory_detection', 'object_abandonment'],
    price: 79,
    color: 'bg-amber-700',
  },
  pro: {
    id: 'pro',
    name: 'Pro',
    max_stores: 1,
    max_cameras: 12,
    features: ['dashboard', 'concealment_detection', 'trajectory_detection', 'object_abandonment', 'sms_alerts', 'restricted_area_detection', 'wrong_way_flow'],
    price: 199,
    color: 'bg-slate-400',
  },
  growth: {
    id: 'growth',
    name: 'Growth',
    max_stores: 3,
    max_cameras: 30,
    features: ['dashboard', 'concealment_detection', 'trajectory_detection', 'object_abandonment', 'sms_alerts', 'restricted_area_detection', 'wrong_way_flow', 'register_theft_detection', 'multi_store', 'api_access'],
    price: 499,
    color: 'bg-teal-500',
  },
  business: {
    id: 'business',
    name: 'Business',
    max_stores: 5,
    max_cameras: 60,
    features: ['dashboard', 'concealment_detection', 'trajectory_detection', 'object_abandonment', 'sms_alerts', 'restricted_area_detection', 'wrong_way_flow', 'register_theft_detection', 'multi_store', 'api_access', 'custom_detection_zones', 'employee_badge_integration', 'dedicated_support', 'advanced_analytics'],
    price: 999,
    color: 'bg-blue-500',
  },
  enterprise: {
    id: 'enterprise',
    name: 'Enterprise',
    max_stores: 20,
    max_cameras: 200,
    features: ['dashboard', 'concealment_detection', 'trajectory_detection', 'object_abandonment', 'sms_alerts', 'restricted_area_detection', 'wrong_way_flow', 'register_theft_detection', 'multi_store', 'api_access', 'custom_detection_zones', 'employee_badge_integration', 'dedicated_support', 'advanced_analytics', 'custom_integrations', 'on_prem_deployment', 'sla'],
    price: 2500,
    color: 'bg-purple-600',
  },
  global: {
    id: 'global',
    name: 'Global',
    max_stores: 9999,
    max_cameras: 9999,
    features: ['dashboard', 'concealment_detection', 'trajectory_detection', 'object_abandonment', 'sms_alerts', 'restricted_area_detection', 'wrong_way_flow', 'register_theft_detection', 'multi_store', 'api_access', 'custom_detection_zones', 'employee_badge_integration', 'dedicated_support', 'advanced_analytics', 'custom_integrations', 'on_prem_deployment', 'sla', 'white_label', 'multi_language', 'global_compliance', 'global_data_centers', '24_7_support', 'custom_model_training'],
    price: 5000,
    color: 'bg-rose-600',
  },
};

export const TIER_ORDER: TierName[] = ['solo', 'pro', 'growth', 'business', 'enterprise', 'global'];

export function getNextTier(currentTier: TierName): TierName | null {
  const currentIndex = TIER_ORDER.indexOf(currentTier);
  if (currentIndex >= 0 && currentIndex < TIER_ORDER.length - 1) {
    return TIER_ORDER[currentIndex + 1];
  }
  return null;
}