import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Package,
  Loader2,
} from "lucide-react";
import { getInventoryForecast } from "../api";

const CommandCenter = ({ filterQuery }) => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState(null);

  useEffect(() => {
    fetchForecasts();
  }, []);

  const fetchForecasts = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getInventoryForecast(10);
      setProducts(data.products || []);
    } catch (err) {
      setError("Failed to load forecasts. Is the API running?");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Filter products based on BhaiBot query
  const filteredProducts = products.filter((product) => {
    if (!filterQuery) return true;
    const query = filterQuery.toLowerCase();
    return (
      product.product_name?.toLowerCase().includes(query) ||
      product.product_id?.toLowerCase().includes(query) ||
      product.recommendation?.toLowerCase().includes(query)
    );
  });

  // Get urgency styling
  const getUrgencyStyle = (recommendation) => {
    const rec = recommendation?.toLowerCase() || "";
    if (rec.includes("urgent") || rec.includes("critical")) {
      return {
        border: "alert-border",
        icon: AlertTriangle,
        iconColor: "text-rickshaw-orange",
        badge: "🚨 URGENT",
        badgeBg: "bg-rickshaw-orange/20 text-rickshaw-orange",
      };
    } else if (rec.includes("stable") || rec.includes("sufficient")) {
      return {
        border: "neon-border",
        icon: CheckCircle,
        iconColor: "text-neon-green",
        badge: "✅ STABLE",
        badgeBg: "bg-neon-green/20 text-neon-green",
      };
    } else {
      return {
        border: "border-jamdani-teal",
        icon: TrendingUp,
        iconColor: "text-jamdani-teal",
        badge: "⚠️ MONITOR",
        badgeBg: "bg-jamdani-teal/20 text-jamdani-teal",
      };
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-neon-green animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Loading AI Forecasts...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card p-8 text-center alert-border">
        <AlertTriangle className="w-12 h-12 text-rickshaw-orange mx-auto mb-4" />
        <h3 className="text-xl font-bold text-rickshaw-orange mb-2">
          Connection Error
        </h3>
        <p className="text-gray-400 mb-4">{error}</p>
        <button onClick={fetchForecasts} className="neon-button">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass-card p-6 neon-border">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold gradient-text mb-2">
              AI Command Center
            </h2>
            <p className="text-gray-400">
              Real-time inventory intelligence powered by MillionX AI
            </p>
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold text-neon-green pulse-glow">
              {filteredProducts.length}
            </div>
            <div className="text-sm text-gray-400">Products Monitored</div>
          </div>
        </div>
      </div>

      {/* Product Grid */}
      {filteredProducts.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <Package className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400">
            {filterQuery
              ? `No products match "${filterQuery}"`
              : "No forecast data available"}
          </p>
        </div>
      ) : (
        <motion.div
          layout
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
        >
          <AnimatePresence>
            {filteredProducts.map((product, index) => {
              const style = getUrgencyStyle(product.recommendation);
              const Icon = style.icon;

              return (
                <motion.div
                  key={product.product_id || index}
                  layoutId={product.product_id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  transition={{ delay: index * 0.05 }}
                  className={`cyber-card ${style.border} relative overflow-hidden`}
                  onClick={() => setSelectedProduct(product)}
                >
                  {/* Background Glow */}
                  <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-neon-green/10 to-transparent blur-2xl"></div>

                  {/* Badge */}
                  <div
                    className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold mb-3 ${style.badgeBg}`}
                  >
                    {style.badge}
                  </div>

                  {/* Content */}
                  <div className="relative z-10">
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="text-lg font-bold text-white truncate flex-1">
                        {product.product_name || "Unknown Product"}
                      </h3>
                      <Icon
                        className={`w-6 h-6 ${style.iconColor} flex-shrink-0 ml-2`}
                      />
                    </div>

                    <p className="text-sm text-gray-400 mb-3 line-clamp-2">
                      {product.recommendation || "No recommendation available"}
                    </p>

                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-500">
                        ID: {product.product_id}
                      </span>
                      <motion.span
                        className="text-neon-green font-mono"
                        whileHover={{ scale: 1.05 }}
                      >
                        View →
                      </motion.span>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </motion.div>
      )}

      {/* Expanded Product Modal */}
      <AnimatePresence>
        {selectedProduct && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
            onClick={() => setSelectedProduct(null)}
          >
            <motion.div
              layoutId={selectedProduct.product_id}
              className="glass-card p-8 max-w-2xl w-full relative"
              onClick={(e) => e.stopPropagation()}
            >
              <button
                onClick={() => setSelectedProduct(null)}
                className="absolute top-4 right-4 text-gray-400 hover:text-neon-green transition-colors"
              >
                ✕
              </button>

              <div className="space-y-4">
                <div>
                  <span
                    className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold mb-3 ${
                      getUrgencyStyle(selectedProduct.recommendation).badgeBg
                    }`}
                  >
                    {getUrgencyStyle(selectedProduct.recommendation).badge}
                  </span>
                  <h2 className="text-3xl font-bold gradient-text mb-2">
                    {selectedProduct.product_name}
                  </h2>
                  <p className="text-sm text-gray-500 mb-4">
                    Product ID: {selectedProduct.product_id}
                  </p>
                </div>

                <div className="glass-card p-4">
                  <h3 className="text-sm font-bold text-neon-green mb-2">
                    AI Recommendation:
                  </h3>
                  <p className="text-gray-300">
                    {selectedProduct.recommendation}
                  </p>
                </div>

                {selectedProduct.forecast_7d && (
                  <div className="glass-card p-4">
                    <h3 className="text-sm font-bold text-neon-green mb-2">
                      7-Day Forecast:
                    </h3>
                    <p className="text-2xl font-bold text-white">
                      {selectedProduct.forecast_7d} units
                    </p>
                  </div>
                )}

                <button
                  onClick={() => setSelectedProduct(null)}
                  className="neon-button w-full"
                >
                  Close
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default CommandCenter;
