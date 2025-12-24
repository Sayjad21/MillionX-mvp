import { useState } from 'react';
import { motion } from 'framer-motion';
import { QrCode, Zap, ArrowRight, Smartphone, Store } from 'lucide-react';

const Onboarding = ({ onComplete }) => {
  const [step, setStep] = useState(0);

  const handleSkipToDemo = () => {
    onComplete();
  };

  return (
    <div className="min-h-screen bg-cyber-gradient flex items-center justify-center p-6 overflow-hidden">
      {/* Background Effects */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-neon-green/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-jamdani-teal/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
      </div>

      {/* Main Content */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-4xl w-full relative z-10"
      >
        {/* Hero Section */}
        <div className="text-center mb-12">
          {/* Animated Logo */}
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', bounce: 0.5 }}
            className="inline-block mb-6"
          >
            <div className="relative">
              <Zap className="w-24 h-24 text-neon-green animate-pulse" />
              <div className="absolute inset-0 blur-2xl bg-neon-green opacity-50"></div>
            </div>
          </motion.div>

          {/* Title */}
          <motion.h1
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="text-6xl font-bold gradient-text mb-4"
          >
            MillionX AI
          </motion.h1>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="text-2xl text-gray-300 mb-2"
          >
            Self-Driving Commerce OS
          </motion.p>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="text-lg text-gray-400"
          >
            AI-Powered Inventory + COD Fraud Shield
          </motion.p>
        </div>

        {/* QR Code Card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5 }}
          className="glass-card p-8 neon-border max-w-2xl mx-auto mb-8"
        >
          <div className="grid md:grid-cols-2 gap-8 items-center">
            {/* Left: QR Code */}
            <div className="text-center">
              <div className="bg-white p-6 rounded-2xl inline-block mb-4 shadow-neon-strong">
                <div className="w-48 h-48 flex items-center justify-center">
                  <QrCode className="w-40 h-40 text-gray-800" />
                </div>
              </div>
              <p className="text-sm text-gray-400">
                Scan with WhatsApp to connect
              </p>
            </div>

            {/* Right: Instructions */}
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 rounded-full bg-neon-green/20 flex items-center justify-center flex-shrink-0">
                  <span className="text-neon-green font-bold">1</span>
                </div>
                <div>
                  <h3 className="font-bold text-white mb-1">Open WhatsApp</h3>
                  <p className="text-sm text-gray-400">On your mobile device</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 rounded-full bg-neon-green/20 flex items-center justify-center flex-shrink-0">
                  <span className="text-neon-green font-bold">2</span>
                </div>
                <div>
                  <h3 className="font-bold text-white mb-1">Scan QR Code</h3>
                  <p className="text-sm text-gray-400">Link your business account</p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 rounded-full bg-neon-green/20 flex items-center justify-center flex-shrink-0">
                  <span className="text-neon-green font-bold">3</span>
                </div>
                <div>
                  <h3 className="font-bold text-white mb-1">Start Chatting</h3>
                  <p className="text-sm text-gray-400">Get AI insights instantly</p>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Commands Preview */}
          <div className="mt-8 pt-8 border-t border-neon-green/20">
            <h3 className="text-sm font-bold text-neon-green mb-3">Quick Commands:</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
              <div className="glass-card p-2 text-center">
                <span className="text-gray-300">"forecast"</span>
              </div>
              <div className="glass-card p-2 text-center">
                <span className="text-gray-300">"risk check"</span>
              </div>
              <div className="glass-card p-2 text-center">
                <span className="text-gray-300">"labh koto?"</span>
              </div>
              <div className="glass-card p-2 text-center">
                <span className="text-gray-300">"help"</span>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Action Buttons */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="flex flex-col sm:flex-row gap-4 justify-center items-center"
        >
          <button
            onClick={handleSkipToDemo}
            className="neon-button flex items-center space-x-2 px-8 py-4 text-lg"
          >
            <span>Enter Dashboard</span>
            <ArrowRight className="w-5 h-5" />
          </button>

          <button
            onClick={handleSkipToDemo}
            className="glass-card px-8 py-4 text-lg border border-jamdani-teal/50 hover:border-neon-green transition-all"
          >
            <span className="text-gray-300">Demo Mode</span>
          </button>
        </motion.div>

        {/* Features Preview */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7 }}
          className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-4"
        >
          <div className="glass-card p-4 text-center">
            <Smartphone className="w-8 h-8 text-neon-green mx-auto mb-2" />
            <h4 className="font-bold text-white text-sm mb-1">Voice-First AI</h4>
            <p className="text-xs text-gray-400">Chat in Bangla/English</p>
          </div>

          <div className="glass-card p-4 text-center">
            <Store className="w-8 h-8 text-jamdani-teal mx-auto mb-2" />
            <h4 className="font-bold text-white text-sm mb-1">Smart Forecasting</h4>
            <p className="text-xs text-gray-400">Predict stockouts</p>
          </div>

          <div className="glass-card p-4 text-center">
            <Zap className="w-8 h-8 text-rickshaw-orange mx-auto mb-2" />
            <h4 className="font-bold text-white text-sm mb-1">COD Shield</h4>
            <p className="text-xs text-gray-400">Block fraudsters</p>
          </div>
        </motion.div>

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="mt-8 text-center text-sm text-gray-500"
        >
          National AI Build-a-thon 2025 • Built for Global South Merchants
        </motion.div>
      </motion.div>
    </div>
  );
};

export default Onboarding;
