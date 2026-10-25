import React from 'react';
import { 
  Scale, 
  Search, 
  FileText, 
  GitCompare, 
  CheckSquare, 
  BarChart3, 
  ShieldAlert,
  Building,
  LogOut,
  User
} from 'lucide-react';
import { UserProfile } from '../types';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  user: UserProfile | null;
  onOpenAuth: () => void;
  onLogout: () => void;
  reviewCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  user,
  onOpenAuth,
  onLogout,
  reviewCount,
}) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    { id: 'research', label: 'Legal Research', icon: Search },
    { id: 'documents', label: 'Documents', icon: FileText },
    { id: 'analysis', label: 'Contract Redline', icon: GitCompare },
    { id: 'reviews', label: 'Review Queue', icon: CheckSquare, badge: reviewCount > 0 ? reviewCount : undefined },
    { id: 'evaluations', label: 'Evaluations', icon: ShieldAlert },
  ];

  return (
    <header className="sticky top-0 z-50 bg-[#0B132B]/95 backdrop-blur-md border-b border-slate-800 px-6 py-3.5">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand */}
        <div 
          onClick={() => setActiveTab('dashboard')} 
          className="flex items-center gap-3 cursor-pointer group"
        >
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-amber-500 to-amber-700 flex items-center justify-center shadow-lg shadow-amber-500/10 group-hover:shadow-amber-500/25 transition-all">
            <Scale className="w-5 h-5 text-slate-950 font-bold" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-serif font-bold text-lg text-white tracking-wide">TrustCounsel</span>
              <span className="text-[10px] uppercase font-bold tracking-widest px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30">AI</span>
            </div>
            <p className="text-[11px] text-slate-400 tracking-tight">Enterprise Legal Intelligence & Truth Verification</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="hidden md:flex items-center gap-1 bg-[#070C18]/80 p-1.5 rounded-xl border border-slate-800/80">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-medium transition-all relative ${
                  isActive
                    ? 'bg-[#1C2541] text-amber-300 shadow-sm border border-slate-700'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-amber-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
                {item.badge !== undefined && (
                  <span className="w-4 h-4 rounded-full bg-purple-500 text-[10px] text-white flex items-center justify-center font-bold">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* User Workspace Info & Auth Button */}
        <div className="flex items-center gap-3">
          {user ? (
            <div className="flex items-center gap-3 bg-[#0D1527] border border-slate-800 py-1.5 px-3 rounded-xl">
              <div className="flex items-center gap-2 text-left">
                <div className="w-7 h-7 rounded-full bg-slate-800 flex items-center justify-center text-amber-400 font-semibold text-xs border border-slate-700">
                  {user.full_name.charAt(0)}
                </div>
                <div>
                  <div className="text-xs font-medium text-slate-200">{user.full_name}</div>
                  <div className="flex items-center gap-1 text-[10px] text-amber-400/80">
                    <Building className="w-2.5 h-2.5" />
                    <span>Workspace Active</span>
                  </div>
                </div>
              </div>
              <button
                onClick={onLogout}
                title="Sign Out"
                className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 transition-colors ml-1"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <button
              onClick={onOpenAuth}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 text-xs font-semibold shadow-lg shadow-amber-500/10 transition-all cursor-pointer"
            >
              <User className="w-3.5 h-3.5" />
              <span>Sign In / Workspace</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
