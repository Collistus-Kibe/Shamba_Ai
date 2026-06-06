import React, { useEffect, useState, useRef } from "react";
import api from "../services/api";

interface MonitorProps {
  activeFarmId: number | null;
  onFarmUpdated?: () => void;
}

export const Monitor: React.FC<MonitorProps> = ({ activeFarmId, onFarmUpdated }) => {
  const [loading, setLoading] = useState(false);
  const [weatherData, setWeatherData] = useState<any>(null);
  const [crops, setCrops] = useState<any[]>([]);
  const [healthScore, setHealthScore] = useState(85);
  
  // Boundary Drawing States
  const [isDrawing, setIsDrawing] = useState(false);
  const [vertices, setVertices] = useState<[number, number][]>([]);
  const [drawnArea, setDrawnArea] = useState<number>(0);
  const [farmName, setFarmName] = useState("");
  const [cropType, setCropType] = useState("");
  const [newFarmModal, setNewFarmModal] = useState(false);
  
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const leafletMapRef = useRef<any>(null);
  const leafletPolygonRef = useRef<any>(null);
  const leafletMarkersRef = useRef<any[]>([]);

  // 1. Fetch telemetry logs on farm change
  useEffect(() => {
    if (!activeFarmId) return;

    const loadMonitorData = async () => {
      setLoading(true);
      try {
        const weather = await api.getFarmWeather(activeFarmId);
        setWeatherData(weather);

        const farmCrops = await api.getFarmCrops(activeFarmId);
        setCrops(farmCrops);
        if (farmCrops.length > 0) {
          const avg = Math.round(farmCrops.reduce((acc, curr) => acc + curr.health_score, 0) / farmCrops.length);
          setHealthScore(avg);
        } else {
          setHealthScore(85);
        }
      } catch (e) {
        console.error("Failed to load monitor telemetry", e);
      } finally {
        setLoading(false);
      }
    };

    loadMonitorData();
  }, [activeFarmId]);

  // 2. Initialize Leaflet Map
  useEffect(() => {
    // Dynamic import to avoid SSR errors and ensure window is defined
    import("leaflet").then((L) => {
      if (!mapContainerRef.current) return;

      // Clean up previous map if exists
      if (leafletMapRef.current) {
        leafletMapRef.current.remove();
        leafletMapRef.current = null;
      }

      // Default coordinates: Nairobi region or current farm coordinates
      let mapCenter: [number, number] = [-1.2921, 36.8219];
      let zoomLevel = 13;

      const initMap = async () => {
        if (activeFarmId) {
          try {
            const farm = await api.getFarms();
            const current = farm.find(f => f.id === activeFarmId);
            if (current && current.latitude && current.longitude) {
              mapCenter = [current.latitude, current.longitude];
              zoomLevel = 16;
            }
          } catch (e) {
            console.error(e);
          }
        }

        const map = L.map(mapContainerRef.current!).setView(mapCenter, zoomLevel);
        leafletMapRef.current = map;

        // Set OpenStreetMap tiles
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);

        // Map Click Listener for boundary drawing
        map.on("click", (e: any) => {
          if (!isDrawing) return;

          const { lat, lng } = e.latlng;
          setVertices((prev) => {
            const next: [number, number][] = [...prev, [lat, lng]];
            
            // Draw marker
            const marker = L.marker([lat, lng], {
              draggable: true
            }).addTo(map);
            leafletMarkersRef.current.push(marker);

            // Re-draw polygon overlay
            if (leafletPolygonRef.current) {
              leafletPolygonRef.current.setLatLngs(next);
            } else {
              leafletPolygonRef.current = L.polygon(next, {
                color: "#006c49",
                fillColor: "#6cf8bb",
                fillOpacity: 0.4
              }).addTo(map);
            }

            // Calculate drawn area in hectares
            const area = calculatePolygonArea(next);
            setDrawnArea(area);

            return next;
          });
        });
      };

      initMap();
    });

    return () => {
      if (leafletMapRef.current) {
        leafletMapRef.current.remove();
        leafletMapRef.current = null;
      }
    };
  }, [activeFarmId, isDrawing]);

  // Shoelace formula approximation for mapping polygon area in Hectares
  const calculatePolygonArea = (latLngs: [number, number][]): number => {
    if (latLngs.length < 3) return 0;
    const numPoints = latLngs.length;
    const latMid = (latLngs[0][0] * Math.PI) / 180;
    const metersPerLat = 111320;
    const metersPerLng = 111320 * Math.cos(latMid);

    const coords = latLngs.map(p => [p[1] * metersPerLng, p[0] * metersPerLat]);

    let area = 0;
    let j = numPoints - 1;
    for (let i = 0; i < numPoints; i++) {
      const p1 = coords[i];
      const p2 = coords[j];
      area += (p2[0] + p1[0]) * (p2[1] - p1[1]);
      j = i;
    }
    area = Math.abs(area / 2); // area in sq meters
    return parseFloat((area / 10000).toFixed(2)); // return in Hectares
  };

  const handleStartDrawing = () => {
    // Reset drawing state
    setVertices([]);
    setDrawnArea(0);
    setIsDrawing(true);
    
    // Clear old layers
    if (leafletPolygonRef.current) {
      leafletPolygonRef.current.remove();
      leafletPolygonRef.current = null;
    }
    leafletMarkersRef.current.forEach(m => m.remove());
    leafletMarkersRef.current = [];
  };

  const handleClearDrawing = () => {
    setVertices([]);
    setDrawnArea(0);
    if (leafletPolygonRef.current) {
      leafletPolygonRef.current.remove();
      leafletPolygonRef.current = null;
    }
    leafletMarkersRef.current.forEach(m => m.remove());
    leafletMarkersRef.current = [];
  };

  const handleSaveBoundary = () => {
    if (vertices.length < 3) {
      alert("Please draw at least 3 points on the map to close a boundary polygon.");
      return;
    }
    setNewFarmModal(true);
  };

  const handleCreateFarmSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!farmName.trim() || !cropType.trim()) return;

    setLoading(true);
    try {
      // GeoJSON polygon coordinate formatting
      const geoJsonBoundary = {
        type: "Polygon",
        coordinates: [vertices.map(v => [v[1], v[0]])] // [longitude, latitude]
      };

      // Starting point center lat/lon
      const centerLat = vertices[0][0];
      const centerLon = vertices[0][1];

      await api.createFarm({
        name: farmName,
        crop_type: cropType,
        latitude: centerLat,
        longitude: centerLon,
        boundary: geoJsonBoundary,
        area_hectares: drawnArea
      });

      // Reset states
      setNewFarmModal(false);
      setIsDrawing(false);
      handleClearDrawing();
      if (onFarmUpdated) onFarmUpdated();
      alert("New Shamba registered successfully!");
    } catch (err: any) {
      alert(`Error creating farm profile: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // SVG dash offset mapping
  const dashArray = `${healthScore}, 100`;

  return (
    <main className="p-margin-mobile flex flex-col gap-lg max-w-lg mx-auto">
      {/* Map Drawing Controls Overlay Card */}
      <section className="bg-surface-container-lowest border border-outline-variant rounded-xl p-md shadow-sm space-y-md">
        <div className="flex justify-between items-center">
          <h2 className="font-label-md text-label-md text-primary font-bold uppercase tracking-wider">
            Farm Boundary Map
          </h2>
          {isDrawing ? (
            <div className="flex gap-sm">
              <button 
                onClick={handleClearDrawing}
                className="bg-surface border border-outline-variant font-label-sm text-label-sm px-3 py-1.5 rounded-full hover:bg-surface-container-low transition-colors"
              >
                Clear
              </button>
              <button 
                onClick={handleSaveBoundary}
                className="bg-secondary text-white font-label-sm text-label-sm px-3 py-1.5 rounded-full hover:bg-primary-container transition-colors font-bold shadow-sm"
              >
                Save ({drawnArea} Ha)
              </button>
            </div>
          ) : (
            <button 
              onClick={handleStartDrawing}
              className="bg-primary text-on-primary font-label-sm text-label-sm px-3 py-1.5 rounded-full hover:bg-primary-container transition-all font-bold shadow-sm flex items-center gap-xs"
            >
              <span className="material-symbols-outlined text-[16px]">draw</span>
              Draw Farm Boundary
            </button>
          )}
        </div>

        {/* Leaflet Map Drawing Container */}
        <div className="relative w-full h-[240px] rounded-xl overflow-hidden shadow-sm border border-outline-variant bg-surface-container">
          <div ref={mapContainerRef} className="w-full h-full" />
          <div className="absolute inset-0 grid-overlay pointer-events-none z-[1000]"></div>
          
          <div className="absolute top-3 left-3 bg-surface-container-lowest/90 backdrop-blur-md text-on-surface px-3 py-1.5 rounded-lg shadow-sm border border-outline-variant/50 flex items-center gap-2 z-[1001]">
            <span className={`w-2 h-2 rounded-full ${isDrawing ? "bg-secondary animate-pulse" : "bg-error"}`}></span>
            <span className="font-label-sm text-label-sm font-bold">
              {isDrawing ? "Drawing Active" : "Farm Sat Feed"}
            </span>
          </div>
        </div>
      </section>

      {/* Main Health Score & NDVI Bento */}
      <div className="grid grid-cols-2 gap-md">
        {/* Farm Health Score Circular Progress */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-md shadow-[0_2px_8px_rgba(0,0,0,0.04)] flex flex-col items-center justify-center relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-secondary to-transparent opacity-50"></div>
          <h2 className="font-label-md text-label-md text-on-surface-variant mb-4 self-start font-bold uppercase tracking-wider">
            Health Score
          </h2>
          <div className="relative w-32 h-32 flex items-center justify-center">
            <svg className="circular-chart text-secondary" viewBox="0 0 36 36">
              <path className="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"></path>
              <path className="circle" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" stroke="currentColor" strokeDasharray={dashArray}></path>
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="font-display-lg text-display-lg text-primary tracking-tighter font-bold">
                {healthScore}
              </span>
            </div>
          </div>
          <div className="mt-2 flex items-center gap-1 text-secondary font-bold">
            <span className="material-symbols-outlined text-[16px]">trending_up</span>
            <span className="font-label-sm text-label-sm">+2% this week</span>
          </div>
        </div>

        {/* Vegetation Health (NDVI) */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-md shadow-[0_2px_8px_rgba(0,0,0,0.04)] flex flex-col justify-between">
          <div>
            <h2 className="font-label-md text-label-md text-on-surface-variant flex items-center gap-2 mb-2 font-bold uppercase tracking-wider">
              <span className="material-symbols-outlined text-[18px]">forest</span>
              NDVI Summary
            </h2>
            <p className="font-body-sm text-body-sm text-on-surface-variant line-clamp-3 mt-1 leading-relaxed">
              Vegetation canopy index is highly consistent. Small water stress detected in dry leaf sectors.
            </p>
          </div>
          <div className="mt-4">
            <div className="flex justify-between font-label-sm text-label-sm text-on-surface-variant mb-1 font-bold">
              <span>Index</span>
              <span className="text-primary font-bold">0.72 / 1.0</span>
            </div>
            <div className="w-full h-3 bg-surface-container-high rounded-full overflow-hidden flex">
              <div className="h-full bg-error" style={{ width: "15%" }}></div>
              <div className="h-full bg-tertiary-fixed-dim" style={{ width: "25%" }}></div>
              <div className="h-full bg-secondary" style={{ width: "60%" }}></div>
            </div>
            <div className="flex justify-between font-label-sm text-[10px] text-outline mt-1 font-bold uppercase">
              <span>Low</span>
              <span>High</span>
            </div>
          </div>
        </div>
      </div>

      {/* Environmental Metrics Grid */}
      <div>
        <h3 className="font-label-md text-label-md text-on-surface-variant mb-3 px-1 uppercase tracking-wider font-bold">
          Environmental Sensors
        </h3>
        <div className="grid grid-cols-3 gap-sm">
          {/* Rainfall */}
          <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-3 flex flex-col justify-between aspect-square hover:bg-surface-container-low transition-colors cursor-pointer shadow-[0_2px_6px_rgba(0,0,0,0.02)]">
            <div className="text-primary-container bg-primary-container/10 w-8 h-8 rounded-full flex items-center justify-center mb-2">
              <span className="material-symbols-outlined text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                water_drop
              </span>
            </div>
            <div>
              <span className="font-headline-md text-headline-md text-primary leading-none block font-bold">
                {weatherData ? weatherData.rainfall : 12}
              </span>
              <span className="font-label-sm text-label-sm text-on-surface-variant font-bold">
                mm / 24h
              </span>
            </div>
          </div>

          {/* Humidity */}
          <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-3 flex flex-col justify-between aspect-square hover:bg-surface-container-low transition-colors cursor-pointer shadow-[0_2px_6px_rgba(0,0,0,0.02)]">
            <div className="text-secondary bg-secondary/10 w-8 h-8 rounded-full flex items-center justify-center mb-2">
              <span className="material-symbols-outlined text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                air
              </span>
            </div>
            <div>
              <span className="font-headline-md text-headline-md text-primary leading-none block font-bold">
                {weatherData ? `${Math.round(weatherData.humidity)}%` : "64%"}
              </span>
              <span className="font-label-sm text-label-sm text-on-surface-variant font-bold">
                Humidity
              </span>
            </div>
          </div>

          {/* Soil Moisture */}
          <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-3 flex flex-col justify-between aspect-square hover:bg-surface-container-low transition-colors cursor-pointer relative overflow-hidden shadow-[0_2px_6px_rgba(0,0,0,0.02)]">
            {weatherData?.soil_moisture < 30 && (
              <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-tertiary-container animate-pulse"></div>
            )}
            <div className={`w-8 h-8 rounded-full flex items-center justify-center mb-2 ${
              weatherData?.soil_moisture < 30 ? "text-tertiary-container bg-tertiary-container/10" : "text-secondary bg-secondary/10"
            }`}>
              <span className="material-symbols-outlined text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                grass
              </span>
            </div>
            <div>
              <span className={`font-headline-md text-headline-md leading-none block font-bold ${
                weatherData?.soil_moisture < 30 ? "text-tertiary-container" : "text-primary"
              }`}>
                {weatherData ? `${weatherData.soil_moisture}%` : "28%"}
              </span>
              <span className="font-label-sm text-label-sm text-on-surface-variant font-bold">
                Soil Moist
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* New Farm Registration Modal Dialog */}
      {newFarmModal && (
        <div className="fixed inset-0 bg-primary/40 backdrop-blur-sm flex justify-center items-center z-[9999] p-margin-mobile">
          <div className="bg-surface-container-lowest w-full max-w-sm rounded-xl border border-outline-variant p-md shadow-lg flex flex-col gap-md">
            <div>
              <h3 className="font-headline-md text-headline-md text-primary font-bold">
                Register New Shamba
              </h3>
              <p className="font-body-md text-body-md text-on-surface-variant text-sm mt-xs">
                Link crop profiles to the boundaries you just drew on the satellite feed.
              </p>
            </div>

            <form onSubmit={handleCreateFarmSubmit} className="flex flex-col gap-md">
              <div className="flex flex-col gap-xs">
                <label className="font-label-sm text-label-sm text-on-surface-variant font-bold">
                  Farm Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Kijani Sector B"
                  value={farmName}
                  onChange={(e) => setFarmName(e.target.value)}
                  className="bg-surface-container-high border-none rounded-lg p-md font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container-lowest focus:ring-1 focus:ring-secondary transition-all"
                  required
                />
              </div>

              <div className="flex flex-col gap-xs">
                <label className="font-label-sm text-label-sm text-on-surface-variant font-bold">
                  Primary Crop Grown
                </label>
                <input
                  type="text"
                  placeholder="e.g. Maize, Coffee, Tomatoes"
                  value={cropType}
                  onChange={(e) => setCropType(e.target.value)}
                  className="bg-surface-container-high border-none rounded-lg p-md font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container-lowest focus:ring-1 focus:ring-secondary transition-all"
                  required
                />
              </div>

              <div className="bg-surface-container p-sm rounded-lg border border-outline-variant/20 font-label-sm text-label-sm text-on-surface flex justify-between items-center font-bold">
                <span>Calculated Boundary Area:</span>
                <span className="text-secondary font-bold">{drawnArea} Hectares</span>
              </div>

              <div className="flex justify-end gap-sm mt-sm">
                <button
                  type="button"
                  onClick={() => setNewFarmModal(false)}
                  className="bg-surface border border-outline-variant px-4 py-2 rounded-lg font-label-md text-label-md font-bold text-on-surface hover:bg-surface-container-low transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-secondary text-white px-4 py-2 rounded-lg font-label-md text-label-md font-bold hover:bg-primary-container transition-colors shadow-sm"
                >
                  Confirm Registration
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
};

export default Monitor;
