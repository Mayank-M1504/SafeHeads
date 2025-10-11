import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, 
  Square, 
  Eye, 
  EyeOff, 
  Settings, 
  Camera,
  Wifi,
  WifiOff,
  AlertCircle,
  Upload,
  Pause,
  RotateCcw,
  BarChart3,
  Activity,
  Shield,
  Users,
  Clock,
  Zap,
  Database,
  Search,
  Filter,
  Download,
  Trash2,
  CheckCircle,
  XCircle,
  Calendar,
  MapPin,
  Car,
  Image as ImageIcon,
  RefreshCw,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000';
const VIOLATIONS_API_URL = 'http://localhost:5001';

// Loading Spinner Component
const LoadingSpinner = ({ size = 20, color = '#4ecdc4' }) => (
  <div className="loading-spinner" style={{ width: size, height: size, borderColor: color }}>
    <div></div>
    <div></div>
    <div></div>
    <div></div>
  </div>
);

// Loading Overlay Component
const LoadingOverlay = ({ message = 'Loading...' }) => (
  <div className="loading-overlay">
    <div className="loading-content">
      <LoadingSpinner size={40} />
      <p>{message}</p>
    </div>
  </div>
);

// Stats Card Component
const StatsCard = ({ icon: Icon, title, value, subtitle, color = '#4ecdc4', loading = false }) => (
  <div className="stats-card" style={{ '--accent-color': color }}>
    <div className="stats-icon">
      {loading ? <LoadingSpinner size={24} color={color} /> : <Icon size={24} />}
    </div>
    <div className="stats-content">
      <h3>{title}</h3>
      <div className="stats-value">{value}</div>
      {subtitle && <div className="stats-subtitle">{subtitle}</div>}
    </div>
  </div>
);

function App() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [detectionEnabled, setDetectionEnabled] = useState(true);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.4);
  const [serverStatus, setServerStatus] = useState('offline');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Video file controls
  const [sourceType, setSourceType] = useState('camera');
  const [videoFile, setVideoFile] = useState(null);
  const [videoInfo, setVideoInfo] = useState(null);
  const [isPaused, setIsPaused] = useState(false);
  
  // Real-time stats
  const [stats, setStats] = useState({
    totalVehicles: 0,
    totalViolations: 0,
    totalCrops: 0,
    currentFPS: 0,
    uptime: 0,
    memoryUsage: 0
  });
  
  // Helmet detection state
  const [helmetInfo, setHelmetInfo] = useState(null);
  const [violations, setViolations] = useState([]);
  const [violationImages, setViolationImages] = useState([]);
  
  // Database violations state
  const [dbViolations, setDbViolations] = useState([]);
  const [violationsLoading, setViolationsLoading] = useState(false);
  const [violationsPagination, setViolationsPagination] = useState({
    page: 1,
    pages: 1,
    per_page: 20,
    total: 0,
    has_next: false,
    has_prev: false
  });
  const [violationsFilter, setViolationsFilter] = useState({
    status: '',
    number_plate: '',
    search: ''
  });
  const [violationsStats, setViolationsStats] = useState({
    total_violations: 0,
    active_violations: 0,
    resolved_violations: 0,
    dismissed_violations: 0,
    recent_violations_24h: 0,
    violations_by_type: {}
  });
  const [showViolationsSection, setShowViolationsSection] = useState(false);
  
  const videoRef = useRef(null);
  const helmetVideoRef = useRef(null);
  const statusCheckInterval = useRef(null);
  const statsInterval = useRef(null);
  const imagesInterval = useRef(null);

  // Check server status periodically
  useEffect(() => {
    checkServerStatus();
    statusCheckInterval.current = setInterval(checkServerStatus, 5000);
    statsInterval.current = setInterval(updateStats, 2000);
    imagesInterval.current = setInterval(fetchViolationImages, 10000); // Refresh images every 10 seconds
    
    // Fetch violation images on component mount
    fetchViolationImages();
    
    return () => {
      if (statusCheckInterval.current) clearInterval(statusCheckInterval.current);
      if (statsInterval.current) clearInterval(statsInterval.current);
      if (imagesInterval.current) clearInterval(imagesInterval.current);
    };
  }, []);

  const checkServerStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/status`, { timeout: 3000 });
      setServerStatus('online');
      setIsStreaming(response.data.is_streaming);
      setDetectionEnabled(response.data.detection_enabled);
      setConfidenceThreshold(response.data.confidence_threshold);
      setVideoInfo(response.data.video_info);
      setHelmetInfo(response.data.helmet_detection);
      setError('');
    } catch (err) {
      setServerStatus('offline');
      setError('Cannot connect to server. Make sure the backend is running on port 5000.');
    }
  };

  const updateStats = async () => {
    try {
      const [statusRes, cropsRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/status`),
        axios.get(`${API_BASE_URL}/crop_info`)
      ]);
      
      const status = statusRes.data;
      const crops = cropsRes.data;
      
      // Try to get violations from the violations API, but don't fail if it's not available
      let violationsCount = 0;
      try {
        const violationsRes = await axios.get(`${VIOLATIONS_API_URL}/api/violations/stats`, { timeout: 2000 });
        if (violationsRes.data.success) {
          violationsCount = violationsRes.data.stats.total_violations || 0;
        }
      } catch (err) {
        // Violations API not available, use 0
        console.log('Violations API not available, using 0 for violations count');
      }
      
      setStats({
        totalVehicles: crops.total_files || 0,
        totalViolations: violationsCount,
        totalCrops: crops.total_files || 0,
        currentFPS: status.video_info?.fps || 0,
        uptime: Date.now() - (status.video_info?.timestamp || Date.now()),
        memoryUsage: status.device_info?.gpu_memory_allocated || 0
      });
      
      // Note: Violation images are now handled by the violations API
      // The main backend no longer provides violation data
    } catch (err) {
      // Silently fail for stats updates
    }
  };

  const fetchViolationImages = async () => {
    console.log('🖼️ Fetching violation images...');
    try {
      // Try to get violations from the violations API
      const response = await axios.get(`${VIOLATIONS_API_URL}/api/violations?per_page=50`, { timeout: 2000 });
      console.log('📡 Violations API response:', response.data);
      
      if (response.data.success) {
        // Convert violations to image objects for backward compatibility
        const images = response.data.violations.map(violation => ({
          filename: violation.crop_filename || 'unknown',
          created: new Date(violation.violation_timestamp).getTime() / 1000,
          image_url: violation.image_url,
          number_plate: violation.number_plate
        }));
        console.log('🖼️ Processed images:', images);
        setViolationImages(images);
      }
    } catch (err) {
      // Silently fail for violation images
      console.log('❌ Violations API not available for images:', err.message);
    }
  };

  const startStream = async () => {
    setLoading(true);
    setError('');
    
    try {
      const payload = {
        source_type: sourceType,
        source: sourceType === 'camera' ? 0 : videoFile
      };
      
      const response = await axios.post(`${API_BASE_URL}/start_stream`, payload);
      
      if (response.data.success) {
        setIsStreaming(true);
        setVideoInfo(response.data.video_info);
        // Force refresh the video streams
        if (videoRef.current) {
          videoRef.current.src = `${API_BASE_URL}/video_feed?t=${Date.now()}`;
        }
      } else {
        setError(response.data.message || 'Failed to start stream');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to start stream');
    } finally {
      setLoading(false);
    }
  };

  const stopStream = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post(`${API_BASE_URL}/stop_stream`);
      
      if (response.data.success) {
        setIsStreaming(false);
        if (videoRef.current) {
          videoRef.current.src = '';
        }
      } else {
        setError(response.data.message || 'Failed to stop stream');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to stop stream');
    } finally {
      setLoading(false);
    }
  };

  const toggleDetection = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post(`${API_BASE_URL}/toggle_detection`);
      
      if (response.data.success) {
        setDetectionEnabled(response.data.detection_enabled);
      } else {
        setError(response.data.message || 'Failed to toggle detection');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to toggle detection');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('video', file);

      const response = await axios.post(`${API_BASE_URL}/upload_video`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 600000, // 10 minutes timeout for very large files
      });

      if (response.data.success) {
        setVideoFile(response.data.filepath);
        setSourceType('video');
        setError('');
      } else {
        setError(response.data.message || 'Failed to upload video');
      }
    } catch (err) {
      if (err.code === 'ECONNABORTED') {
        setError('Upload timeout. The file is very large or the connection is slow. Please try again or check your internet connection.');
      } else {
        setError(err.response?.data?.message || 'Failed to upload video');
      }
    } finally {
      setLoading(false);
    }
  };

  const pauseVideo = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/pause_video`);
      if (response.data.success) {
        setIsPaused(true);
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to pause video');
    }
  };

  const resumeVideo = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/resume_video`);
      if (response.data.success) {
        setIsPaused(false);
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to resume video');
    }
  };

  const seekVideo = async (frameNumber) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/seek_video`, {
        frame: frameNumber
      });
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to seek video');
    }
  };

  const updateConfidence = async (threshold) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/set_confidence`, {
        threshold: threshold
      });
      
      if (response.data.success) {
        setConfidenceThreshold(threshold);
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to update confidence');
    }
  };

  // Database violations functions
  const fetchDbViolations = async (page = 1, filters = {}) => {
    setViolationsLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: violationsPagination.per_page.toString(),
        ...filters
      });
      
      const response = await axios.get(`${VIOLATIONS_API_URL}/api/violations?${params}`);
      
      if (response.data.success) {
        setDbViolations(response.data.violations);
        setViolationsPagination(response.data.pagination);
      } else {
        setError(response.data.message || 'Failed to fetch violations');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to fetch violations');
    } finally {
      setViolationsLoading(false);
    }
  };

  const fetchViolationsStats = async () => {
    try {
      const response = await axios.get(`${VIOLATIONS_API_URL}/api/violations/stats`);
      if (response.data.success) {
        setViolationsStats(response.data.stats);
      }
    } catch (err) {
      console.error('Failed to fetch violations stats:', err);
    }
  };

  const updateViolationStatus = async (numberPlate, status) => {
    try {
      const response = await axios.put(`${VIOLATIONS_API_URL}/api/violations/${numberPlate}`, {
        status: status
      });
      
      if (response.data.success) {
        // Refresh violations list
        fetchDbViolations(violationsPagination.page, violationsFilter);
        fetchViolationsStats();
        setError('');
      } else {
        setError(response.data.message || 'Failed to update violation status');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to update violation status');
    }
  };

  const deleteViolation = async (numberPlate) => {
    if (!window.confirm('Are you sure you want to delete this violation? This action cannot be undone.')) {
      return;
    }
    
    try {
      const response = await axios.delete(`${VIOLATIONS_API_URL}/api/violations/${numberPlate}`);
      
      if (response.data.success) {
        // Refresh violations list
        fetchDbViolations(violationsPagination.page, violationsFilter);
        fetchViolationsStats();
        setError('');
      } else {
        setError(response.data.message || 'Failed to delete violation');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to delete violation');
    }
  };

  const exportViolations = async () => {
    try {
      const response = await axios.get(`${VIOLATIONS_API_URL}/api/violations/export`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'violations_export.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to export violations');
    }
  };

  const handleFilterChange = (key, value) => {
    const newFilter = { ...violationsFilter, [key]: value };
    setViolationsFilter(newFilter);
    fetchDbViolations(1, newFilter);
  };

  const handlePageChange = (newPage) => {
    fetchDbViolations(newPage, violationsFilter);
  };

  return (
    <div className="app">
      {/* Header Section */}
      <header className="header">
        <h1>🎥 Safehead - Vehicle & Helmet Detection</h1>
        <p>Real-time vehicle detection with automatic helmet analysis pipeline</p>
        
        {/* Status Indicator */}
        <div className="status-indicator">
          <div className={`status-dot ${serverStatus}`}></div>
          <span className="status-text">
            {serverStatus === 'online' ? (
              <>
                <Wifi size={16} style={{ marginRight: '0.5rem' }} />
                Server Online
              </>
            ) : (
              <>
                <WifiOff size={16} style={{ marginRight: '0.5rem' }} />
                Server Offline
              </>
            )}
          </span>
        </div>
      </header>

      {/* Error Display */}
      {error && (
        <div className="error-message">
          <AlertCircle size={20} />
          {error}
        </div>
      )}

      {/* Main Video Stream Section */}
      <div className="main-stream-section">
        <div className="stream-header">
          <h2>🚗 Main Detection Stream</h2>
          <div className="stream-controls">
            <div className="source-selector">
              <button
                className={`btn ${sourceType === 'camera' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setSourceType('camera')}
                disabled={isStreaming || loading}
              >
                <Camera size={16} />
                Camera
              </button>
              <button
                className={`btn ${sourceType === 'video' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setSourceType('video')}
                disabled={isStreaming || loading}
              >
                <Upload size={16} />
                Upload Video
              </button>
            </div>
            
            {sourceType === 'video' && (
              <div className="file-upload">
                <input
                  type="file"
                  accept="video/*"
                  onChange={handleFileUpload}
                  disabled={loading || isStreaming}
                  id="video-upload"
                />
                <label htmlFor="video-upload" className="upload-label">
                  {loading ? <LoadingSpinner size={16} /> : <Upload size={16} />}
                  {videoFile ? 'Change Video' : 'Select Video File'}
                </label>
                {videoFile && (
                  <div className="file-info">
                    <div className="file-name">{videoFile.split('/').pop()}</div>
                    <div className="file-size">
                      {(() => {
                        const fileInput = document.getElementById('video-upload');
                        if (fileInput && fileInput.files[0]) {
                          const size = fileInput.files[0].size;
                          return `${(size / 1024 / 1024).toFixed(1)}MB`;
                        }
                        return '';
                      })()}
                    </div>
                  </div>
                )}
              </div>
            )}
            
            <div className="stream-buttons">
              <button
                className="btn btn-primary"
                onClick={startStream}
                disabled={loading || isStreaming || serverStatus === 'offline' || (sourceType === 'video' && !videoFile)}
              >
                {loading ? <LoadingSpinner size={16} /> : <Play size={16} />}
                Start Stream
              </button>
              <button
                className="btn btn-secondary"
                onClick={stopStream}
                disabled={loading || !isStreaming || serverStatus === 'offline'}
              >
                <Square size={16} />
                Stop Stream
              </button>
            </div>
          </div>
        </div>

        <div className="video-container">
          {isStreaming ? (
            <img
              ref={videoRef}
              src={`${API_BASE_URL}/video_feed`}
              alt="Main Detection Stream"
              className="video-stream"
              onError={() => setError('Video stream error. Check camera connection.')}
            />
          ) : (
            <div className="video-placeholder">
              <Camera size={64} />
              <h3>Stream Not Active</h3>
              <p>Click "Start Stream" to begin detection</p>
            </div>
          )}
        </div>
      </div>

      {/* Helmet Detection Stream Section */}
      <div className="helmet-stream-section">
        <div className="stream-header">
          <h2>🪖 Helmet Violation Stream</h2>
          <div className="helmet-stats">
            <span className="stat-badge">
              <Shield size={16} />
              {stats.totalViolations} Violations
            </span>
            <span className="stat-badge">
              <Activity size={16} />
              {helmetInfo?.enabled ? 'Active' : 'Inactive'}
            </span>
          </div>
        </div>

        <div className="helmet-container">
          {violationImages.length > 0 ? (
            <div className="violation-gallery">
              {violationImages.slice(0, 6).map((image, index) => {
                console.log(`🖼️ Rendering image ${index}:`, image);
                return (
                  <div key={index} className="violation-item">
                    <img
                      src={image.image_url || `${API_BASE_URL}/violation/${image.filename}`}
                      alt={`Violation ${index + 1}`}
                      className="violation-image"
                      onError={(e) => {
                        console.log(`❌ Image failed to load:`, e.target.src);
                        e.target.style.display = 'none';
                      }}
                      onLoad={() => console.log(`✅ Image loaded:`, image.image_url || image.filename)}
                    />
                    <div className="violation-info">
                      <span className="violation-time">
                        {new Date(image.created * 1000).toLocaleTimeString()}
                      </span>
                      {image.number_plate && (
                        <span className="violation-plate">
                          {image.number_plate}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="helmet-placeholder">
              <Shield size={64} />
              <h3>No Violations Detected</h3>
              <p>Start the main stream to begin helmet detection</p>
              <p style={{fontSize: '0.8rem', opacity: 0.7}}>
                Images: {violationImages.length} | 
                Check console for debug info
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Video Controls Section */}
      {isStreaming && videoInfo && (
        <div className="video-controls-section">
          <h2>🎮 Video Controls</h2>
          <div className="controls-grid">
            <div className="control-group">
              <button
                className="btn btn-toggle"
                onClick={isPaused ? resumeVideo : pauseVideo}
                disabled={loading || serverStatus === 'offline'}
              >
                {isPaused ? <Play size={16} /> : <Pause size={16} />}
                {isPaused ? 'Resume' : 'Pause'}
              </button>
            </div>

            <div className="control-group">
              <button
                className="btn btn-toggle"
                onClick={toggleDetection}
                disabled={loading || serverStatus === 'offline'}
              >
                {detectionEnabled ? <Eye size={16} /> : <EyeOff size={16} />}
                {detectionEnabled ? 'Disable Detection' : 'Enable Detection'}
              </button>
            </div>

            <div className="control-group">
              <label>Confidence: {confidenceThreshold.toFixed(2)}</label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={confidenceThreshold}
                onChange={(e) => updateConfidence(parseFloat(e.target.value))}
                className="slider"
                disabled={serverStatus === 'offline'}
              />
            </div>

            {videoInfo.source_type === 'video' && (
              <div className="control-group">
                <label>Frame: {videoInfo.current_frame || 0} / {videoInfo.total_frames || 0}</label>
                <input
                  type="range"
                  min="0"
                  max={videoInfo.total_frames || 0}
                  value={videoInfo.current_frame || 0}
                  onChange={(e) => seekVideo(parseInt(e.target.value))}
                  className="slider"
                  disabled={serverStatus === 'offline'}
                />
                <div className="video-info">
                  Duration: {Math.round(videoInfo.duration_seconds || 0)}s | 
                  FPS: {(videoInfo.fps || 0).toFixed(1)}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Real Statistics Section */}
      <div className="stats-section">
        <h2>📊 Real-Time Statistics</h2>
        <div className="stats-grid">
          <StatsCard
            icon={Users}
            title="Vehicles Detected"
            value={stats.totalVehicles}
            subtitle="Total crops saved"
            color="#4ecdc4"
            loading={loading}
          />
          <StatsCard
            icon={Shield}
            title="Helmet Violations"
            value={stats.totalViolations}
            subtitle="No helmet detected"
            color="#ff6b6b"
            loading={loading}
          />
          <StatsCard
            icon={Activity}
            title="Current FPS"
            value={stats.currentFPS.toFixed(1)}
            subtitle="Frames per second"
            color="#ffa726"
            loading={loading}
          />
          <StatsCard
            icon={Clock}
            title="Uptime"
            value={Math.floor(stats.uptime / 1000 / 60)}
            subtitle="Minutes running"
            color="#9c27b0"
            loading={loading}
          />
          <StatsCard
            icon={Zap}
            title="Memory Usage"
            value={`${stats.memoryUsage.toFixed(1)}GB`}
            subtitle="GPU memory"
            color="#00bcd4"
            loading={loading}
          />
          <StatsCard
            icon={BarChart3}
            title="Detection Rate"
            value={detectionEnabled ? '100%' : '0%'}
            subtitle="Detection active"
            color={detectionEnabled ? '#4caf50' : '#f44336'}
            loading={loading}
          />
        </div>
      </div>

      {/* Database Violations Management Section */}
      <div className="violations-section">
        <div className="violations-header">
          <h2>🗄️ Database Violations Management</h2>
          <div className="violations-controls">
            <button
              className="btn btn-primary"
              onClick={() => {
                setShowViolationsSection(!showViolationsSection);
                if (!showViolationsSection) {
                  fetchDbViolations();
                  fetchViolationsStats();
                }
              }}
            >
              <Database size={16} />
              {showViolationsSection ? 'Hide Violations' : 'View Violations'}
            </button>
            {showViolationsSection && (
              <button
                className="btn btn-secondary"
                onClick={exportViolations}
                disabled={violationsLoading}
              >
                <Download size={16} />
                Export CSV
              </button>
            )}
          </div>
        </div>

        {showViolationsSection && (
          <>
            {/* Violations Statistics */}
            <div className="violations-stats">
              <div className="violation-stat-card">
                <div className="stat-icon">
                  <Shield size={20} />
                </div>
                <div className="stat-content">
                  <div className="stat-value">{violationsStats.total_violations}</div>
                  <div className="stat-label">Total Violations</div>
                </div>
              </div>
              <div className="violation-stat-card">
                <div className="stat-icon active">
                  <Activity size={20} />
                </div>
                <div className="stat-content">
                  <div className="stat-value">{violationsStats.active_violations}</div>
                  <div className="stat-label">Active</div>
                </div>
              </div>
              <div className="violation-stat-card">
                <div className="stat-icon resolved">
                  <CheckCircle size={20} />
                </div>
                <div className="stat-content">
                  <div className="stat-value">{violationsStats.resolved_violations}</div>
                  <div className="stat-label">Resolved</div>
                </div>
              </div>
              <div className="violation-stat-card">
                <div className="stat-icon dismissed">
                  <XCircle size={20} />
                </div>
                <div className="stat-content">
                  <div className="stat-value">{violationsStats.dismissed_violations}</div>
                  <div className="stat-label">Dismissed</div>
                </div>
              </div>
              <div className="violation-stat-card">
                <div className="stat-icon recent">
                  <Clock size={20} />
                </div>
                <div className="stat-content">
                  <div className="stat-value">{violationsStats.recent_violations_24h}</div>
                  <div className="stat-label">Last 24h</div>
                </div>
              </div>
            </div>

            {/* Filters */}
            <div className="violations-filters">
              <div className="filter-group">
                <Search size={16} />
                <input
                  type="text"
                  placeholder="Search by number plate..."
                  value={violationsFilter.search}
                  onChange={(e) => handleFilterChange('search', e.target.value)}
                  className="filter-input"
                />
              </div>
              <div className="filter-group">
                <Filter size={16} />
                <select
                  value={violationsFilter.status}
                  onChange={(e) => handleFilterChange('status', e.target.value)}
                  className="filter-select"
                >
                  <option value="">All Status</option>
                  <option value="active">Active</option>
                  <option value="resolved">Resolved</option>
                  <option value="dismissed">Dismissed</option>
                </select>
              </div>
              <button
                className="btn btn-toggle"
                onClick={() => fetchDbViolations(violationsPagination.page, violationsFilter)}
                disabled={violationsLoading}
              >
                <RefreshCw size={16} />
                Refresh
              </button>
            </div>

            {/* Violations Table */}
            <div className="violations-table-container">
              {violationsLoading ? (
                <div className="loading-container">
                  <LoadingSpinner size={40} />
                  <p>Loading violations...</p>
                </div>
              ) : dbViolations.length > 0 ? (
                <div className="violations-table">
                  <div className="table-header">
                    <div className="table-cell">Number Plate</div>
                    <div className="table-cell">Type</div>
                    <div className="table-cell">Timestamp</div>
                    <div className="table-cell">Status</div>
                    <div className="table-cell">Confidence</div>
                    <div className="table-cell">Location</div>
                    <div className="table-cell">Actions</div>
                  </div>
                  {dbViolations.map((violation) => (
                    <div key={violation.number_plate} className="table-row">
                      <div className="table-cell">
                        <div className="number-plate">
                          <Car size={16} />
                          {violation.number_plate}
                        </div>
                      </div>
                      <div className="table-cell">
                        <span className="violation-type">
                          {violation.violation_type.replace('_', ' ').toUpperCase()}
                        </span>
                      </div>
                      <div className="table-cell">
                        <div className="timestamp">
                          <Calendar size={14} />
                          {new Date(violation.violation_timestamp).toLocaleString()}
                        </div>
                      </div>
                      <div className="table-cell">
                        <span className={`status-badge ${violation.status}`}>
                          {violation.status}
                        </span>
                      </div>
                      <div className="table-cell">
                        <div className="confidence">
                          {(violation.confidence_score * 100).toFixed(1)}%
                        </div>
                      </div>
                      <div className="table-cell">
                        <div className="location">
                          <MapPin size={14} />
                          {violation.location || 'Unknown'}
                        </div>
                      </div>
                      <div className="table-cell">
                        <div className="actions">
                          {violation.image_url ? (
                            <button
                              className="action-btn view"
                              onClick={() => {
                                console.log('Opening image URL:', violation.image_url);
                                window.open(violation.image_url, '_blank');
                              }}
                              title="View Image"
                            >
                              <ImageIcon size={14} />
                            </button>
                          ) : (
                            <span className="no-image" title="No image available">
                              <ImageIcon size={14} style={{opacity: 0.3}} />
                            </span>
                          )}
                          {violation.status !== 'resolved' && (
                            <button
                              className="action-btn resolve"
                              onClick={() => updateViolationStatus(violation.number_plate, 'resolved')}
                              title="Mark as Resolved"
                            >
                              <CheckCircle size={14} />
                            </button>
                          )}
                          {violation.status !== 'dismissed' && (
                            <button
                              className="action-btn dismiss"
                              onClick={() => updateViolationStatus(violation.number_plate, 'dismissed')}
                              title="Dismiss"
                            >
                              <XCircle size={14} />
                            </button>
                          )}
                          <button
                            className="action-btn delete"
                            onClick={() => deleteViolation(violation.number_plate)}
                            title="Delete"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="no-violations">
                  <Database size={64} />
                  <h3>No Violations Found</h3>
                  <p>No violations match your current filters</p>
                </div>
              )}
            </div>

            {/* Pagination */}
            {violationsPagination.pages > 1 && (
              <div className="pagination">
                <button
                  className="btn btn-secondary"
                  onClick={() => handlePageChange(violationsPagination.page - 1)}
                  disabled={!violationsPagination.has_prev || violationsLoading}
                >
                  <ChevronLeft size={16} />
                  Previous
                </button>
                <div className="pagination-info">
                  Page {violationsPagination.page} of {violationsPagination.pages}
                  <span className="total-items">
                    ({violationsPagination.total} total)
                  </span>
                </div>
                <button
                  className="btn btn-secondary"
                  onClick={() => handlePageChange(violationsPagination.page + 1)}
                  disabled={!violationsPagination.has_next || violationsLoading}
                >
                  Next
                  <ChevronRight size={16} />
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Loading Overlay */}
      {loading && <LoadingOverlay message="Processing..." />}
    </div>
  );
}

export default App;