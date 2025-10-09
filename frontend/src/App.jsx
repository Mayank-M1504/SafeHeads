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
  AlertCircle
} from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000';

function App() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [detectionEnabled, setDetectionEnabled] = useState(true);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.4);
  const [detectionMode, setDetectionMode] = useState('vehicle');
  const [vehicleClasses, setVehicleClasses] = useState([0]);
  const [cameraIndex, setCameraIndex] = useState(0);
  const [serverStatus, setServerStatus] = useState('offline');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [modelsLoaded, setModelsLoaded] = useState({});
  
  // Video file controls
  const [sourceType, setSourceType] = useState('camera'); // 'camera' or 'video'
  const [videoFile, setVideoFile] = useState(null);
  const [videoInfo, setVideoInfo] = useState(null);
  const [isPaused, setIsPaused] = useState(false);
  
  // Device information
  const [deviceInfo, setDeviceInfo] = useState(null);
  
  // Crop information
  const [cropInfo, setCropInfo] = useState(null);
  
  // Gemini analysis state
  const [geminiInfo, setGeminiInfo] = useState(null);
  const [geminiResults, setGeminiResults] = useState([]);
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);
  
  // Helmet detection state
  const [helmetInfo, setHelmetInfo] = useState(null);
  const [helmetResults, setHelmetResults] = useState([]);
  
  // Violation state
  const [violationInfo, setViolationInfo] = useState(null);
  const [violations, setViolations] = useState([]);
  
  const videoRef = useRef(null);
  const helmetVideoRef = useRef(null);
  const statusCheckInterval = useRef(null);

  // Check server status periodically
  useEffect(() => {
    checkServerStatus();
    statusCheckInterval.current = setInterval(checkServerStatus, 5000);
    
    return () => {
      if (statusCheckInterval.current) {
        clearInterval(statusCheckInterval.current);
      }
    };
  }, []);

  const checkServerStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/status`, { timeout: 3000 });
      setServerStatus('online');
      setIsStreaming(response.data.is_streaming);
      setDetectionEnabled(response.data.detection_enabled);
      setConfidenceThreshold(response.data.confidence_threshold);
      setDetectionMode(response.data.detection_mode);
      setVehicleClasses(response.data.vehicle_classes);
      setModelsLoaded(response.data.models_loaded);
      setVideoInfo(response.data.video_info);
      setDeviceInfo(response.data.device_info);
      setCropInfo(response.data.crop_info);
      setGeminiInfo(response.data.gemini_info);
      setHelmetInfo(response.data.helmet_detection);
      setViolationInfo(response.data.violations);
      if (response.data.video_info) {
        setIsPaused(response.data.video_info.is_paused);
        setSourceType(response.data.video_info.source_type);
      }
      setError('');
    } catch (err) {
      setServerStatus('offline');
      setError('Cannot connect to server. Make sure the backend is running on port 5000.');
    }
  };

  const startStream = async () => {
    setLoading(true);
    setError('');
    
    try {
      const payload = {
        source_type: sourceType,
        source: sourceType === 'camera' ? cameraIndex : videoFile
      };
      
      const response = await axios.post(`${API_BASE_URL}/start_stream`, payload);
      
      if (response.data.success) {
        setIsStreaming(true);
        setVideoInfo(response.data.video_info);
        // Force refresh the video streams
        if (videoRef.current) {
          videoRef.current.src = `${API_BASE_URL}/video_feed?t=${Date.now()}`;
        }
        if (helmetVideoRef.current) {
          helmetVideoRef.current.src = `${API_BASE_URL}/helmet_feed?t=${Date.now()}`;
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
        if (helmetVideoRef.current) {
          helmetVideoRef.current.src = '';
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

  const updateConfidence = async (threshold) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/set_confidence`, {
        threshold: threshold
      });
      
      if (response.data.success) {
        setConfidenceThreshold(threshold);
      } else {
        setError(response.data.message || 'Failed to update confidence');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to update confidence');
    }
  };

  const updateDetectionMode = async (mode) => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post(`${API_BASE_URL}/set_detection_mode`, {
        mode: mode
      });
      
      if (response.data.success) {
        setDetectionMode(mode);
        setError('');
      } else {
        setError(response.data.message || 'Failed to update detection mode');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to update detection mode');
    } finally {
      setLoading(false);
    }
  };

  const updateVehicleClasses = async (classes) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/set_vehicle_classes`, {
        classes: classes
      });
      
      if (response.data.success) {
        setVehicleClasses(classes);
        setError('');
      } else {
        setError(response.data.message || 'Failed to update vehicle classes');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to update vehicle classes');
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
      });

      if (response.data.success) {
        setVideoFile(response.data.filepath);
        setSourceType('video');
        setError('');
      } else {
        setError(response.data.message || 'Failed to upload video');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to upload video');
    } finally {
      setLoading(false);
    }
  };

  const pauseVideo = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/pause_video`);
      if (response.data.success) {
        setIsPaused(true);
      } else {
        setError(response.data.message || 'Failed to pause video');
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
      } else {
        setError(response.data.message || 'Failed to resume video');
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
      if (response.data.success) {
        // Update video info will be handled by status check
      } else {
        setError(response.data.message || 'Failed to seek video');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to seek video');
    }
  };

  const switchDevice = async (device) => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post(`${API_BASE_URL}/switch_device`, {
        device: device
      });
      
      if (response.data.success) {
        setDeviceInfo(response.data.device_info);
        setError('');
      } else {
        setError(response.data.message || 'Failed to switch device');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to switch device');
    } finally {
      setLoading(false);
    }
  };

  const setSaveInterval = async (interval) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/set_save_interval`, {
        interval: interval
      });
      
      if (response.data.success) {
        setCropInfo(prev => ({ ...prev, save_interval: interval }));
        setError('');
      } else {
        setError(response.data.message || 'Failed to set save interval');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to set save interval');
    }
  };

  const clearCrops = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post(`${API_BASE_URL}/clear_crops`);
      
      if (response.data.success) {
        setCropInfo(prev => ({ ...prev, total_crops: 0 }));
        setError('');
      } else {
        setError(response.data.message || 'Failed to clear crops');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to clear crops');
    } finally {
      setLoading(false);
    }
  };

  const setMinCropSize = async (width, height) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/set_min_crop_size`, {
        min_width: width,
        min_height: height
      });
      
      if (response.data.success) {
        setCropInfo(prev => ({ 
          ...prev, 
          min_crop_width: width,
          min_crop_height: height 
        }));
        setError('');
      } else {
        setError(response.data.message || 'Failed to set minimum crop size');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to set minimum crop size');
    }
  };

  // Gemini analysis functions
  const toggleGeminiAnalysis = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/toggle_gemini_analysis`);
      
      if (response.data.success) {
        setGeminiInfo(prev => ({
          ...prev,
          analysis_enabled: response.data.gemini_analysis_enabled
        }));
        setError('');
      } else {
        setError(response.data.message || 'Failed to toggle Gemini analysis');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to toggle Gemini analysis');
    }
  };

  const fetchGeminiResults = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/gemini_results?limit=20`);
      
      if (response.data.success) {
        setGeminiResults(response.data.results);
        setGeminiInfo(prev => ({
          ...prev,
          total_analyses: response.data.total_analyses
        }));
        setError('');
      } else {
        setError(response.data.message || 'Failed to fetch Gemini results');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to fetch Gemini results');
    }
  };

  const analyzeImage = async (filename) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/analyze_image`, {
        filename: filename
      });
      
      if (response.data.success) {
        setSelectedAnalysis(response.data.analysis);
        // Refresh results
        fetchGeminiResults();
        setError('');
      } else {
        setError(response.data.message || 'Failed to analyze image');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to analyze image');
    }
  };

  // Helmet detection functions
  const toggleHelmetDetection = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/toggle_helmet_detection`);
      
      if (response.data.success) {
        setHelmetInfo(prev => ({
          ...prev,
          enabled: response.data.helmet_detection_enabled
        }));
        setError('');
      } else {
        setError(response.data.message || 'Failed to toggle helmet detection');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to toggle helmet detection');
    }
  };

  const fetchHelmetResults = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/helmet_results?limit=20`);
      
      if (response.data.success) {
        setHelmetResults(response.data.results);
        setHelmetInfo(prev => ({
          ...prev,
          total_results: response.data.total_results
        }));
        setError('');
      } else {
        setError(response.data.message || 'Failed to fetch helmet results');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to fetch helmet results');
    }
  };

  // Violation functions
  const fetchViolations = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/violations?limit=50`);
      
      if (response.data.success) {
        setViolations(response.data.violations);
        setViolationInfo(prev => ({
          ...prev,
          total_violations: response.data.total_violations
        }));
        setError('');
      } else {
        setError(response.data.message || 'Failed to fetch violations');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to fetch violations');
    }
  };

  const clearViolations = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post(`${API_BASE_URL}/clear_violations`);
      
      if (response.data.success) {
        setViolations([]);
        setViolationInfo(prev => ({ ...prev, total_violations: 0 }));
        setError('');
      } else {
        setError(response.data.message || 'Failed to clear violations');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to clear violations');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>🎥 Safehead - Vehicle & Helmet Detection</h1>
        <p>Real-time vehicle detection with automatic helmet analysis pipeline</p>
      </header>

      {error && (
        <div style={{ 
          background: 'rgba(255, 107, 107, 0.2)', 
          border: '1px solid rgba(255, 107, 107, 0.5)',
          borderRadius: '8px',
          padding: '1rem',
          marginBottom: '1rem',
          color: '#ff6b6b',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem'
        }}>
          <AlertCircle size={20} />
          {error}
        </div>
      )}

      <div className="dashboard" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div className="video-section" style={{ width: '100%', marginBottom: '1rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', height: '50vh' }}>
            {/* Vehicle Detection Stream */}
            <div className="video-container" style={{ width: '100%', height: '100%', overflow: 'hidden', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}>
              <div style={{ padding: '0.5rem', background: 'rgba(0,0,0,0.3)', color: 'white', fontSize: '0.9rem', fontWeight: 'bold' }}>
                🚗 Vehicle Detection Stream
              </div>
              {isStreaming ? (
                <img
                  ref={videoRef}
                  src={`${API_BASE_URL}/video_feed`}
                  alt="Vehicle Detection Stream"
                  className="video-stream"
                  style={{ width: '100%', height: 'calc(100% - 40px)', objectFit: 'contain', display: 'block', background: 'black' }}
                  onError={() => setError('Vehicle stream error. Check camera connection.')}
                />
              ) : (
                <div className="video-placeholder" style={{ height: 'calc(100% - 40px)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                  <Camera size={48} style={{ opacity: 0.5, marginBottom: '1rem' }} />
                  <div>Vehicle stream not active</div>
                  <div style={{ fontSize: '0.9rem', opacity: 0.7, marginTop: '0.5rem' }}>
                    Click "Start Stream" to begin
                  </div>
                </div>
              )}
            </div>

            {/* Helmet Detection Stream */}
            <div className="video-container" style={{ width: '100%', height: '100%', overflow: 'hidden', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}>
              <div style={{ padding: '0.5rem', background: 'rgba(0,0,0,0.3)', color: 'white', fontSize: '0.9rem', fontWeight: 'bold' }}>
                🪖 Helmet Detection Results
              </div>
              {isStreaming ? (
                <img
                  ref={helmetVideoRef}
                  src={`${API_BASE_URL}/helmet_feed`}
                  alt="Helmet Detection Stream"
                  className="video-stream"
                  style={{ width: '100%', height: 'calc(100% - 40px)', objectFit: 'contain', display: 'block', background: 'black' }}
                  onError={() => setError('Helmet stream error.')}
                />
              ) : (
                <div className="video-placeholder" style={{ height: 'calc(100% - 40px)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                  <Camera size={48} style={{ opacity: 0.5, marginBottom: '1rem' }} />
                  <div>Helmet stream not active</div>
                  <div style={{ fontSize: '0.9rem', opacity: 0.7, marginTop: '0.5rem' }}>
                    Start vehicle stream first
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="controls-section" style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '1rem' }}>
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

            <div className="control-group">
              <h3>Source Selection</h3>
              <div className="button-group">
                <button
                  className={`btn ${sourceType === 'camera' ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => setSourceType('camera')}
                  disabled={isStreaming}
                >
                  📹 Camera
                </button>
                <button
                  className={`btn ${sourceType === 'video' ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => setSourceType('video')}
                  disabled={isStreaming}
                >
                  🎬 Video File
                </button>
              </div>
              {sourceType === 'video' && (
                <div className="input-group" style={{ marginTop: '1rem' }}>
                  <label>Upload Video File</label>
                  <input
                    type="file"
                    accept="video/*"
                    onChange={handleFileUpload}
                    disabled={loading || isStreaming}
                    style={{ 
                      padding: '0.5rem',
                      border: '1px solid rgba(255, 255, 255, 0.3)',
                      borderRadius: '8px',
                      background: 'rgba(255, 255, 255, 0.1)',
                      color: 'white'
                    }}
                  />
                  {videoFile && (
                    <div style={{ fontSize: '0.8rem', color: 'rgba(255, 255, 255, 0.7)', marginTop: '0.5rem' }}>
                      Selected: {videoFile.split('/').pop()}
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="control-group">
              <h3>Stream Controls</h3>
              <div className="button-group">
                <button
                  className="btn btn-primary"
                  onClick={startStream}
                  disabled={loading || isStreaming || serverStatus === 'offline' || (sourceType === 'video' && !videoFile)}
                >
                  <Play size={16} />
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

            {sourceType === 'video' && isStreaming && videoInfo && (
              <div className="control-group">
                <h3>Video Controls</h3>
                <div className="button-group">
                  <button
                    className="btn btn-toggle"
                    onClick={isPaused ? resumeVideo : pauseVideo}
                    disabled={loading || serverStatus === 'offline'}
                  >
                    {isPaused ? <Play size={16} /> : <Square size={16} />}
                    {isPaused ? 'Resume' : 'Pause'}
                  </button>
                </div>
                <div className="slider-group" style={{ marginTop: '1rem' }}>
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
                </div>
                <div style={{ fontSize: '0.8rem', color: 'rgba(255, 255, 255, 0.7)', marginTop: '0.5rem' }}>
                  Duration: {Math.round(videoInfo.duration_seconds || 0)}s | FPS: {(videoInfo.fps || 0).toFixed(1)}
                </div>
              </div>
            )}
          </div>

          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="control-group">
              <h3>Detection Settings</h3>
              <div className="button-group">
                <button
                  className="btn btn-toggle"
                  onClick={toggleDetection}
                  disabled={loading || serverStatus === 'offline'}
                >
                  {detectionEnabled ? <Eye size={16} /> : <EyeOff size={16} />}
                  {detectionEnabled ? 'Disable Detection' : 'Enable Detection'}
                </button>
              </div>
            </div>

            <div className="control-group">
              <h3>🪖 Helmet Detection Pipeline</h3>
              {helmetInfo && (
                <div style={{ fontSize: '0.85rem', color: 'rgba(255, 255, 255, 0.8)', marginBottom: '1rem' }}>
                  <div>Status: {helmetInfo.enabled ? '🟢 Active' : '🔴 Disabled'}</div>
                  <div>Total Results: {helmetInfo.total_results || 0}</div>
                  <div>Analysis Interval: {helmetInfo.analysis_interval || 0.5}s</div>
                  <div>Results Directory: {helmetInfo.results_directory || 'helmet_results/'}</div>
                </div>
              )}
              <div className="button-group">
                <button
                  className={`btn ${helmetInfo?.enabled ? 'btn-secondary' : 'btn-primary'}`}
                  onClick={toggleHelmetDetection}
                  disabled={loading || serverStatus === 'offline'}
                >
                  {helmetInfo?.enabled ? '⏸️ Disable Helmet Detection' : '▶️ Enable Helmet Detection'}
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={fetchHelmetResults}
                  disabled={loading || serverStatus === 'offline'}
                >
                  🔄 Refresh Helmet Results
                </button>
              </div>
              {helmetResults.length > 0 && (
                <div style={{ marginTop: '1rem' }}>
                  <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem' }}>Recent Helmet Detection Results ({helmetResults.length})</h4>
                  <div style={{ maxHeight: '200px', overflowY: 'auto', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '0.5rem', backgroundColor: 'rgba(0, 0, 0, 0.2)' }}>
                    {helmetResults.map((result, index) => (
                      <div
                        key={index}
                        style={{ padding: '0.5rem', borderBottom: index < helmetResults.length - 1 ? '1px solid rgba(255, 255, 255, 0.1)' : 'none' }}
                      >
                        <div style={{ fontSize: '0.8rem', fontWeight: 'bold', marginBottom: '0.25rem' }}>
                          Vehicle ID: {result.vehicle_id || 'Unknown'} - {result.crop_file}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'rgba(255, 255, 255, 0.8)' }}>
                          Detections: {result.detections?.length || 0}
                          {result.detections?.map((det, i) => (
                            <span key={i} style={{ marginLeft: '0.5rem', color: det.class?.toLowerCase().includes('no_helmet') ? '#ff6b6b' : '#4ecdc4' }}>
                              {det.class}: {det.confidence?.toFixed(2)}
                            </span>
                          ))}
                        </div>
                        <div style={{ fontSize: '0.7rem', color: 'rgba(255, 255, 255, 0.5)', marginTop: '0.25rem' }}>
                          {new Date(result.timestamp * 1000).toLocaleString()}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="control-group">
              <h3>🚨 Helmet Violations</h3>
              {violationInfo && (
                <div style={{ fontSize: '0.85rem', color: 'rgba(255, 255, 255, 0.8)', marginBottom: '1rem' }}>
                  <div>Total Violations: <span style={{ color: '#ff6b6b', fontWeight: 'bold' }}>{violationInfo.total_violations || 0}</span></div>
                  <div>Directory: {violationInfo.violation_directory || 'violation/'}</div>
                </div>
              )}
              <div className="button-group">
                <button
                  className="btn btn-secondary"
                  onClick={fetchViolations}
                  disabled={loading || serverStatus === 'offline'}
                >
                  🔄 Refresh Violations
                </button>
                <button
                  className="btn btn-secondary"
                  onClick={clearViolations}
                  disabled={loading || serverStatus === 'offline' || !violationInfo?.total_violations}
                >
                  🗑️ Clear All Violations
                </button>
              </div>
              {violations.length > 0 && (
                <div style={{ marginTop: '1rem' }}>
                  <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem' }}>Recent Violations ({violations.length})</h4>
                  <div style={{ maxHeight: '200px', overflowY: 'auto', border: '1px solid rgba(255, 107, 107, 0.3)', borderRadius: '0.5rem', backgroundColor: 'rgba(255, 107, 107, 0.1)' }}>
                    {violations.map((violation, index) => (
                      <div
                        key={index}
                        style={{ padding: '0.5rem', borderBottom: index < violations.length - 1 ? '1px solid rgba(255, 107, 107, 0.2)' : 'none' }}
                      >
                        <div style={{ fontSize: '0.8rem', fontWeight: 'bold', marginBottom: '0.25rem', color: '#ff6b6b' }}>
                          🚨 Vehicle ID: {violation.vehicle_id || 'Unknown'}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'rgba(255, 255, 255, 0.8)' }}>
                          Violations: {violation.detections?.length || 0}
                          {violation.detections?.map((det, i) => (
                            <span key={i} style={{ marginLeft: '0.5rem', color: '#ff6b6b' }}>
                              {det.class}: {det.confidence?.toFixed(2)}
                            </span>
                          ))}
                        </div>
                        <div style={{ fontSize: '0.7rem', color: 'rgba(255, 255, 255, 0.5)', marginTop: '0.25rem' }}>
                          {new Date(violation.timestamp * 1000).toLocaleString()}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="control-group">
              <h3>Configuration</h3>
              <div className="slider-group">
                <label>Confidence Threshold: {confidenceThreshold.toFixed(2)}</label>
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
              <div className="input-group">
                <label>Camera Index</label>
                <input
                  type="number"
                  min="0"
                  max="10"
                  value={cameraIndex}
                  onChange={(e) => setCameraIndex(parseInt(e.target.value))}
                  placeholder="0"
                  disabled={isStreaming || serverStatus === 'offline'}
                />
              </div>
              <div className="input-group">
                <label>Vehicle Classes (comma separated)</label>
                <input
                  type="text"
                  value={vehicleClasses.join(', ')}
                  onChange={(e) => {
                    const classes = e.target.value.split(',').map(c => parseInt(c.trim())).filter(c => !isNaN(c));
                    setVehicleClasses(classes);
                  }}
                  onBlur={() => updateVehicleClasses(vehicleClasses)}
                  placeholder="0"
                  disabled={serverStatus === 'offline'}
                />
              </div>
            </div>
          </div>

          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="control-group">
              <h3>Device & Performance</h3>
              {deviceInfo && (
                <div style={{ fontSize: '0.85rem', color: 'rgba(255, 255, 255, 0.8)', marginBottom: '1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {deviceInfo.device === 'cpu' ? '🖥️' : '🎮'} 
                    <strong>Device: {deviceInfo.device.toUpperCase()}</strong>
                  </div>
                  {deviceInfo.cuda_available && deviceInfo.device !== 'cpu' && (
                    <>
                      <div>GPU: {deviceInfo.gpu_name}</div>
                      <div>Memory: {deviceInfo.gpu_memory_allocated?.toFixed(1)}GB / {deviceInfo.gpu_memory_total?.toFixed(1)}GB</div>
                      <div>Cached: {deviceInfo.gpu_memory_cached?.toFixed(1)}GB</div>
                    </>
                  )}
                  {deviceInfo.cuda_available && deviceInfo.device_count > 0 && (
                    <div>Available GPUs: {deviceInfo.device_count}</div>
                  )}
                </div>
              )}
              <div className="button-group">
                {deviceInfo?.cuda_available ? (
                  <>
                    <button
                      className={`btn ${deviceInfo?.device === 'cuda:0' ? 'btn-primary' : 'btn-secondary'}`}
                      onClick={() => switchDevice('cuda:0')}
                      disabled={loading || serverStatus === 'offline'}
                    >
                      🎮 Use GPU
                    </button>
                    <button
                      className={`btn ${deviceInfo?.device === 'cpu' ? 'btn-primary' : 'btn-secondary'}`}
                      onClick={() => switchDevice('cpu')}
                      disabled={loading || serverStatus === 'offline'}
                    >
                      🖥️ Use CPU
                    </button>
                  </>
                ) : (
                  <div style={{ 
                    padding: '0.75rem', 
                    background: 'rgba(255, 107, 107, 0.2)', 
                    borderRadius: '8px',
                    color: '#ff6b6b',
                    fontSize: '0.85rem'
                  }}>
                    ⚠️ GPU not available - using CPU only
                  </div>
                )}
              </div>
            </div>

            <div className="control-group">
              <h3>Auto-Save Vehicle Crops</h3>
              {cropInfo && (
                <div style={{ fontSize: '0.85rem', color: 'rgba(255, 255, 255, 0.8)', marginBottom: '1rem' }}>
                  <div>📁 Directory: cropped_images/</div>
                  <div>💾 Total Saved: {cropInfo.total_crops} images</div>
                  <div>⏱️ Save Interval: {cropInfo.save_interval}s</div>
                  <div>📏 Min Size: {cropInfo.min_crop_width}x{cropInfo.min_crop_height}px</div>
                  {cropInfo.last_save_time > 0 && (
                    <div>🕒 Last Save: {new Date(cropInfo.last_save_time * 1000).toLocaleTimeString()}</div>
                  )}
                </div>
              )}
              <div className="slider-group">
                <label>Save Interval: {cropInfo?.save_interval || 2}s</label>
                <input
                  type="range"
                  min="0.5"
                  max="10"
                  step="0.5"
                  value={cropInfo?.save_interval || 2}
                  onChange={(e) => setSaveInterval(parseFloat(e.target.value))}
                  className="slider"
                  disabled={serverStatus === 'offline'}
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '1rem' }}>
                <div className="input-group" style={{ margin: 0 }}>
                  <label style={{ fontSize: '0.8rem' }}>Min Width (px)</label>
                  <input
                    type="number"
                    min="50"
                    max="1000"
                    value={cropInfo?.min_crop_width || 135}
                    onChange={(e) => setMinCropSize(parseInt(e.target.value), cropInfo?.min_crop_height || 332)}
                    disabled={serverStatus === 'offline'}
                    style={{ padding: '0.5rem', fontSize: '0.85rem' }}
                  />
                </div>
                <div className="input-group" style={{ margin: 0 }}>
                  <label style={{ fontSize: '0.8rem' }}>Min Height (px)</label>
                  <input
                    type="number"
                    min="50"
                    max="1000"
                    value={cropInfo?.min_crop_height || 332}
                    onChange={(e) => setMinCropSize(cropInfo?.min_crop_width || 135, parseInt(e.target.value))}
                    disabled={serverStatus === 'offline'}
                    style={{ padding: '0.5rem', fontSize: '0.85rem' }}
                  />
                </div>
              </div>
              <div className="button-group" style={{ marginTop: '1rem' }}>
                <button
                  className="btn btn-secondary"
                  onClick={clearCrops}
                  disabled={loading || serverStatus === 'offline' || !cropInfo?.total_crops}
                >
                  🗑️ Clear All Crops
                </button>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'rgba(255, 255, 255, 0.6)', marginTop: '0.5rem', fontStyle: 'italic' }}>
                Vehicle detections are automatically saved every {cropInfo?.save_interval || 2} seconds when streaming.
                Only crops larger than {cropInfo?.min_crop_width || 135}x{cropInfo?.min_crop_height || 332}px are saved.
              </div>
            </div>

            {geminiInfo && (
              <div className="control-group">
                <h3>🤖 Gemini AI Analysis</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '1rem', fontSize: '0.85rem' }}>
                  <div>
                    <strong>Status:</strong> {geminiInfo.enabled ? (geminiInfo.analysis_enabled ? '🟢 Active' : '🟡 Paused') : '🔴 Not Configured'}
                  </div>
                  <div>
                    <strong>Total Analyses:</strong> {geminiInfo.total_analyses || 0}
                  </div>
                </div>
                {geminiInfo.enabled ? (
                  <>
                    <div className="button-group">
                      <button
                        className={`btn ${geminiInfo.analysis_enabled ? 'btn-secondary' : 'btn-primary'}`}
                        onClick={toggleGeminiAnalysis}
                        disabled={loading || serverStatus === 'offline'}
                      >
                        {geminiInfo.analysis_enabled ? '⏸️ Pause Analysis' : '▶️ Resume Analysis'}
                      </button>
                      <button
                        className="btn btn-secondary"
                        onClick={fetchGeminiResults}
                        disabled={loading || serverStatus === 'offline'}
                      >
                        🔄 Refresh Results
                      </button>
                    </div>
                    {geminiResults.length > 0 && (
                      <div style={{ marginTop: '1rem' }}>
                        <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem' }}>Recent Analysis Results ({geminiResults.length})</h4>
                        <div style={{ maxHeight: '300px', overflowY: 'auto', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: '0.5rem', backgroundColor: 'rgba(0, 0, 0, 0.2)' }}>
                          {geminiResults.map((result, index) => (
                            <div
                              key={index}
                              style={{ padding: '0.75rem', borderBottom: index < geminiResults.length - 1 ? '1px solid rgba(255, 255, 255, 0.1)' : 'none', cursor: 'pointer', transition: 'background-color 0.2s' }}
                              onClick={() => setSelectedAnalysis(result.analysis)}
                              onMouseEnter={(e) => e.target.style.backgroundColor = 'rgba(255, 255, 255, 0.05)'}
                              onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
                            >
                              <div style={{ fontSize: '0.8rem', fontWeight: 'bold', marginBottom: '0.25rem' }}>{result.filename}</div>
                              {result.analysis && result.analysis.vehicle_type && (
                                <div style={{ fontSize: '0.75rem', color: 'rgba(255, 255, 255, 0.8)' }}>
                                  🚗 {result.analysis.color || 'Unknown'} {result.analysis.brand || 'Unknown'} {result.analysis.vehicle_type}
                                  {result.analysis.license_plate && result.analysis.license_plate !== 'not_visible' && (
                                    <span> • 🔖 {result.analysis.license_plate}</span>
                                  )}
                                </div>
                              )}
                              {result.analysis && result.analysis.error && (
                                <div style={{ fontSize: '0.75rem', color: '#ff6b6b' }}>❌ {result.analysis.error}</div>
                              )}
                              <div style={{ fontSize: '0.7rem', color: 'rgba(255, 255, 255, 0.5)', marginTop: '0.25rem' }}>
                                {new Date(result.timestamp * 1000).toLocaleString()}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {selectedAnalysis && (
                      <div style={{ marginTop: '1rem', padding: '1rem', border: '1px solid rgba(255, 255, 255, 0.2)', borderRadius: '0.5rem', backgroundColor: 'rgba(0, 0, 0, 0.3)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                          <h4 style={{ fontSize: '0.9rem', margin: 0 }}>Analysis Details</h4>
                          <button className="btn btn-small" onClick={() => setSelectedAnalysis(null)} style={{ padding: '0.25rem 0.5rem', fontSize: '0.7rem' }}>✕ Close</button>
                        </div>
                        {selectedAnalysis.error ? (
                          <div style={{ color: '#ff6b6b', fontSize: '0.85rem' }}>Error: {selectedAnalysis.error}</div>
                        ) : (
                          <div style={{ fontSize: '0.8rem' }}>
                            {Object.entries(selectedAnalysis).filter(([key, value]) => !['analysis_timestamp', 'image_path', 'raw_response'].includes(key) && value).map(([key, value]) => (
                              <div key={key} style={{ marginBottom: '0.5rem' }}>
                                <strong style={{ textTransform: 'capitalize' }}>{key.replace('_', ' ')}:</strong> {Array.isArray(value) ? value.join(', ') : value.toString()}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </>
                ) : (
                  <div style={{ padding: '1rem', backgroundColor: 'rgba(255, 165, 0, 0.1)', border: '1px solid rgba(255, 165, 0, 0.3)', borderRadius: '0.5rem', fontSize: '0.85rem' }}>
                    <div style={{ marginBottom: '0.5rem' }}>⚠️ Gemini AI not configured</div>
                    <div style={{ fontSize: '0.75rem', color: 'rgba(255, 255, 255, 0.7)' }}>
                      To enable vehicle analysis:
                      <br />1. Get API key from Google AI Studio
                      <br />2. Create .env file in backend/
                      <br />3. Add: GEMINI_API_KEY=your_key
                      <br />4. Restart the server
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className="control-group">
              <h3>Model Information</h3>
              <div style={{ fontSize: '0.85rem', color: 'rgba(255, 255, 255, 0.8)' }}>
                <div>🚗 Vehicle Model: {modelsLoaded.vehicle_model || 'best.pt'}</div>
                <div>🪖 Helmet Model: {modelsLoaded.helmet_model || 'best-helmet-2.pt'}</div>
              </div>
            </div>

            <div className="control-group">
              <h3>Status</h3>
              <div style={{ fontSize: '0.85rem', color: 'rgba(255, 255, 255, 0.8)' }}>
                <div>Streaming: {isStreaming ? '✅ Active' : '❌ Inactive'}</div>
                <div>Source: {sourceType === 'camera' ? `📹 Camera ${cameraIndex}` : '🎬 Video File'}</div>
                <div>Detection: {detectionEnabled ? '✅ Enabled' : '❌ Disabled'}</div>
                <div>Mode: Vehicle Detection Only</div>
                <div>Confidence: {confidenceThreshold.toFixed(2)}</div>
                <div>Vehicle Classes: [{vehicleClasses.join(', ')}]</div>
                <div>Helmet Detection: {helmetInfo?.enabled ? '✅ Active' : '❌ Disabled'}</div>
                <div>Helmet Results: {helmetInfo?.total_results || 0}</div>
                <div>Violations: <span style={{ color: '#ff6b6b', fontWeight: 'bold' }}>{violationInfo?.total_violations || 0}</span></div>
                {videoInfo && videoInfo.source_type === 'video' && (
                  <>
                    <div>Video: {isPaused ? '⏸️ Paused' : '▶️ Playing'}</div>
                    <div>Progress: {Math.round((videoInfo.current_frame / videoInfo.total_frames) * 100)}%</div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
