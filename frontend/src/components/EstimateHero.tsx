import React from "react";
import type { PropertyEstimate } from "../types/property";
import { formatCurrency } from "../services/api";

interface EstimateHeroProps {
  data: PropertyEstimate;
}

const EstimateHero: React.FC<EstimateHeroProps> = ({ data }) => {
  const lowPct = data.zestimate_range?.low_percent
    ? parseInt(data.zestimate_range.low_percent)
    : null;
  const highPct = data.zestimate_range?.high_percent
    ? parseInt(data.zestimate_range.high_percent)
    : null;

  const zestimateLow =
    data.zestimate && lowPct
      ? Math.round(data.zestimate * (1 - lowPct / 100))
      : null;
  const zestimateHigh =
    data.zestimate && highPct
      ? Math.round(data.zestimate * (1 + highPct / 100))
      : null;

  return (
    <div className="estimate-hero" id="estimate-hero">
      {/* Property image */}
      {data.image_url && (
        <div className="hero-image-container">
          <img
            src={data.image_url}
            alt={data.full_address || "Property"}
            className="hero-image"
          />
          <div className="hero-image-overlay">
            {data.home_status && (
              <span className={`status-badge status-${data.home_status?.toLowerCase().replace(/_/g, "-")}`}>
                {data.home_status.replace(/_/g, " ")}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Zestimate display */}
      <div className="zestimate-display">
        <div className="zestimate-label">Zestimate®</div>
        <div className="zestimate-value">
          {data.zestimate != null ? formatCurrency(data.zestimate) : "Not Available"}
        </div>

        {zestimateLow != null && zestimateHigh != null && (
          <div className="zestimate-range">
            <div className="range-bar">
              <div className="range-track">
                <div className="range-indicator" />
              </div>
            </div>
            <div className="range-labels">
              <span>{formatCurrency(zestimateLow)}</span>
              <span>{formatCurrency(zestimateHigh)}</span>
            </div>
          </div>
        )}

        {data.rent_zestimate != null && (
          <div className="rent-estimate">
            <span className="rent-label">Rent Zestimate®</span>
            <span className="rent-value">{formatCurrency(data.rent_zestimate)}/mo</span>
          </div>
        )}
      </div>

      {/* Address */}
      <div className="hero-address">
        <h2>{data.street_address}</h2>
        <p>
          {data.city}, {data.state} {data.zipcode}
          {data.county && <span className="county"> · {data.county}</span>}
        </p>
      </div>

      {/* Zillow link */}
      {data.zillow_url && (
        <a
          href={data.zillow_url}
          target="_blank"
          rel="noopener noreferrer"
          className="zillow-link"
          id="zillow-link"
        >
          View on Zillow →
        </a>
      )}
    </div>
  );
};

export default EstimateHero;
