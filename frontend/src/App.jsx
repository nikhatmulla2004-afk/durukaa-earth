import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import mapboxgl from 'mapbox-gl';
import MapboxDraw from '@mapbox/mapbox-gl-draw';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

// Paste your Mapbox public token here
mapboxgl.accessToken = 'YOUR_MAPBOX_PUBLIC_TOKEN_HERE';

const API_BASE = 'http://127.0.0.1:8000';

export default function App() {
  const [token, setToken] = useState(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [newProjectName, setNewProjectName] = useState('');
  
  const mapContainer = useRef(null);
  const map = useRef(null);
  const draw = useRef(null);

  // Login handler
  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post(`${API_BASE}/auth/login`, { email, password });
      setToken(res.data.access_token);
      loadProjects();
    } catch {
      // Auto register if account not found
      await axios.post(`${API_BASE}/auth/register`, { email, password });
      const res = await axios.post(`${API_BASE}/auth/login`, { email, password });
      setToken(res.data.access_token);
      loadProjects();
    }
  };

  const loadProjects = async () => {
    const res = await axios.get(`${API_BASE}/projects`);
    setProjects(res.data);
  };

  const handleCreateProject = async () => {
    if (!newProjectName) return;
    await axios.post(`${API_BASE}/projects`, { name: newProjectName, description: 'Nature restoration project' });
    setNewProjectName('');
    loadProjects();
  };

  // Mapbox setup
  useEffect(() => {
    if (!token || map.current) return;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/satellite-streets-v12',
      center: [78.9629, 20.5937],
      zoom: 4
    });

    draw.current = new MapboxDraw({
      displayControlsDefault: false,
      controls: { polygon: true, trash: true }
    });
    map.current.addControl(draw.current);

    map.current.on('draw.create', async (e) => {
      const polygon = e.features[0].geometry;
      if (selectedProject) {
        await axios.post(`${API_BASE}/sites`, {
          project_id: selectedProject.id,
          name: `Site ${Date.now()}`,
          geometry: polygon
        });
        alert('Site polygon saved to project!');
      } else {
        alert('Select a project from the left panel first to attach this site!');
      }
    });
  }, [token, selectedProject]);

  const loadAnalytics = async (projectId) => {
    const res = await axios.get(`${API_BASE}/sites/${projectId}/analytics`);
    setAnalytics(res.data);
  };

  if (!token) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#f4f6f8' }}>
        <form onSubmit={handleLogin} style={{ background: '#fff', padding: '2rem', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)', width: '320px' }}>
          <h2 style={{ margin: '0 0 1rem' }}>Darukaa.Earth Login</h2>
          <input style={{ width: '100%', padding: '8px', marginBottom: '10px' }} placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required />
          <input style={{ width: '100%', padding: '8px', marginBottom: '15px' }} type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required />
          <button style={{ width: '100%', padding: '10px', background: '#10b981', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }} type="submit">Sign In / Register</button>
        </form>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'sans-serif' }}>
      {/* Left Sidebar */}
      <div style={{ width: '320px', borderRight: '1px solid #e5e7eb', padding: '1.5rem', overflowY: 'auto' }}>
        <h3 style={{ marginTop: 0 }}>Darukaa.Earth</h3>
        <div style={{ marginBottom: '1.5rem' }}>
          <input
            style={{ width: '65%', padding: '6px' }}
            placeholder="New Project Name"
            value={newProjectName}
            onChange={e => setNewProjectName(e.target.value)}
          />
          <button style={{ padding: '6px 10px', marginLeft: '6px' }} onClick={handleCreateProject}>Add</button>
        </div>

        <h4>Projects</h4>
        {projects.map(p => (
          <div
            key={p.id}
            onClick={() => { setSelectedProject(p); loadAnalytics(p.id); }}
            style={{
              padding: '10px',
              borderRadius: '6px',
              cursor: 'pointer',
              background: selectedProject?.id === p.id ? '#e0f2fe' : '#f9fafb',
              marginBottom: '8px'
            }}
          >
            <strong>{p.name}</strong>
            <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#6b7280' }}>{p.description}</p>
          </div>
        ))}
      </div>

      {/* Main Panel */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Map Container */}
        <div style={{ flex: 1, position: 'relative' }}>
          <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />
        </div>

        {/* Analytics Container */}
        <div style={{ height: '240px', borderTop: '1px solid #e5e7eb', padding: '1rem', background: '#fff' }}>
          {analytics ? (
            <Line
              data={{
                labels: analytics.labels,
                datasets: [
                  { label: 'Carbon Offset (Tons)', data: analytics.carbon_tons, borderColor: '#10b981', tension: 0.3 },
                  { label: 'Biodiversity Score', data: analytics.biodiversity_score, borderColor: '#3b82f6', tension: 0.3 }
                ]
              }}
              options={{ maintainAspectRatio: false }}
            />
          ) : (
            <p style={{ color: '#6b7280' }}>Select a project from the left panel to display performance analytics.</p>
          )}
        </div>
      </div>
    </div>
  );
}
