import { useState } from 'react';
import './TripForm.css';

// Used both for the client-side check below and to keep the label
// text in sync with the actual backend rule (70-hour/8-day cycle),
// instead of a random number nobody could trace back to why it's there.
const MAX_CYCLE_HOURS = 70;

/**
 * TripForm
 *
 * The only screen the driver actually interacts with directly.
 * Everything else in the app (map, log sheets) just displays whatever
 * comes back once this is submitted. Its two jobs: collect the 4
 * required inputs, and catch obviously-bad input before it ever
 * reaches the backend - there's no point spending a network round
 * trip telling someone they forgot to type a pickup address.
 */
export default function TripForm({ onSubmit, loading }) {
  const [formData, setFormData] = useState({
    current_location: '',
    pickup_location: '',
    dropoff_location: '',
    cycle_hours_used: '',
  });

  // Field-level error messages, keyed the same way as formData, so we
  // can point at the exact field that's wrong instead of one vague
  // banner sitting at the top of the form.
  const [errors, setErrors] = useState({});

  const handleChange = (field) => (event) => {
    setFormData((prev) => ({ ...prev, [field]: event.target.value }));
  };

  const validate = () => {
    const newErrors = {};

    if (!formData.current_location.trim()) {
      newErrors.current_location = 'Enter where the driver is starting from.';
    }
    if (!formData.pickup_location.trim()) {
      newErrors.pickup_location = 'Enter the pickup location.';
    }
    if (!formData.dropoff_location.trim()) {
      newErrors.dropoff_location = 'Enter the dropoff location.';
    }

    const cycleHours = Number(formData.cycle_hours_used);
    if (formData.cycle_hours_used === '' || Number.isNaN(cycleHours)) {
      newErrors.cycle_hours_used = 'Enter the hours already used this cycle.';
    } else if (cycleHours < 0 || cycleHours > MAX_CYCLE_HOURS) {
      newErrors.cycle_hours_used = `Must be between 0 and ${MAX_CYCLE_HOURS}.`;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!validate()) return;

    // The backend serializer (Module 3) expects cycle_hours_used as a
    // real number, not the string every text input naturally
    // produces - convert it right here at the boundary, once.
    onSubmit({
      ...formData,
      cycle_hours_used: Number(formData.cycle_hours_used),
    });
  };

  return (
    <form className="trip-form" onSubmit={handleSubmit}>
      <div className="trip-form-grid">
        <Field
          label="Current Location"
          value={formData.current_location}
          onChange={handleChange('current_location')}
          error={errors.current_location}
          placeholder="e.g. Chicago, IL"
        />
        <Field
          label="Pickup Location"
          value={formData.pickup_location}
          onChange={handleChange('pickup_location')}
          error={errors.pickup_location}
          placeholder="e.g. Indianapolis, IN"
        />
        <Field
          label="Dropoff Location"
          value={formData.dropoff_location}
          onChange={handleChange('dropoff_location')}
          error={errors.dropoff_location}
          placeholder="e.g. Louisville, KY"
        />
        <Field
          label="Current Cycle Used (Hrs)"
          value={formData.cycle_hours_used}
          onChange={handleChange('cycle_hours_used')}
          error={errors.cycle_hours_used}
          placeholder="e.g. 10"
          type="number"
          min={0}
          max={MAX_CYCLE_HOURS}
          step="0.5"
        />
      </div>

      <button type="submit" className="trip-form-submit" disabled={loading}>
        {loading ? 'Planning trip…' : 'Plan Trip'}
      </button>
    </form>
  );
}

/**
 * Field
 *
 * One labeled input, split out into its own tiny component purely so
 * TripForm's markup above stays readable - four of these written
 * inline would bury the actual form layout under repeated boilerplate.
 */
function Field({ label, error, ...inputProps }) {
  return (
    <label className="trip-form-field">
      <span className="trip-form-label">{label}</span>
      <input className={`trip-form-input ${error ? 'has-error' : ''}`} {...inputProps} />
      {error && <span className="trip-form-error">{error}</span>}
    </label>
  );
}