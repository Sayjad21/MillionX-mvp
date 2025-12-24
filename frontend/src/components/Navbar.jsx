import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Zap, X, MessageSquare, LayoutDashboard, Sparkles } from "lucide-react";

const Navbar = ({ currentScreen, onNavigate }) => {
  const [showQRModal, setShowQRModal] = useState(false);

  return (
    <>
      <nav className="fixed top-0 left-0 right-0 z-50 glass-card border-b border-neon-green/20">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo & Branding */}
            <div className="flex items-center space-x-3">
              <div className="relative">
                <Zap className="w-8 h-8 text-neon-green animate-pulse" />
                <div className="absolute inset-0 blur-lg bg-neon-green opacity-50"></div>
              </div>
              <div>
                <h1 className="text-2xl font-bold gradient-text">
                  MillionX AI
                </h1>
                <p className="text-xs text-gray-400">
                  Commerce OS • Build-a-thon 2025
                </p>
              </div>
            </div>

            {/* Navigation Menu */}
            <div className="flex items-center space-x-2">
              <button
                onClick={() => onNavigate?.("dashboard")}
                className={`px-4 py-2 rounded-lg transition-all flex items-center space-x-2 ${
                  currentScreen === "dashboard"
                    ? "bg-neon-green text-cyber-night font-bold"
                    : "text-gray-300 hover:text-neon-green hover:bg-neon-green/10"
                }`}
              >
                <LayoutDashboard className="w-4 h-4" />
                <span className="hidden sm:inline">Dashboard</span>
              </button>

              <button
                onClick={() => onNavigate?.("haggling")}
                className={`px-4 py-2 rounded-lg transition-all flex items-center space-x-2 ${
                  currentScreen === "haggling"
                    ? "bg-neon-green text-cyber-night font-bold"
                    : "text-gray-300 hover:text-neon-green hover:bg-neon-green/10"
                }`}
              >
                <Sparkles className="w-4 h-4" />
                <span className="hidden sm:inline">Haggling Arena</span>
              </button>

              <button
                onClick={() => setShowQRModal(true)}
                className="glass-card px-4 py-2 border border-jamdani-teal/50 hover:border-neon-green transition-all flex items-center space-x-2"
              >
                <MessageSquare className="w-4 h-4" />
                <span className="hidden sm:inline">WhatsApp</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* QR Code Modal */}
      <AnimatePresence>
        {showQRModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm"
            onClick={() => setShowQRModal(false)}
          >
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              className="glass-card p-8 max-w-md w-full mx-4 relative"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Close Button */}
              <button
                onClick={() => setShowQRModal(false)}
                className="absolute top-4 right-4 text-gray-400 hover:text-neon-green transition-colors"
              >
                <X className="w-6 h-6" />
              </button>

              {/* Content */}
              <div className="text-center">
                <div className="mb-4">
                  <MessageSquare className="w-12 h-12 text-neon-green mx-auto pulse-glow" />
                </div>
                <h2 className="text-2xl font-bold gradient-text mb-2">
                  Connect via WhatsApp
                </h2>
                <p className="text-gray-400 mb-6">
                  Scan the QR code to start chatting with MillionX AI Bot
                </p>

                {/* QR Code Placeholder */}
                <div className="bg-white p-6 rounded-lg mb-6 mx-auto w-64 h-64 flex items-center justify-center">
                  <div className="text-center">
                    <div className="w-48 h-48 bg-gray-200 rounded-lg flex items-center justify-center mb-2">
                      <div className="text-gray-500 text-sm">
                        [QR Code Here]
                        <div className="text-xs mt-2">
                          Use: wa.me/YOUR_NUMBER
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Instructions */}
                <div className="text-left glass-card p-4 space-y-2">
                  <h3 className="text-sm font-bold text-neon-green mb-2">
                    Quick Commands:
                  </h3>
                  <div className="text-xs text-gray-300 space-y-1">
                    <p>• "forecast" - Get inventory predictions</p>
                    <p>• "risk check" - Analyze COD orders</p>
                    <p>• "help" - View all commands</p>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default Navbar;
