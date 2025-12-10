/**
 * Mock recurring payment data
 * @typedef {Object} RecurringPayment
 * @property {string} id - Unique identifier
 * @property {string} merchant - Merchant name
 * @property {number} averageAmount - Average payment amount
 * @property {string} frequency - Payment frequency
 * @property {string} nextDate - Next predicted charge date
 * @property {string} category - Payment category
 */

export const mockRecurringPayments = [
  {
    id: 'rec_001',
    merchant: 'Netflix',
    averageAmount: 15.99,
    frequency: 'Monthly',
    nextDate: '2025-12-26',
    category: 'Entertainment'
  },
  {
    id: 'rec_002',
    merchant: 'Spotify',
    averageAmount: 10.99,
    frequency: 'Monthly',
    nextDate: '2025-12-22',
    category: 'Entertainment'
  },
  {
    id: 'rec_003',
    merchant: 'Amazon Prime',
    averageAmount: 14.99,
    frequency: 'Monthly',
    nextDate: '2025-12-25',
    category: 'Subscriptions'
  },
  {
    id: 'rec_004',
    merchant: 'LA Fitness',
    averageAmount: 49.99,
    frequency: 'Monthly',
    nextDate: '2025-12-18',
    category: 'Health'
  },
  {
    id: 'rec_005',
    merchant: 'Comcast',
    averageAmount: 79.99,
    frequency: 'Monthly',
    nextDate: '2025-12-17',
    category: 'Utilities'
  },
  {
    id: 'rec_006',
    merchant: 'Electric Company',
    averageAmount: 92.34,
    frequency: 'Monthly',
    nextDate: '2025-12-03',
    category: 'Utilities'
  },
  {
    id: 'rec_007',
    merchant: 'Apple iCloud',
    averageAmount: 2.99,
    frequency: 'Monthly',
    nextDate: '2025-12-10',
    category: 'Subscriptions'
  },
  {
    id: 'rec_008',
    merchant: 'Planet Fitness',
    averageAmount: 24.99,
    frequency: 'Monthly',
    nextDate: '2025-12-05',
    category: 'Health'
  }
];
