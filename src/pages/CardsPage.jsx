import React from 'react';
import { Plus } from 'lucide-react';
import { Button } from '../components/Button';

/**
 * Cards page (placeholder)
 */
export const CardsPage = () => {
  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">My Cards</h2>
          <p className="text-sm text-gray-500 mt-1">Manage your payment cards</p>
        </div>
        <Button variant="primary" icon={<Plus size={18} />}>
          Add New Card
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Card 1 */}
        <div className="bg-gradient-to-br from-primary-600 to-primary-800 rounded-2xl p-6 text-white shadow-xl">
          <div className="flex justify-between items-start mb-8">
            <span className="text-sm opacity-80">Exp 09/24</span>
            <div className="flex space-x-1">
              <div className="w-2 h-2 rounded-full bg-white opacity-80"></div>
              <div className="w-2 h-2 rounded-full bg-white opacity-80"></div>
              <div className="w-2 h-2 rounded-full bg-white opacity-80"></div>
            </div>
          </div>
          <div className="space-y-4">
            <p className="text-2xl font-bold tracking-wider">VISA</p>
            <div className="space-y-1">
              <p className="text-base tracking-widest">1253 5432</p>
              <p className="text-base tracking-widest">3521 3090</p>
            </div>
          </div>
        </div>

        {/* Card 2 */}
        <div className="bg-gradient-to-br from-blue-600 to-blue-800 rounded-2xl p-6 text-white shadow-xl">
          <div className="flex justify-between items-start mb-8">
            <span className="text-sm opacity-80">Exp 12/25</span>
            <div className="flex space-x-1">
              <div className="w-2 h-2 rounded-full bg-white opacity-80"></div>
              <div className="w-2 h-2 rounded-full bg-white opacity-80"></div>
              <div className="w-2 h-2 rounded-full bg-white opacity-80"></div>
            </div>
          </div>
          <div className="space-y-4">
            <p className="text-2xl font-bold tracking-wider">MASTERCARD</p>
            <div className="space-y-1">
              <p className="text-base tracking-widest">8845 6721</p>
              <p className="text-base tracking-widest">9034 1256</p>
            </div>
          </div>
        </div>

        {/* Add New Card */}
        <div className="border-2 border-dashed border-gray-300 rounded-2xl p-6 flex flex-col items-center justify-center hover:border-primary-500 hover:bg-primary-50 transition-colors cursor-pointer">
          <Plus size={48} className="text-gray-400 mb-4" />
          <p className="text-gray-600 font-medium">Add New Card</p>
        </div>
      </div>
    </div>
  );
};
