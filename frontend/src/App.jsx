import { useState } from 'react';
import TripForm from './components/TripForm';
import MapView from './components/MapView';
import LogSheet from './components/LogSheet';
import { planTrip } from './api/planTrip';
import './App.css';

function App() {
  const [tripPlan, setTripPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handlePlanTrip = async (formData) => {
    setLoading(true);
    setError(null);
    setTripPlan(null);

    try {
      const result = await planTrip(formData);
      setTripPlan(result);
    } catch (err) {
      setError(err.message || 'Something went wrong while planning the trip.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>ELD Trip Planner</h1>
        <p>Plan a trip and generate compliant daily logs</p>
      </header>

      <TripForm onSubmit={handlePlanTrip} loading={loading} />

      {error && <div className="error-banner">{error}</div>}

      {tripPlan && (
        <div className="results">
          <MapView route={tripPlan.route} stops={tripPlan.stops} />
          <div className="log-sheets">
            {tripPlan.daily_logs.map((log, index) => (
              <LogSheet key={log.date || index} log={log} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;