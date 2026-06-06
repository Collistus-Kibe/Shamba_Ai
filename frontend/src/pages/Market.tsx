import React, { useEffect, useState } from "react";
import api from "../services/api";

export const Market: React.FC = () => {
  const [prices, setPrices] = useState<any[]>([]);
  const [crops, setCrops] = useState<string[]>([]);
  const [regions, setRegions] = useState<string[]>([]);
  const [selectedCrop, setSelectedCrop] = useState<string>("Maize");
  const [selectedRegion, setSelectedRegion] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [bestMarket, setBestMarket] = useState<any>(null);

  // Load baseline prices and filter option lists
  useEffect(() => {
    const loadPrices = async () => {
      setLoading(true);
      try {
        const pricesList = await api.getMarketPrices(
          selectedCrop || undefined, 
          selectedRegion || undefined
        );
        setPrices(pricesList);

        const cropList = await api.getMarketCrops();
        setCrops(cropList);

        const regList = await api.getMarketPrices().then(arr => 
          Array.from(new Set(arr.map(item => item.region)))
        );
        setRegions(regList);

        // Fetch best market info
        if (selectedCrop) {
          const best = await api.getMarketBest(selectedCrop);
          setBestMarket(best);
        }
      } catch (e) {
        console.error("Failed to load market statistics", e);
      } finally {
        setLoading(false);
      }
    };

    loadPrices();
  }, [selectedCrop, selectedRegion]);

  // Premium vector SVG price line chart builder
  const renderSVGChart = () => {
    // Standard mock price heights (percentages from bottom of viewbox)
    // Represents historical weekly movements: Mon, Tue, Wed, Thu, Fri, Sat, Sun
    const mockPoints = [20, 32, 26, 54, 82, 78, 88];
    const width = 500;
    const height = 180;
    const padding = 20;

    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;

    const coordinates = mockPoints.map((val, index) => {
      const x = padding + (index * chartWidth) / (mockPoints.length - 1);
      const y = height - padding - (val * chartHeight) / 100;
      return { x, y };
    });

    // Create cubic bezier curve commands
    let pathD = `M ${coordinates[0].x} ${coordinates[0].y}`;
    for (let i = 0; i < coordinates.length - 1; i++) {
      const p0 = coordinates[i];
      const p1 = coordinates[i + 1];
      const cpX1 = p0.x + (p1.x - p0.x) / 2;
      const cpY1 = p0.y;
      const cpX2 = p0.x + (p1.x - p0.x) / 2;
      const cpY2 = p1.y;
      pathD += ` C ${cpX1} ${cpY1}, ${cpX2} ${cpY2}, ${p1.x} ${p1.y}`;
    }

    // Gradient fill path
    const fillD = `${pathD} L ${coordinates[coordinates.length - 1].x} ${height - padding} L ${coordinates[0].x} ${height - padding} Z`;

    return (
      <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} className="overflow-visible">
        <defs>
          <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#6cf8bb" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#6cf8bb" stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {/* X Axis Grid Lines */}
        <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#bfc9c3" strokeOpacity="0.4" strokeWidth="1" />
        <line x1={padding} y1={padding} x2={width - padding} y2={padding} stroke="#bfc9c3" strokeOpacity="0.1" strokeWidth="1" />
        <line x1={padding} y1={(height) / 2} x2={width - padding} y2={(height) / 2} stroke="#bfc9c3" strokeOpacity="0.1" strokeWidth="1" />

        {/* Path Fill Area (Gradient) */}
        <path d={fillD} fill="url(#chartGradient)" />

        {/* Line Path */}
        <path d={pathD} fill="none" stroke="#006c49" strokeWidth="3" strokeLinecap="round" />

        {/* Markers */}
        {coordinates.map((pt, idx) => (
          <g key={idx}>
            <circle
              cx={pt.x}
              cy={pt.y}
              r="4"
              fill="#003527"
              stroke="#ffffff"
              strokeWidth="2"
              className="transition-transform duration-200 hover:scale-150 cursor-pointer"
            />
            {idx === coordinates.length - 1 && (
              <circle
                cx={pt.x}
                cy={pt.y}
                r="8"
                fill="#6cf8bb"
                fillOpacity="0.3"
                className="animate-ping"
              />
            )}
          </g>
        ))}
      </svg>
    );
  };

  return (
    <main className="p-margin-mobile md:p-margin-desktop space-y-lg max-w-7xl mx-auto">
      {/* Interactive Chart Section */}
      <section className="bg-surface-container-lowest border border-outline-variant rounded-xl p-md shadow-sm relative overflow-hidden">
        <div className="flex justify-between items-start mb-sm">
          <div>
            <span className="font-label-md text-label-md text-primary bg-primary-fixed-dim bg-opacity-20 px-2 py-1 rounded-sm uppercase tracking-widest block mb-xs w-fit">
              {selectedCrop} ({bestMarket?.price_unit || "90kg Bag"})
            </span>
            <h2 className="font-headline-lg-mobile text-headline-lg-mobile md:font-headline-lg md:text-headline-lg text-on-surface font-bold">
              KES {bestMarket ? bestMarket.current_price.toLocaleString() : "3,450"}
            </h2>
            <p className="font-body-md text-body-md text-secondary font-semibold flex items-center gap-1 mt-xs">
              <span className="material-symbols-outlined text-[16px] font-bold">trending_up</span> 
              {bestMarket ? `+${bestMarket.trend_percentage}%` : "+5.2%"} (7 Days)
            </p>
          </div>

          {/* Region Filter Selector */}
          <div className="flex gap-xs">
            <select
              value={selectedCrop}
              onChange={(e) => setSelectedCrop(e.target.value)}
              className="bg-surface-container border border-outline-variant rounded-full px-3 py-1 font-label-sm text-label-sm text-on-surface-variant outline-none focus:ring-1 focus:ring-primary cursor-pointer"
            >
              {crops.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
        </div>

        {/* SVG Chart display */}
        <div className="h-48 w-full mt-md relative">
          {renderSVGChart()}
        </div>
        
        <div className="flex justify-between mt-sm text-outline font-label-sm text-label-sm px-2 font-bold uppercase">
          <span>Mon</span>
          <span>Tue</span>
          <span>Wed</span>
          <span>Thu</span>
          <span>Fri</span>
          <span>Sat</span>
          <span>Sun</span>
        </div>
      </section>

      {/* Business Insights */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-md">
        <div className="bg-primary-container text-on-primary-container rounded-xl p-md flex items-start gap-md shadow-sm relative overflow-hidden group">
          <div className="absolute inset-0 opacity-10 bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-white to-transparent pointer-events-none"></div>
          <div className="bg-surface-tint bg-opacity-30 p-2 rounded-lg">
            <span className="material-symbols-outlined text-secondary-fixed">compost</span>
          </div>
          <div>
            <h3 className="font-label-md text-label-md uppercase opacity-85 mb-1 font-bold tracking-wider">
              High-Demand Crop
            </h3>
            <p className="font-headline-md text-headline-md text-white font-bold mb-xs">Soybeans</p>
            <p className="font-body-md text-body-md opacity-90">
              +12% expected yield return next quarter. Domestic supply contracts expanding.
            </p>
          </div>
        </div>

        <div className="bg-surface-container-highest text-on-surface rounded-xl p-md flex items-start gap-md shadow-sm border border-outline-variant/30">
          <div className="bg-surface p-2 rounded-lg border border-outline-variant">
            <span className="material-symbols-outlined text-primary">location_on</span>
          </div>
          <div>
            <h3 className="font-label-md text-label-md uppercase text-on-surface-variant mb-1 font-bold tracking-wider">
              Best Market
            </h3>
            <p className="font-headline-md text-headline-md text-primary font-bold mb-xs">
              {bestMarket ? bestMarket.market_name : "Eldoret Central"}
            </p>
            <p className="font-body-md text-body-md text-on-surface-variant">
              Currently offering KES {bestMarket ? bestMarket.current_price.toLocaleString() : "3,800"} per {bestMarket?.price_unit || "bag"}.
            </p>
          </div>
        </div>
      </section>

      {/* Current Market Prices List */}
      <section className="space-y-sm">
        <h2 className="font-headline-md text-headline-md text-on-surface font-bold">
          Current Market Prices
        </h2>
        <div className="flex flex-col gap-sm">
          {prices.map((item) => (
            <div 
              key={item.id} 
              className="bg-surface-container-lowest border border-outline-variant rounded-lg p-md flex justify-between items-center shadow-[0_2px_4px_rgba(0,0,0,0.02)] hover:shadow-md transition-shadow"
            >
              <div className="flex items-center gap-md">
                <div className="w-10 h-10 rounded-full bg-surface-container-low flex items-center justify-center text-primary font-bold text-lg">
                  {item.crop.charAt(0)}
                </div>
                <div>
                  <h3 className="font-label-md text-label-md text-on-surface font-bold">
                    {item.crop}
                  </h3>
                  <span className="inline-block mt-1 font-label-sm text-label-sm text-on-surface-variant bg-surface-container-high px-2.5 py-0.5 rounded-full font-bold">
                    {item.market_name}
                  </span>
                </div>
              </div>
              
              <div className="text-right">
                <p className="font-headline-md text-headline-md text-on-surface text-[18px] font-bold">
                  {item.currency} {item.current_price.toLocaleString()}
                </p>
                <p className={`font-label-sm text-label-sm flex items-center justify-end gap-0.5 font-bold ${
                  item.trend_percentage > 0 
                    ? "text-secondary" 
                    : item.trend_percentage < 0 
                      ? "text-error" 
                      : "text-outline"
                }`}>
                  <span className="material-symbols-outlined text-[14px] font-bold">
                    {item.trend_percentage > 0 
                      ? "arrow_upward" 
                      : item.trend_percentage < 0 
                        ? "arrow_downward" 
                        : "horizontal_rule"}
                  </span>
                  {item.trend_percentage !== 0 ? `${Math.abs(item.trend_percentage)}%` : "0.0%"}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Market Alerts */}
      <section>
        <h2 className="font-headline-md text-headline-md text-on-surface font-bold mb-md">
          Market Alerts
        </h2>
        <div className="bg-error-container text-on-error-container rounded-xl p-md flex items-start gap-md border border-[#ffb4ab] shadow-sm">
          <span className="material-symbols-outlined text-error mt-0.5 text-[28px]">
            warning
          </span>
          <div>
            <h3 className="font-label-md text-label-md font-bold mb-xs text-on-error-container uppercase tracking-wider">
              Fertilizer Price Surge
            </h3>
            <p className="font-body-md text-body-md text-sm leading-relaxed">
              DAP fertilizer prices have increased by 15% in your region. Consider purchasing soon or exploring compost-based alternatives.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
};

export default Market;
