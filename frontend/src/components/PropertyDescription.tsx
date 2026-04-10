import React, { useState } from "react";

interface PropertyDescriptionProps {
  description: string | null;
}

const PropertyDescription: React.FC<PropertyDescriptionProps> = ({ description }) => {
  const [expanded, setExpanded] = useState(false);

  if (!description) return null;

  const isLong = description.length > 300;
  const displayText = isLong && !expanded ? description.slice(0, 300) + "..." : description;

  return (
    <div className="property-description card" id="property-description">
      <h3 className="card-title">About This Property</h3>
      <p className="description-text">{displayText}</p>
      {isLong && (
        <button
          className="expand-button"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? "Show less" : "Read more"}
        </button>
      )}
    </div>
  );
};

export default PropertyDescription;
