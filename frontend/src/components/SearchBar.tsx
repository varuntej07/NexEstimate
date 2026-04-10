import React, { useState } from "react";

interface SearchBarProps {
  onSearch: (address: string) => void;
  loading: boolean;
}

const SearchBar: React.FC<SearchBarProps> = ({ onSearch, loading }) => {
  const [address, setAddress] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = address.trim();
    if (trimmed.length >= 5) {
      onSearch(trimmed);
    }
  };

  return (
    <form className="search-bar" onSubmit={handleSubmit} id="search-form">
      <div className="search-input-wrapper">
        <svg
          className="search-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.3-4.3" />
        </svg>
        <input
          id="address-input"
          type="text"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          placeholder="Enter a US property address (e.g. 328 26th Avenue, Seattle, WA 98122)"
          disabled={loading}
          autoFocus
          autoComplete="off"
        />
      </div>
      <button
        id="search-button"
        type="submit"
        disabled={loading || address.trim().length < 5}
      >
        {loading ? (
          <span className="button-loading">
            <span className="spinner" />
            Searching...
          </span>
        ) : (
          "Get Estimate"
        )}
      </button>
    </form>
  );
};

export default SearchBar;
