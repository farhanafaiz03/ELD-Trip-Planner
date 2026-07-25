
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api';

export async function planTrip(formData) {
  const res = await fetch(`${API_BASE_URL}/plan-trip/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(formData),
  });

  if (!res.ok) {
    
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || 'Failed to plan trip. Please try again.');
  }

  return res.json();
}