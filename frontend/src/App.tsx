import SearchBar from "./components/SearchBar";
import EstimateHero from "./components/EstimateHero";
import PropertyDetails from "./components/PropertyDetails";
import PricingInfo from "./components/PricingInfo";
import PropertyDescription from "./components/PropertyDescription";
import LoadingSkeleton from "./components/LoadingSkeleton";
import ErrorDisplay from "./components/ErrorDisplay";
import { useEstimate } from "./hooks/useEstimate";
import { useState } from "react";

function App() {
  const { data, loading, error, search } = useEstimate();
  const [lastAddress, setLastAddress] = useState("");

  const handleSearch = (address: string) => {
    setLastAddress(address);
    search(address);
  };

  const handleRetry = () => {
    if (lastAddress) {
      search(lastAddress);
    }
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="logo">
            <span className="logo-icon">🏠</span>
            <h1>
              Nex<span className="logo-accent">Estimate</span>
            </h1>
          </div>
          <p className="header-subtitle">
            Zillow Zestimate® Agent — Instant property valuations powered by AI
          </p>
        </div>
      </header>

      {/* Main content */}
      <main className="app-main">
        <div className="container">
          {/* Search section */}
          <section className="search-section">
            <SearchBar onSearch={handleSearch} loading={loading} />
          </section>

          {/* Results */}
          {loading && <LoadingSkeleton />}

          {error && (
            <ErrorDisplay message={error} onRetry={handleRetry} />
          )}

          {data && !loading && (
            <div className="results-container" id="results">
              <EstimateHero data={data} />

              <div className="details-row">
                <PropertyDetails data={data} />
                <PricingInfo data={data} />
              </div>

              <PropertyDescription description={data.description} />
            </div>
          )}

          {/* Empty state */}
          {!data && !loading && !error && (
            <div className="empty-state" id="empty-state">
              <div className="empty-icon">🔍</div>
              <h2>Find Any Property's Zestimate</h2>
              <p>
                Enter a US property address above to get the current Zillow
                Zestimate®, property details, and market data.
              </p>
              <div className="sample-addresses">
                <p className="sample-label">Try these examples:</p>
                {[
                  "328 26th Avenue, Seattle, WA 98122",
                  "1600 Pennsylvania Ave, Washington, DC 20500",
                  "742 Evergreen Terrace, Springfield, IL 62704",
                ].map((addr) => (
                  <button
                    key={addr}
                    className="sample-address"
                    onClick={() => handleSearch(addr)}
                  >
                    {addr}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <p>
          NexEstimate · Built with FastAPI + React + TypeScript ·{" "}
          <a
            href="/docs"
            target="_blank"
            rel="noopener noreferrer"
          >
            API Docs
          </a>
        </p>
      </footer>
    </div>
  );
}

export default App;
