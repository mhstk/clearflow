/**
 * Mock transaction data
 * @typedef {Object} Transaction
 * @property {string} id - Unique identifier
 * @property {string} date - ISO date string
 * @property {string} descriptionRaw - Raw bank description
 * @property {string} noteUser - User-friendly note
 * @property {string} category - Transaction category
 * @property {string} merchant - Merchant name
 * @property {number} amount - Transaction amount (negative for spending)
 */

export const mockTransactions = [
  {
    id: 'txn_001',
    date: '2025-11-28',
    descriptionRaw: 'WHOLE FOODS MKT #10347 CHICAGO IL',
    noteUser: 'Weekly grocery shopping',
    category: 'Groceries',
    merchant: 'Whole Foods',
    amount: -127.45
  },
  {
    id: 'txn_002',
    date: '2025-11-27',
    descriptionRaw: 'UBER *TRIP HELP.UBER.COM CA',
    noteUser: 'Ride to downtown',
    category: 'Transportation',
    merchant: 'Uber',
    amount: -23.50
  },
  {
    id: 'txn_003',
    date: '2025-11-26',
    descriptionRaw: 'NETFLIX.COM LOS GATOS CA',
    noteUser: 'Monthly subscription',
    category: 'Entertainment',
    merchant: 'Netflix',
    amount: -15.99
  },
  {
    id: 'txn_004',
    date: '2025-11-25',
    descriptionRaw: 'STARBUCKS STORE #18467',
    noteUser: 'Morning coffee',
    category: 'Dining',
    merchant: 'Starbucks',
    amount: -6.75
  },
  {
    id: 'txn_005',
    date: '2025-11-25',
    descriptionRaw: 'PAYPAL *AMAZONPRIME 402-935-7733 WA',
    noteUser: 'Amazon Prime membership',
    category: 'Subscriptions',
    merchant: 'Amazon Prime',
    amount: -14.99
  },
  {
    id: 'txn_006',
    date: '2025-11-24',
    descriptionRaw: 'SHELL OIL 57444239800 CHICAGO IL',
    noteUser: 'Gas fill-up',
    category: 'Transportation',
    merchant: 'Shell',
    amount: -52.30
  },
  {
    id: 'txn_007',
    date: '2025-11-23',
    descriptionRaw: 'TRADER JOES #514 CHICAGO IL',
    noteUser: 'Quick grocery run',
    category: 'Groceries',
    merchant: 'Trader Joes',
    amount: -43.20
  },
  {
    id: 'txn_008',
    date: '2025-11-22',
    descriptionRaw: 'CHIPOTLE 2353 EVANSTON IL',
    noteUser: 'Lunch with colleagues',
    category: 'Dining',
    merchant: 'Chipotle',
    amount: -18.95
  },
  {
    id: 'txn_009',
    date: '2025-11-22',
    descriptionRaw: 'SPOTIFY USA 877-7781161 NY',
    noteUser: 'Music subscription',
    category: 'Entertainment',
    merchant: 'Spotify',
    amount: -10.99
  },
  {
    id: 'txn_010',
    date: '2025-11-21',
    descriptionRaw: 'WALGREENS #4589 CHICAGO IL',
    noteUser: 'Pharmacy and toiletries',
    category: 'Health',
    merchant: 'Walgreens',
    amount: -34.67
  },
  {
    id: 'txn_011',
    date: '2025-11-20',
    descriptionRaw: 'TARGET 00003456 CHICAGO IL',
    noteUser: 'Household items',
    category: 'Shopping',
    merchant: 'Target',
    amount: -89.32
  },
  {
    id: 'txn_012',
    date: '2025-11-19',
    descriptionRaw: 'VENMO *PAYMENT',
    noteUser: 'Split dinner bill',
    category: 'Dining',
    merchant: 'Venmo',
    amount: -35.00
  },
  {
    id: 'txn_013',
    date: '2025-11-18',
    descriptionRaw: 'LA FITNESS #0234 MEMBERSHIP',
    noteUser: 'Gym membership',
    category: 'Health',
    merchant: 'LA Fitness',
    amount: -49.99
  },
  {
    id: 'txn_014',
    date: '2025-11-17',
    descriptionRaw: 'COMCAST CABLE COMM IL',
    noteUser: 'Internet bill',
    category: 'Utilities',
    merchant: 'Comcast',
    amount: -79.99
  },
  {
    id: 'txn_015',
    date: '2025-11-16',
    descriptionRaw: 'PANERA BREAD #3401 CHICAGO IL',
    noteUser: 'Breakfast',
    category: 'Dining',
    merchant: 'Panera Bread',
    amount: -12.50
  },
  {
    id: 'txn_016',
    date: '2025-11-15',
    descriptionRaw: 'DEPOSIT - PAYROLL ACH',
    noteUser: 'Monthly salary',
    category: 'Income',
    merchant: 'Employer',
    amount: 5500.00
  },
  {
    id: 'txn_017',
    date: '2025-11-14',
    descriptionRaw: 'AMAZON.COM*M23K45 AMZN.COM/BILL WA',
    noteUser: 'Office supplies',
    category: 'Shopping',
    merchant: 'Amazon',
    amount: -67.84
  },
  {
    id: 'txn_018',
    date: '2025-11-13',
    descriptionRaw: 'UBER EATS HELP.UBER.COM',
    noteUser: 'Dinner delivery',
    category: 'Dining',
    merchant: 'Uber Eats',
    amount: -32.45
  },
  {
    id: 'txn_019',
    date: '2025-11-12',
    descriptionRaw: 'BP#5478900 CHICAGO IL',
    noteUser: 'Gas',
    category: 'Transportation',
    merchant: 'BP',
    amount: -48.20
  },
  {
    id: 'txn_020',
    date: '2025-11-11',
    descriptionRaw: 'JEWEL-OSCO #3042 CHICAGO IL',
    noteUser: 'Weekly groceries',
    category: 'Groceries',
    merchant: 'Jewel-Osco',
    amount: -115.60
  },
  {
    id: 'txn_021',
    date: '2025-11-10',
    descriptionRaw: 'APPLE.COM/BILL 866-712-7753 CA',
    noteUser: 'iCloud storage',
    category: 'Subscriptions',
    merchant: 'Apple',
    amount: -2.99
  },
  {
    id: 'txn_022',
    date: '2025-11-09',
    descriptionRaw: 'COSTCO WHSE #0123 CHICAGO IL',
    noteUser: 'Bulk shopping',
    category: 'Groceries',
    merchant: 'Costco',
    amount: -156.78
  },
  {
    id: 'txn_023',
    date: '2025-11-08',
    descriptionRaw: 'DUNKIN #338845 CHICAGO IL',
    noteUser: 'Coffee and donut',
    category: 'Dining',
    merchant: 'Dunkin',
    amount: -5.49
  },
  {
    id: 'txn_024',
    date: '2025-11-07',
    descriptionRaw: 'ATM WITHDRAWAL',
    noteUser: 'Cash withdrawal',
    category: 'Cash',
    merchant: 'ATM',
    amount: -100.00
  },
  {
    id: 'txn_025',
    date: '2025-11-06',
    descriptionRaw: 'CVS/PHARMACY #9842 CHICAGO IL',
    noteUser: 'Prescriptions',
    category: 'Health',
    merchant: 'CVS',
    amount: -28.45
  },
  {
    id: 'txn_026',
    date: '2025-11-05',
    descriptionRaw: 'PLANET FITNESS MONTHLY',
    noteUser: 'Gym membership',
    category: 'Health',
    merchant: 'Planet Fitness',
    amount: -24.99
  },
  {
    id: 'txn_027',
    date: '2025-11-04',
    descriptionRaw: 'MCDONALD\'S F23455',
    noteUser: 'Quick lunch',
    category: 'Dining',
    merchant: 'McDonalds',
    amount: -9.87
  },
  {
    id: 'txn_028',
    date: '2025-11-03',
    descriptionRaw: 'ELECTRIC COMPANY OF IL',
    noteUser: 'Electricity bill',
    category: 'Utilities',
    merchant: 'Electric Company',
    amount: -92.34
  },
  {
    id: 'txn_029',
    date: '2025-11-02',
    descriptionRaw: 'LYFT *RIDE LYFT.COM',
    noteUser: 'Ride to airport',
    category: 'Transportation',
    merchant: 'Lyft',
    amount: -45.30
  },
  {
    id: 'txn_030',
    date: '2025-11-01',
    descriptionRaw: 'BEST BUY #00345 CHICAGO IL',
    noteUser: 'Electronics purchase',
    category: 'Shopping',
    merchant: 'Best Buy',
    amount: -245.99
  },
  {
    id: 'txn_031',
    date: '2025-10-30',
    descriptionRaw: 'WHOLE FOODS MKT #10347 CHICAGO IL',
    noteUser: 'Weekly groceries',
    category: 'Groceries',
    merchant: 'Whole Foods',
    amount: -134.25
  },
  {
    id: 'txn_032',
    date: '2025-10-28',
    descriptionRaw: 'STARBUCKS STORE #18467',
    noteUser: 'Morning coffee',
    category: 'Dining',
    merchant: 'Starbucks',
    amount: -7.25
  },
  {
    id: 'txn_033',
    date: '2025-10-26',
    descriptionRaw: 'NETFLIX.COM LOS GATOS CA',
    noteUser: 'Monthly subscription',
    category: 'Entertainment',
    merchant: 'Netflix',
    amount: -15.99
  },
  {
    id: 'txn_034',
    date: '2025-10-25',
    descriptionRaw: 'TARGET 00003456 CHICAGO IL',
    noteUser: 'Household shopping',
    category: 'Shopping',
    merchant: 'Target',
    amount: -72.18
  },
  {
    id: 'txn_035',
    date: '2025-10-23',
    descriptionRaw: 'SHELL OIL 57444239800 CHICAGO IL',
    noteUser: 'Gas fill-up',
    category: 'Transportation',
    merchant: 'Shell',
    amount: -55.60
  },
  {
    id: 'txn_036',
    date: '2025-10-20',
    descriptionRaw: 'TRADER JOES #514 CHICAGO IL',
    noteUser: 'Groceries',
    category: 'Groceries',
    merchant: 'Trader Joes',
    amount: -38.90
  },
  {
    id: 'txn_037',
    date: '2025-10-18',
    descriptionRaw: 'COMCAST CABLE COMM IL',
    noteUser: 'Internet bill',
    category: 'Utilities',
    merchant: 'Comcast',
    amount: -79.99
  },
  {
    id: 'txn_038',
    date: '2025-10-15',
    descriptionRaw: 'DEPOSIT - PAYROLL ACH',
    noteUser: 'Monthly salary',
    category: 'Income',
    merchant: 'Employer',
    amount: 5500.00
  },
  {
    id: 'txn_039',
    date: '2025-10-12',
    descriptionRaw: 'JEWEL-OSCO #3042 CHICAGO IL',
    noteUser: 'Weekly groceries',
    category: 'Groceries',
    merchant: 'Jewel-Osco',
    amount: -108.45
  },
  {
    id: 'txn_040',
    date: '2025-10-08',
    descriptionRaw: 'SPOTIFY USA 877-7781161 NY',
    noteUser: 'Music subscription',
    category: 'Entertainment',
    merchant: 'Spotify',
    amount: -10.99
  }
];

export const categories = [
  'Groceries',
  'Dining',
  'Transportation',
  'Entertainment',
  'Shopping',
  'Health',
  'Utilities',
  'Subscriptions',
  'Income',
  'Cash'
];
