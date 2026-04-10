import React from "react";
import type { PropertyEstimate } from "../types/property";
import { formatCurrency } from "../services/api";

interface PricingInfoProps {
  data: PropertyEstimate;
}

const PricingInfo: React.FC<PricingInfoProps> = ({ data }) => {
  const items = [
    {
      label: "List Price",
      value: formatCurrency(data.price),
      highlight: true,
    },
    {
      label: "Last Sold Price",
      value: formatCurrency(data.last_sold_price),
      highlight: false,
    },
    {
      label: "Days on Zillow",
      value: data.days_on_zillow != null ? `${data.days_on_zillow} days` : "N/A",
      highlight: false,
    },
    {
      label: "Page Views",
      value: data.page_view_count != null ? data.page_view_count.toLocaleString() : "N/A",
      highlight: false,
    },
    {
      label: "Favorites",
      value: data.favorite_count != null ? data.favorite_count.toLocaleString() : "N/A",
      highlight: false,
    },
  ];

  return (
    <div className="pricing-info card" id="pricing-info">
      <h3 className="card-title">Market Data</h3>
      <div className="pricing-list">
        {items.map((item) => (
          <div
            className={`pricing-item ${item.highlight ? "pricing-highlight" : ""}`}
            key={item.label}
          >
            <span className="pricing-label">{item.label}</span>
            <span className="pricing-value">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PricingInfo;
