/**
 * Mock dashboard data
 */

export const mockDashboardStats = {
  totalSpending: 1847.32,
  totalIncome: 11000.00,
  transactionCount: 38,
  recurringCount: 8
};

export const mockSpendingOverTime = [
  { month: 'Jul', amount: 1650 },
  { month: 'Aug', amount: 1820 },
  { month: 'Sep', amount: 1590 },
  { month: 'Oct', amount: 1735 },
  { month: 'Nov', amount: 1847 },
  { month: 'Dec', amount: 850 }
];

export const mockCategoryBreakdown = [
  { name: 'Groceries', value: 726.18, color: '#22c55e' },
  { name: 'Dining', value: 283.21, color: '#3b82f6' },
  { name: 'Transportation', value: 224.90, color: '#f59e0b' },
  { name: 'Shopping', value: 475.33, color: '#8b5cf6' },
  { name: 'Utilities', value: 252.32, color: '#ef4444' },
  { name: 'Entertainment', value: 42.97, color: '#ec4899' },
  { name: 'Health', value: 187.09, color: '#06b6d4' },
  { name: 'Subscriptions', value: 32.97, color: '#84cc16' }
];

export const mockAIInsights = [
  {
    id: 1,
    text: "Your top spending category this month is Groceries at $726.18, representing 36% of total spending."
  },
  {
    id: 2,
    text: "Transportation costs decreased by 15% compared to last month - great job!"
  },
  {
    id: 3,
    text: "You have 8 recurring payments totaling $275/month. Consider reviewing subscriptions you might not be using."
  },
  {
    id: 4,
    text: "Dining out spending is up 12% from last month. Consider meal prepping to save money."
  },
  {
    id: 5,
    text: "You're on track to save $3,152 this month based on your income and spending patterns."
  }
];
