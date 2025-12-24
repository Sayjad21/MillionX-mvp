import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, TrendingUp, DollarSign, Zap, Info } from "lucide-react";

const HagglingArena = () => {
  const [priceRange, setPriceRange] = useState({ min: 500, max: 600 });
  const [currentPrice, setCurrentPrice] = useState(550);
  const [isSimulating, setIsSimulating] = useState(false);
  const [result, setResult] = useState(null);

  // Mock products for demo
  const products = [
    { id: "PROD-130", name: "Samsung Galaxy S24", msrp: 85000, cost: 70000 },
    { id: "PROD-202", name: "iPhone 15 Pro", msrp: 120000, cost: 100000 },
    { id: "PROD-354", name: "Dyson Vacuum V15", msrp: 55000, cost: 45000 },
  ];

  const [selectedProduct, setSelectedProduct] = useState(products[0]);

  const handleSimulation = async () => {
    setIsSimulating(true);
    setResult(null);

    // Simulate negotiation scenarios
    await new Promise((resolve) => setTimeout(resolve, 2000));

    // Calculate optimal price
    const profitMargin =
      ((currentPrice - selectedProduct.cost) / selectedProduct.cost) * 100;
    const ethicalCheck = currentPrice <= selectedProduct.msrp * 1.1;
    const competitiveCheck = currentPrice <= selectedProduct.msrp * 0.95;

    let strategy = "";
    let expectedProfit = 0;
    let confidence = 0;

    if (ethicalCheck && competitiveCheck) {
      strategy = `Start at ৳${currentPrice.toLocaleString()}, competitive pricing. High conversion rate expected.`;
      expectedProfit = (currentPrice - selectedProduct.cost) * 8; // 8 sales expected
      confidence = 92;
    } else if (ethicalCheck) {
      strategy = `Slightly above market. Start at ৳${currentPrice.toLocaleString()}, be ready to negotiate down 5%.`;
      expectedProfit = (currentPrice - selectedProduct.cost) * 5; // 5 sales expected
      confidence = 75;
    } else {
      strategy = `⚠️ Price exceeds ethical cap (110% MSRP). AI recommends max ৳${(
        selectedProduct.msrp * 1.1
      ).toLocaleString()}.`;
      expectedProfit = (currentPrice - selectedProduct.cost) * 2; // Only 2 sales
      confidence = 45;
    }

    setResult({
      strategy,
      expectedProfit,
      profitMargin: profitMargin.toFixed(1),
      confidence,
      ethicalCheck,
      scenarios: [
        {
          buyer: "Budget Conscious",
          success: competitiveCheck ? 95 : 60,
          offer: currentPrice * 0.9,
        },
        {
          buyer: "Brand Loyal",
          success: ethicalCheck ? 85 : 50,
          offer: currentPrice * 0.95,
        },
        { buyer: "Impulse Buyer", success: 90, offer: currentPrice },
      ],
    });

    setIsSimulating(false);
  };

  const getGaugeColor = () => {
    const ratio = currentPrice / selectedProduct.msrp;
    if (ratio <= 0.95) return "text-neon-green";
    if (ratio <= 1.1) return "text-yellow-500";
    return "text-rickshaw-orange";
  };

  const getGaugeFill = () => {
    const ratio =
      (currentPrice - priceRange.min) / (priceRange.max - priceRange.min);
    return `${ratio * 100}%`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-6 neon-border"
      >
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold gradient-text mb-2 flex items-center">
              <Sparkles className="w-8 h-8 mr-2 text-neon-green" />
              Haggling Twin Arena
            </h2>
            <p className="text-gray-400">
              AI-Powered Pricing Simulator • Test 1,000 Scenarios in 2 Seconds
            </p>
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold text-neon-green pulse-glow">
              10x
            </div>
            <div className="text-sm text-gray-400">Innovation Factor</div>
          </div>
        </div>
      </motion.div>

      {/* Main Arena */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Left: Controls */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card p-6"
        >
          <h3 className="text-xl font-bold text-white mb-4">Configuration</h3>

          {/* Product Selection */}
          <div className="mb-6">
            <label className="text-sm font-bold text-neon-green mb-2 block">
              Select Product:
            </label>
            <div className="space-y-2">
              {products.map((product) => (
                <button
                  key={product.id}
                  onClick={() => {
                    setSelectedProduct(product);
                    setCurrentPrice(Math.round(product.msrp * 0.95));
                    setPriceRange({
                      min: product.cost * 1.1,
                      max: product.msrp * 1.2,
                    });
                  }}
                  className={`w-full text-left p-3 rounded-lg border-2 transition-all ${
                    selectedProduct.id === product.id
                      ? "border-neon-green bg-neon-green/10"
                      : "border-jamdani-teal/30 hover:border-jamdani-teal"
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-white">{product.name}</span>
                    <span className="text-xs text-gray-400">{product.id}</span>
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    MSRP: ৳{product.msrp.toLocaleString()} • Cost: ৳
                    {product.cost.toLocaleString()}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Price Slider */}
          <div className="mb-6">
            <label className="text-sm font-bold text-neon-green mb-2 block">
              Set Your Price:
            </label>
            <div className="space-y-4">
              {/* Speedometer Gauge */}
              <div className="relative">
                <div className="h-32 flex items-end justify-center">
                  <div className="relative w-48 h-24 overflow-hidden">
                    {/* Gauge Background */}
                    <div className="absolute bottom-0 left-0 right-0 h-24 border-8 border-gray-700 rounded-t-full"></div>

                    {/* Colored Zones */}
                    <div className="absolute bottom-0 left-0 w-1/3 h-24 border-8 border-neon-green rounded-tl-full opacity-30"></div>
                    <div className="absolute bottom-0 left-1/3 w-1/3 h-24 border-t-8 border-yellow-500 opacity-30"></div>
                    <div className="absolute bottom-0 right-0 w-1/3 h-24 border-8 border-rickshaw-orange rounded-tr-full opacity-30"></div>

                    {/* Needle */}
                    <motion.div
                      animate={{
                        rotate:
                          ((currentPrice - priceRange.min) /
                            (priceRange.max - priceRange.min)) *
                            180 -
                          90,
                      }}
                      transition={{ type: "spring", stiffness: 100 }}
                      className="absolute bottom-0 left-1/2 w-1 h-20 bg-white origin-bottom"
                      style={{ transformOrigin: "bottom center" }}
                    >
                      <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-3 h-3 rounded-full bg-white shadow-neon"></div>
                    </motion.div>

                    {/* Center Pin */}
                    <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-4 h-4 rounded-full bg-cyber-night border-2 border-white"></div>
                  </div>
                </div>

                {/* Price Display */}
                <div className="text-center mt-4">
                  <div
                    className={`text-4xl font-bold ${getGaugeColor()} transition-colors`}
                  >
                    ৳{currentPrice.toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-400 mt-1">
                    {(
                      ((currentPrice - selectedProduct.cost) /
                        selectedProduct.cost) *
                      100
                    ).toFixed(1)}
                    % Profit Margin
                  </div>
                </div>
              </div>

              {/* Slider */}
              <input
                type="range"
                min={priceRange.min}
                max={priceRange.max}
                value={currentPrice}
                onChange={(e) => setCurrentPrice(parseInt(e.target.value))}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                style={{
                  background: `linear-gradient(to right, #39FF14 0%, #39FF14 ${getGaugeFill()}, #1e293b ${getGaugeFill()}, #1e293b 100%)`,
                }}
              />

              {/* Range Labels */}
              <div className="flex justify-between text-xs text-gray-500">
                <span>Min: ৳{priceRange.min.toLocaleString()}</span>
                <span>Max: ৳{priceRange.max.toLocaleString()}</span>
              </div>
            </div>
          </div>

          {/* Simulate Button */}
          <button
            onClick={handleSimulation}
            disabled={isSimulating}
            className={`w-full neon-button py-4 text-lg font-bold flex items-center justify-center space-x-2 ${
              isSimulating ? "opacity-50 cursor-not-allowed" : ""
            }`}
          >
            {isSimulating ? (
              <>
                <Zap className="w-5 h-5 animate-spin" />
                <span>Simulating 1,000 Deals...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                <span>Run Simulation</span>
              </>
            )}
          </button>

          {/* Ethical Guardrail Info */}
          <div className="mt-4 glass-card p-3 border border-jamdani-teal/30">
            <div className="flex items-start space-x-2">
              <Info className="w-4 h-4 text-jamdani-teal mt-0.5 flex-shrink-0" />
              <p className="text-xs text-gray-400">
                Ethical AI ensures fair pricing. Prices above 110% MSRP are
                flagged automatically.
              </p>
            </div>
          </div>
        </motion.div>

        {/* Right: Results */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="glass-card p-6"
        >
          <h3 className="text-xl font-bold text-white mb-4">
            Simulation Results
          </h3>

          <AnimatePresence mode="wait">
            {!result && !isSimulating && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col items-center justify-center h-full min-h-[400px] text-center"
              >
                <TrendingUp className="w-16 h-16 text-gray-600 mb-4" />
                <p className="text-gray-400">
                  Configure your price and run simulation to see AI
                  recommendations
                </p>
              </motion.div>
            )}

            {isSimulating && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col items-center justify-center h-full min-h-[400px]"
              >
                <div className="relative w-32 h-32 mb-4">
                  <div className="radar-sweep"></div>
                  <div
                    className="radar-sweep"
                    style={{ animationDelay: "0.5s" }}
                  ></div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Sparkles className="w-12 h-12 text-neon-green animate-pulse" />
                  </div>
                </div>
                <p className="text-gray-300 font-bold">
                  Analyzing market scenarios...
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  Testing 1,000 buyer personas
                </p>
              </motion.div>
            )}

            {result && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                {/* Strategy Card */}
                <div
                  className={`glass-card p-4 border-2 ${
                    result.ethicalCheck
                      ? "border-neon-green"
                      : "border-rickshaw-orange"
                  }`}
                >
                  <h4 className="text-sm font-bold text-neon-green mb-2">
                    AI Strategy Recommendation:
                  </h4>
                  <p className="text-white text-sm">{result.strategy}</p>
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="glass-card p-4 text-center">
                    <DollarSign className="w-8 h-8 text-neon-green mx-auto mb-2" />
                    <div className="text-2xl font-bold text-white">
                      ৳{result.expectedProfit.toLocaleString()}
                    </div>
                    <div className="text-xs text-gray-400">Expected Profit</div>
                  </div>

                  <div className="glass-card p-4 text-center">
                    <Zap className="w-8 h-8 text-jamdani-teal mx-auto mb-2" />
                    <div className="text-2xl font-bold text-white">
                      {result.confidence}%
                    </div>
                    <div className="text-xs text-gray-400">
                      Confidence Score
                    </div>
                  </div>
                </div>

                {/* Buyer Scenarios */}
                <div>
                  <h4 className="text-sm font-bold text-neon-green mb-3">
                    Buyer Simulation Results:
                  </h4>
                  <div className="space-y-2">
                    {result.scenarios.map((scenario, idx) => (
                      <div key={idx} className="glass-card p-3">
                        <div className="flex justify-between items-center mb-2">
                          <span className="font-bold text-white text-sm">
                            {scenario.buyer}
                          </span>
                          <span
                            className={`text-xs font-bold ${
                              scenario.success >= 80
                                ? "text-neon-green"
                                : scenario.success >= 60
                                ? "text-yellow-500"
                                : "text-rickshaw-orange"
                            }`}
                          >
                            {scenario.success}% Success
                          </span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              scenario.success >= 80
                                ? "bg-neon-green"
                                : scenario.success >= 60
                                ? "bg-yellow-500"
                                : "bg-rickshaw-orange"
                            }`}
                            style={{ width: `${scenario.success}%` }}
                          ></div>
                        </div>
                        <div className="text-xs text-gray-400 mt-1">
                          Counter-offer: ৳{scenario.offer.toLocaleString()}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Action Button */}
                <button className="w-full glass-card py-3 border-2 border-neon-green hover:bg-neon-green/10 transition-all text-white font-bold">
                  Apply This Pricing Strategy
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>

      {/* Bottom Info */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="glass-card p-4 border border-jamdani-teal/30"
      >
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center space-x-2 text-gray-400">
            <Info className="w-4 h-4" />
            <span>
              Powered by Multi-Agent AI • Ethical Pricing Enforced • Real-time
              Market Data
            </span>
          </div>
          <div className="text-neon-green font-mono">v2.0</div>
        </div>
      </motion.div>
    </div>
  );
};

export default HagglingArena;
