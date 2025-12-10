# ClearFlow - Personal Finance Intelligence Dashboard

A modern, responsive React + Tailwind CSS frontend for managing and analyzing personal finances with AI-powered insights.

## Features

- **Dashboard Overview**: View key metrics, spending trends, and category breakdowns
- **Transaction Management**: Filter and explore transactions with Excel-like functionality
- **Recurring Payments**: Track and analyze subscription and recurring payments
- **CSV Upload**: Upload bank statements for automatic categorization
- **AI Insights**: Get intelligent insights about spending habits (placeholder for future API integration)
- **Responsive Design**: Fully responsive layout that works on mobile, tablet, and desktop

## Tech Stack

- **React 18** - Modern React with functional components
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **Recharts** - Responsive chart library
- **Lucide React** - Beautiful icon library
- **Vite** - Fast build tool and dev server

## Getting Started

### Prerequisites

- Node.js 16+ and npm

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open your browser to `http://localhost:3000`

### Build for Production

```bash
npm run build
```

## Project Structure

```
clearflow/
├── src/
│   ├── components/       # Reusable UI components
│   │   ├── Button.jsx
│   │   ├── Badge.jsx
│   │   ├── MetricCard.jsx
│   │   ├── ChartCard.jsx
│   │   ├── FilterPanel.jsx
│   │   ├── TransactionsTable.jsx
│   │   ├── RecurringList.jsx
│   │   ├── Sidebar.jsx
│   │   └── TopBar.jsx
│   ├── pages/           # Page components
│   │   ├── DashboardPage.jsx
│   │   ├── TransactionsPage.jsx
│   │   ├── UploadPage.jsx
│   │   ├── RecurringPage.jsx
│   │   └── SettingsPage.jsx
│   ├── mock/            # Mock data for development
│   │   ├── transactions.js
│   │   ├── dashboard.js
│   │   └── recurring.js
│   ├── App.jsx          # Main app component with routing
│   ├── main.jsx         # Application entry point
│   └── index.css        # Global styles
├── index.html
├── package.json
├── vite.config.js
└── tailwind.config.js
```

## Key Components

### Reusable Components

- **Button**: Multi-variant button component (primary, secondary, ghost, danger)
- **Badge**: Styled badges for categories and statuses
- **MetricCard**: Display key metrics with icons
- **ChartCard**: Wrapper for charts with titles and actions
- **FilterPanel**: Filtering interface for transactions
- **TransactionsTable**: Responsive table with expandable rows
- **RecurringList**: Grid of recurring payment cards
- **Sidebar**: Left navigation sidebar
- **TopBar**: Top header with search and actions

### Pages

- **Dashboard**: Overview with metrics, charts, and AI insights
- **Transactions**: Filterable transaction list with charts
- **Upload**: CSV file upload interface
- **Recurring**: Recurring payments management
- **Settings**: User settings and preferences

## Mock Data

The application currently uses mock data stored in `src/mock/`:

- `transactions.js` - Sample transaction data
- `dashboard.js` - Dashboard statistics and insights
- `recurring.js` - Recurring payment data

This data structure is designed to be easily replaced with real API calls in the future.

## Future Integration

The application is structured to support future backend integration:

1. Replace mock data imports with API calls
2. Use React hooks (e.g., `useEffect`, `useState`) to fetch data
3. Implement actual AI insights via API endpoints
4. Add authentication and user management
5. Connect CSV upload to backend processing

## Styling

The app uses Tailwind CSS with a custom green accent color (`#22C55E`). The design follows modern fintech aesthetics with:

- White backgrounds
- Rounded cards with subtle shadows
- Clean typography
- Responsive layouts
- Professional color palette

## License

MIT
