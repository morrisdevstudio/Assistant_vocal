import { AudioLines, BellRing, Cpu, House, Info, Music2, Palette, ShieldCheck } from 'lucide-react'
import type { SettingsSection } from './navigation'

export type SettingsDetail = Exclude<SettingsSection, 'home'>
export const firstSettingsSection: SettingsDetail = 'appearance'

export const settingsSections = [
  { title: 'Apparence', icon: Palette, page: 'appearance' },
  { title: 'Voix et conversation', icon: AudioLines, page: 'voice' },
  { title: 'Maison et appareils', icon: House, page: 'house' },
  { title: 'IA et recherche', icon: Cpu, page: 'ai' },
  { title: 'Musique', icon: Music2, page: 'music' },
  { title: 'Notifications et sonneries', icon: BellRing, page: 'notifications' },
  { title: 'Données et confidentialité', icon: ShieldCheck, page: 'privacy' },
  { title: 'À propos et diagnostic', icon: Info, page: 'diagnostic' },
] as const
