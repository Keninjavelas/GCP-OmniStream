/**
 * Situational Awareness Stream for GCP-OmniStream
 * Real-time WebSocket stream for helmet telemetry visualization
 */

const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const { Firestore } = require('@google-cloud/firestore');

// Environment variables
const PORT = process.env.PORT || 8080;
const FIRESTORE_PROJECT = process.env.FIRESTORE_PROJECT || 'omnistream-dev';
const ENVIRONMENT = process.env.ENVIRONMENT || 'dev';

// Initialize Express and HTTP server
const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST']
  }
});

// Initialize Firestore
const firestore = new Firestore({
  projectId: FIRESTORE_PROJECT,
  timestampsInSnapshots: true
});

// In-memory cache for recent telemetry
const telemetryCache = new Map();
const MAX_CACHE_SIZE = 1000;

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    environment: ENVIRONMENT,
    timestamp: new Date().toISOString()
  });
});

// Get recent telemetry for a helmet
app.get('/api/helmet/:helmetId', async (req, res) => {
  try {
    const { helmetId } = req.params;
    const helmetRef = firestore.collection('helmet_telemetry').doc(helmetId);
    const doc = await helmetRef.get();
    
    if (!doc.exists) {
      return res.status(404).json({ error: 'Helmet not found' });
    }
    
    res.json({
      helmetId: helmetId,
      lastTelemetry: doc.data(),
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error fetching helmet telemetry:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get all active helmets
app.get('/api/helmets', async (req, res) => {
  try {
    const helmetsRef = firestore.collection('helmet_telemetry');
    const snapshot = await helmetsRef.limit(100).get();
    
    const helmets = [];
    snapshot.forEach((doc) => {
      helmets.push({
        helmetId: doc.id,
        ...doc.data()
      });
    });
    
    res.json({
      helmets,
      count: helmets.length,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error fetching helmets:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// WebSocket connection handler
io.on('connection', (socket) => {
  console.log(`Client connected: ${socket.id}`);
  
  // Subscribe to telemetry updates
  socket.on('subscribe:helmet', (helmetId) => {
    socket.join(`helmet:${helmetId}`);
    console.log(`Client ${socket.id} subscribed to helmet: ${helmetId}`);
    
    // Send cached telemetry immediately
    const cached = telemetryCache.get(helmetId);
    if (cached) {
      socket.emit('telemetry:update', cached);
    }
  });
  
  socket.on('subscribe:all', () => {
    console.log(`Client ${socket.id} subscribed to all telemetry`);
  });
  
  socket.on('disconnect', () => {
    console.log(`Client disconnected: ${socket.id}`);
  });
});

// Export function for Cloud Functions
const processTelemetry = async (data) => {
  const helmetId = data.helmetId || data.helmet_id;
  const telemetryData = {
    ...data,
    timestamp: new Date().toISOString(),
    lastUpdated: new Date().toISOString()
  };
  
  // Update Firestore
  const helmetRef = firestore.collection('helmet_telemetry').doc(helmetId);
  await helmetRef.set(telemetryData, { merge: true });
  
  // Update cache
  telemetryCache.set(helmetId, telemetryData);
  if (telemetryCache.size > MAX_CACHE_SIZE) {
    const firstKey = telemetryCache.keys().next().value;
    telemetryCache.delete(firstKey);
  }
  
  // Emit to WebSocket clients
  io.to(`helmet:${helmetId}`).emit('telemetry:update', telemetryData);
  io.emit('telemetry:global', telemetryData);
  
  console.log(`Processed telemetry for helmet: ${helmetId}`);
};

// Start server
if (require.main === module) {
  server.listen(PORT, () => {
    console.log(`Situational Awareness Stream running on port ${PORT}`);
    console.log(`Environment: ${ENVIRONMENT}`);
  });
}

module.exports = { app, server, processTelemetry };
