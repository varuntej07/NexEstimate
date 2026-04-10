import React from "react";
import type { PropertyEstimate } from "../types/property";
import { formatNumber, formatHomeType } from "../services/api";

interface PropertyDetailsProps {
  data: PropertyEstimate;
}

interface DetailItem {
  icon: string;
  label: string;
  value: string;
}

const PropertyDetails: React.FC<PropertyDetailsProps> = ({ data }) => {
  const details: DetailItem[] = [
    { icon: "🛏️", label: "Bedrooms", value: data.bedrooms?.toString() ?? "N/A" },
    { icon: "🛁", label: "Bathrooms", value: data.bathrooms?.toString() ?? "N/A" },
    { icon: "📐", label: "Living Area", value: data.living_area ? `${formatNumber(data.living_area)} sqft` : "N/A" },
    { icon: "🏡", label: "Lot Size", value: data.lot_size ? `${formatNumber(Math.round(data.lot_size))} sqft` : "N/A" },
    { icon: "🏗️", label: "Year Built", value: data.year_built?.toString() ?? "N/A" },
    { icon: "🏠", label: "Home Type", value: formatHomeType(data.home_type) },
    { icon: "📍", label: "County", value: data.county ?? "N/A" },
    { icon: "💰", label: "Tax Rate", value: data.property_tax_rate != null ? `${data.property_tax_rate}%` : "N/A" },
  ];

  return (
    <div className="property-details card" id="property-details">
      <h3 className="card-title">Property Details</h3>
      <div className="details-grid">
        {details.map((item) => (
          <div className="detail-item" key={item.label}>
            <span className="detail-icon">{item.icon}</span>
            <div className="detail-content">
              <span className="detail-label">{item.label}</span>
              <span className="detail-value">{item.value}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PropertyDetails;
