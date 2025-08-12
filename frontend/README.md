# Trading Bot Frontend

React-based frontend dashboard for the Adaptive Cloud-Ready Trading Bot.

## Features

- **Live Trading Dashboard**: Real-time portfolio monitoring, position tracking, and trade execution
- **Backtesting Interface**: Historical strategy testing with comprehensive performance analysis
- **Strategy Optimization**: Parameter optimization using genetic algorithms and other methods
- **Responsive Design**: Clean, uncluttered interface that works on desktop and mobile
- **Real-time Updates**: WebSocket integration for live data updates
- **Interactive Charts**: Performance visualization using Chart.js

## Quick Start

1. **Install Dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start Development Server**
   ```bash
   npm start
   ```
   The application will open at `http://localhost:3000`

3. **Build for Production**
   ```bash
   npm run build
   ```

## Environment Configuration

Create a `.env` file in the frontend directory:

```env
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=ws://localhost:8000/ws
REACT_APP_ENVIRONMENT=development
```

## Project Structure

```
frontend/
├── public/
│   └── index.html          # HTML template
├── src/
│   ├── components/         # React components
│   │   ├── NavigationBar.jsx
│   │   ├── LiveTradingTab.jsx
│   │   ├── BacktestTab.jsx
│   │   ├── OptimizationTab.jsx
│   │   ├── ResultsChart.jsx
│   │   └── ParameterForm.jsx
│   ├── api/
│   │   └── backend.js      # API integration
│   └── App.jsx             # Main app component
└── package.json
```

## Available Scripts

- `npm start` - Start development server
- `npm run build` - Build for production
- `npm test` - Run tests
- `npm run lint` - Run ESLint
- `npm run format` - Format code with Prettier

## API Integration

The frontend communicates with the Python backend through:
- REST API for data fetching and commands
- WebSocket for real-time updates
- Error handling and retry logic
- Authentication support

## Deployment

### Development
```bash
npm start
```

### Production
```bash
npm run build
npm run serve
```

### Docker
```bash
docker build -t trading-bot-frontend .
docker run -p 3000:3000 trading-bot-frontend
```

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Contributing

1. Follow the existing code style
2. Use ESLint and Prettier for formatting
3. Write meaningful component names and comments
4. Test on multiple browsers before submitting