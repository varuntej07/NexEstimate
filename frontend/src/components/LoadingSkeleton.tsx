import React from "react";

const LoadingSkeleton: React.FC = () => {
  return (
    <div className="loading-skeleton" id="loading-skeleton">
      {/* Hero skeleton */}
      <div className="skeleton-hero">
        <div className="skeleton-image shimmer" />
        <div className="skeleton-estimate">
          <div className="skeleton-line skeleton-label shimmer" />
          <div className="skeleton-line skeleton-value shimmer" />
          <div className="skeleton-line skeleton-range shimmer" />
        </div>
      </div>

      {/* Details skeleton */}
      <div className="skeleton-cards">
        <div className="skeleton-card shimmer" />
        <div className="skeleton-card shimmer" />
      </div>

      {/* Description skeleton */}
      <div className="skeleton-description">
        <div className="skeleton-line shimmer" style={{ width: "40%" }} />
        <div className="skeleton-line shimmer" style={{ width: "100%" }} />
        <div className="skeleton-line shimmer" style={{ width: "90%" }} />
        <div className="skeleton-line shimmer" style={{ width: "75%" }} />
      </div>
    </div>
  );
};

export default LoadingSkeleton;
