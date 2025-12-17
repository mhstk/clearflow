import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Receipt, Repeat, Upload, Settings, Users, CreditCard, Mail, Shield, Tags } from 'lucide-react';
import logo512 from '../resources/logo/512.png';

/**
 * Icon-only Sidebar navigation component (collapsed style)
 */
export const Sidebar = ({ isOpen, onClose }) => {
  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/transactions', label: 'Transactions', icon: Receipt },
    { path: '/recurring', label: 'Recurring', icon: Repeat },
    { path: '/categories', label: 'Categories', icon: Tags },
    // { path: '/cards', label: 'Cards', icon: CreditCard },
    { path: '/upload', label: 'Upload', icon: Upload },
    // { path: '/users', label: 'Users', icon: Users },
    // { path: '/mail', label: 'Mail', icon: Mail },
    { path: '/settings', label: 'Settings', icon: Settings },
    // { path: '/security', label: 'Security', icon: Shield }
  ];

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar - Icon Only */}
      <aside
        className={`
          fixed md:static inset-y-0 left-0 z-50
          w-20 bg-white border-r border-gray-100
          transform transition-transform duration-300 ease-in-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        `}
      >
        <div className="flex flex-col h-full items-center py-6">
          {/* Logo */}
          <div className="mb-8">
            <img src={logo512} alt="ClearFlow" className="w-12 h-12 rounded-2xl shadow-lg" />
          </div>

          {/* Navigation Icons */}
          <nav className="flex-1 w-full px-3">
            <ul className="space-y-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <li key={item.path}>
                    <NavLink
                      to={item.path}
                      onClick={onClose}
                      title={item.label}
                      className={({ isActive }) =>
                        `flex items-center justify-center w-14 h-14 rounded-xl transition-all ${
                          isActive
                            ? 'bg-primary-50 text-primary-600'
                            : 'text-gray-400 hover:bg-gray-50 hover:text-gray-600'
                        }`
                      }
                      end={item.path === '/'}
                    >
                      <Icon size={24} />
                    </NavLink>
                  </li>
                );
              })}
            </ul>
          </nav>

        </div>
      </aside>
    </>
  );
};
