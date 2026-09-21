'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

interface NavItem {
  href: string;
  icon: string;
  label: string;
  roles?: string[];
}

const NAV_ITEMS: NavItem[] = [
  { href: '/dashboard', icon: '🏠', label: 'Dashboard' },
  { href: '/patients', icon: '👥', label: 'Patients' },
  { href: '/appointments', icon: '📅', label: 'Appointments' },
  { href: '/emr', icon: '📋', label: 'Medical Records' },
  { href: '/laboratory', icon: '🧪', label: 'Laboratory' },
  { href: '/pharmacy', icon: '💊', label: 'Pharmacy' },
  { href: '/billing', icon: '💳', label: 'Billing' },
  { href: '/inpatient', icon: '🛏️', label: 'Inpatient' },
  { href: '/staff', icon: '👨‍⚕️', label: 'Staff', roles: ['ADMINISTRATOR'] },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const role = user?.role ?? '';
  const visibleItems = NAV_ITEMS.filter(
    (item) => !item.roles || item.roles.includes(role)
  );

  const initials = user?.full_name
    ? user.full_name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()
    : '?';

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">🏥</div>
        <div className="sidebar-logo-text">
          <h2>MediCore HMS</h2>
          <span>Hospital System</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        <div className="nav-section-label">Menu</div>
        {visibleItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`nav-item${isActive ? ' active' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="sidebar-footer">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
          <div className="user-avatar">{initials}</div>
          <div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
              {user?.full_name}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--accent)', fontWeight: 500 }}>
              {role}
            </div>
          </div>
        </div>
        <button className="btn btn-secondary w-full" id="sidebar-logout-btn" onClick={logout}>
          🚪 Logout
        </button>
      </div>
    </aside>
  );
}
