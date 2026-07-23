export async function planTrip(formData) {
  const res = await fetch('http://127.0.0.1:8000/api/plan-trip/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(formData),
  });
  if (!res.ok) throw new Error('Failed to plan trip');
  return res.json();
}