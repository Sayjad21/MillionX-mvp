import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Shield,
  ShieldAlert,
  Search,
  Loader2,
  Phone,
  MapPin,
} from "lucide-react";
import { checkRiskScore } from "../api";

const RiskScanner = () => {
  const [phoneNumber, setPhoneNumber] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [isExpanded, setIsExpanded] = useState(false);

  const handleScan = async (e) => {
    e.preventDefault();
    if (!phoneNumber.trim()) return;

    setLoading(true);
    setResult(null);

    try {
      // Create mock order data with the phone number
      const orderData = {
        order_id: `ORD-${Date.now()}`,
        customer_phone: phoneNumber,
        customer_name: "Customer",
        amount: 2500,
        delivery_address: "Dhaka, Bangladesh",
        payment_method: "COD",
        order_date: new Date().toISOString(),
      };

      const data = await checkRiskScore(orderData);
      setResult(data);
      setIsExpanded(true);
    } catch (err) {
      setResult({
        risk_level: "ERROR",
        risk_score: 0,
        recommendation: "RETRY",
        error: "Failed to connect to API",
      });
    } finally {
      setLoading(false);
    }
  };

  const getRiskStyle = () => {
    if (!result) return null;

    const level = result.risk_level?.toUpperCase();
    if (level === "LOW") {
      return {
        bg: "bg-neon-green/10",
        border: "border-neon-green",
        text: "text-neon-green",
        icon: Shield,
        label: "SAFE TO DELIVER",
        glow: "shadow-neon",
      };
    } else if (level === "HIGH") {
      return {
        bg: "bg-rickshaw-orange/10",
        border: "border-rickshaw-orange",
        text: "text-rickshaw-orange",
        icon: ShieldAlert,
        label: "HIGH RISK",
        glow: "shadow-orange-glow",
      };
    } else {
      return {
        bg: "bg-yellow-500/10",
        border: "border-yellow-500",
        text: "text-yellow-500",
        icon: Shield,
        label: "MODERATE RISK",
        glow: "shadow-lg",
      };
    }
  };

  const style = getRiskStyle();

  return (
    <motion.div
      initial={{ x: 100, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      className={`${
        isExpanded ? "fixed" : "sticky"
      } top-24 right-6 z-40 transition-all duration-300`}
    >
      <div className="glass-card p-6 w-80 border-2 border-neon-green/30">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Shield className="w-6 h-6 text-neon-green pulse-glow" />
            <h3 className="font-bold text-lg gradient-text">COD Shield</h3>
          </div>
          {isExpanded && (
            <button
              onClick={() => setIsExpanded(false)}
              className="text-gray-400 hover:text-white text-sm"
            >
              Minimize
            </button>
          )}
        </div>

        <p className="text-xs text-gray-400 mb-4">
          Real-time fraud detection for Cash-on-Delivery orders
        </p>

        {/* Search Form */}
        <form onSubmit={handleScan} className="space-y-3">
          <div className="relative">
            <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              type="text"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              placeholder="Enter phone number..."
              className="w-full bg-cyber-night border border-jamdani-teal/50 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-neon-green transition-colors"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !phoneNumber.trim()}
            className={`w-full flex items-center justify-center space-x-2 px-4 py-2 rounded-lg font-bold transition-all ${
              loading
                ? "bg-gray-700 text-gray-400 cursor-not-allowed"
                : "neon-button"
            }`}
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Scanning...</span>
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                <span>Analyze Risk</span>
              </>
            )}
          </button>
        </form>

        {/* Loading Animation */}
        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-6 flex items-center justify-center"
          >
            <div className="relative w-32 h-32">
              {/* Radar Circles */}
              <div className="radar-sweep"></div>
              <div
                className="radar-sweep"
                style={{ animationDelay: "0.5s" }}
              ></div>
              <div
                className="radar-sweep"
                style={{ animationDelay: "1s" }}
              ></div>

              {/* Center Icon */}
              <div className="absolute inset-0 flex items-center justify-center">
                <Shield className="w-12 h-12 text-neon-green animate-pulse" />
              </div>
            </div>
          </motion.div>
        )}

        {/* Results */}
        <AnimatePresence>
          {result && !loading && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mt-6 space-y-4"
            >
              {/* Risk Badge */}
              <div
                className={`${style.bg} ${style.border} border-2 rounded-lg p-4 ${style.glow}`}
              >
                <div className="flex items-center justify-between mb-2">
                  {style.icon && (
                    <style.icon className={`w-8 h-8 ${style.text}`} />
                  )}
                  <div className="text-right">
                    <div className={`text-3xl font-bold ${style.text}`}>
                      {result.risk_score}
                    </div>
                    <div className="text-xs text-gray-400">Risk Score</div>
                  </div>
                </div>
                <div className={`text-sm font-bold ${style.text}`}>
                  {style.label}
                </div>
              </div>

              {/* Recommendation */}
              <div className="glass-card p-4">
                <h4 className="text-xs font-bold text-neon-green mb-2">
                  Recommendation:
                </h4>
                <p className="text-sm text-gray-300">{result.recommendation}</p>
              </div>

              {/* Risk Factors */}
              {result.factors && result.factors.length > 0 && (
                <div className="glass-card p-4">
                  <h4 className="text-xs font-bold text-neon-green mb-2">
                    Risk Factors:
                  </h4>
                  <ul className="space-y-2">
                    {result.factors.slice(0, 3).map((factor, idx) => (
                      <li
                        key={idx}
                        className="text-xs text-gray-400 flex items-start"
                      >
                        <span className="text-rickshaw-orange mr-2">•</span>
                        <span>{factor.description || factor.factor}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Actions */}
              <button
                onClick={() => {
                  setResult(null);
                  setPhoneNumber("");
                }}
                className="w-full text-sm text-gray-400 hover:text-neon-green transition-colors"
              >
                Scan Another →
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
};

export default RiskScanner;
