import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Package,
  Loader2,
  HelpCircle,
} from "lucide-react";
import { getInventoryForecast } from "../api";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
} from "recharts";

// Helper to get product image from Unsplash based on name
const getProductImage = (name) => {
  const lowerName = name.toLowerCase();
  if (
    lowerName.includes("phone") ||
    lowerName.includes("mobile") ||
    lowerName.includes("samsung") ||
    lowerName.includes("iphone")
  )
    return "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=500&q=80";
  if (
    lowerName.includes("laptop") ||
    lowerName.includes("computer") ||
    lowerName.includes("dell") ||
    lowerName.includes("macbook")
  )
    return "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500&q=80";
  if (
    lowerName.includes("camera") ||
    lowerName.includes("canon") ||
    lowerName.includes("sony")
  )
    return "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=500&q=80";
  if (
    lowerName.includes("shoe") ||
    lowerName.includes("nike") ||
    lowerName.includes("adidas")
  )
    return "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500&q=80";
  if (
    lowerName.includes("watch") ||
    lowerName.includes("rolex") ||
    lowerName.includes("time")
  )
    return "https://images.unsplash.com/photo-1524592094714-0f0654e20314?w=500&q=80";
  if (
    lowerName.includes("shirt") ||
    lowerName.includes("cloth") ||
    lowerName.includes("apparel")
  )
    return "https://images.unsplash.com/photo-1489987707025-afc232f7ea0f?w=500&q=80";
  if (
    lowerName.includes("headphone") ||
    lowerName.includes("audio") ||
    lowerName.includes("speaker")
  )
    return "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&q=80";

  // Default tech/product image
  return "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=500&q=80";
};

const CommandCenter = ({ filterQuery }) => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [showMetricsTooltip, setShowMetricsTooltip] = useState(false);
  useEffect(() => {
    fetchForecasts();
  }, []);

  const fetchForecasts = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getInventoryForecast(100); // Show ALL products

      // Flatten the nested structure: analysis.forecast → forecast
      const flattenedProducts = (data.products || []).map((product) => ({
        ...product,
        forecast: product.analysis?.forecast || null,
        forecast_7d: product.analysis?.forecast?.predicted_demand
          ? Math.round(product.analysis.forecast.predicted_demand)
          : null,
      }));

      setProducts(flattenedProducts);
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
                  className={`cyber-card ${style.border} relative overflow-hidden group cursor-pointer`}
                  onClick={() => setSelectedProduct(product)}
                >
                  {/* Product Image Header */}
                  <div className="h-36 w-full overflow-hidden relative">
                    <img
                      src={getProductImage(product.product_name)}
                      alt={product.product_name}
                      className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-cyber-night via-cyber-night/70 to-transparent" />

                    {/* Badge on Image */}
                    <div className="absolute top-3 left-3">
                      <div
                        className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold backdrop-blur-sm ${style.badgeBg}`}
                      >
                        {style.badge}
                      </div>
                    </div>

                    {/* Product Name Overlay */}
                    <div className="absolute bottom-2 left-3 right-3">
                      <h3 className="font-bold text-white text-lg drop-shadow-lg line-clamp-1 group-hover:text-neon-green transition-colors">
                        {product.product_name || "Unknown Product"}
                      </h3>
                      <p className="text-xs text-gray-300/80 mt-0.5">
                        ID: {product.product_id}
                      </p>
                    </div>
                  </div>

                  {/* Card Content Below Image */}
                  <div className="p-4 relative z-10">
                    {/* Background Glow */}
                    <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-neon-green/10 to-transparent blur-2xl"></div>

                    <div className="flex items-start justify-between mb-3 relative z-10">
                      <div className="flex-1">
                        <Icon className={`w-6 h-6 ${style.iconColor} mb-2`} />
                      </div>
                    </div>

                    <p className="text-sm text-gray-400 mb-3 line-clamp-2 relative z-10">
                      {product.recommendation || "No recommendation available"}
                    </p>

                    <div className="flex items-center justify-end text-xs relative z-10">
                      <motion.span
                        className="text-neon-green font-mono"
                        whileHover={{ scale: 1.05 }}
                      >
                        View Details →
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

                {/* Live Pulse Graph */}
                {selectedProduct.forecast?.predictions &&
                  selectedProduct.forecast.predictions.length > 0 && (
                    <div className="glass-card p-4">
                      <h3 className="text-sm font-bold text-neon-green mb-3">
                        📈 Live Demand Pulse
                      </h3>
                      <ResponsiveContainer width="100%" height={200}>
                        <LineChart data={selectedProduct.forecast.predictions}>
                          <CartesianGrid
                            strokeDasharray="3 3"
                            stroke="#1a4d4d"
                          />
                          <XAxis
                            dataKey="date"
                            stroke="#6b7280"
                            style={{ fontSize: "11px" }}
                            tickFormatter={(date) =>
                              new Date(date).toLocaleDateString("en-GB", {
                                day: "2-digit",
                                month: "short",
                              })
                            }
                          />
                          <YAxis
                            stroke="#6b7280"
                            style={{ fontSize: "11px" }}
                          />
                          <RechartsTooltip
                            contentStyle={{
                              backgroundColor: "#0a1a1a",
                              border: "1px solid #39FF14",
                              borderRadius: "8px",
                            }}
                            labelFormatter={(date) =>
                              new Date(date).toLocaleDateString("en-GB")
                            }
                          />
                          <Line
                            type="monotone"
                            dataKey="predicted_quantity"
                            stroke="#39FF14"
                            strokeWidth={3}
                            dot={{ fill: "#39FF14", r: 4 }}
                            activeDot={{ r: 6 }}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                {/* XAI Model Metrics Tooltip */}
                {selectedProduct.forecast?.model_metrics && (
                  <div className="glass-card p-4 relative">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-sm font-bold text-neon-green">
                        🎯 Model Confidence
                      </h3>
                      <div className="relative">
                        <button
                          onMouseEnter={() => setShowMetricsTooltip(true)}
                          onMouseLeave={() => setShowMetricsTooltip(false)}
                          className="text-jamdani-teal hover:text-neon-green transition-colors"
                        >
                          <HelpCircle className="w-5 h-5" />
                        </button>

                        {/* XAI Tooltip */}
                        {showMetricsTooltip && (
                          <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="absolute right-0 bottom-full mb-2 w-72 bg-cyber-night border-2 border-neon-green rounded-lg p-4 shadow-neon-strong z-50"
                          >
                            <h4 className="text-xs font-bold text-neon-green mb-3">
                              🧠 Why This Prediction?
                            </h4>
                            <div className="space-y-2 text-xs">
                              <div className="flex justify-between">
                                <span className="text-gray-400">
                                  Model Accuracy (R²):
                                </span>
                                <span className="text-white font-bold">
                                  {(
                                    selectedProduct.forecast.model_metrics
                                      .r_squared * 100
                                  ).toFixed(1)}
                                  %
                                </span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-400">
                                  Trend Slope:
                                </span>
                                <span className="text-white font-bold">
                                  {selectedProduct.forecast.model_metrics
                                    .slope > 0
                                    ? "📈"
                                    : "📉"}{" "}
                                  {selectedProduct.forecast.model_metrics.slope.toFixed(
                                    2
                                  )}
                                </span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-400">
                                  Training Data:
                                </span>
                                <span className="text-white font-bold">
                                  {
                                    selectedProduct.forecast.model_metrics
                                      .training_days
                                  }{" "}
                                  days
                                </span>
                              </div>
                              {selectedProduct.forecast.model_metrics
                                .confidence && (
                                <div className="flex justify-between mt-3 pt-2 border-t border-neon-green/30">
                                  <span className="text-gray-400">
                                    Overall Confidence:
                                  </span>
                                  <span className="text-neon-green font-bold">
                                    {(
                                      selectedProduct.forecast.model_metrics
                                        .confidence * 100
                                    ).toFixed(0)}
                                    %
                                  </span>
                                </div>
                              )}
                            </div>
                            <p className="text-[10px] text-gray-500 mt-3 italic">
                              AI model trained on historical sales data using
                              linear regression
                            </p>
                          </motion.div>
                        )}
                      </div>
                    </div>
                    <p className="text-2xl font-bold text-white">
                      {selectedProduct.forecast.model_metrics.confidence
                        ? `${(
                            selectedProduct.forecast.model_metrics.confidence *
                            100
                          ).toFixed(0)}%`
                        : `${(
                            selectedProduct.forecast.model_metrics.r_squared *
                            100
                          ).toFixed(0)}%`}
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
