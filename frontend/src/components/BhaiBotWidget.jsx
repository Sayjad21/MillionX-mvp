import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, Send, X, Sparkles, MessageCircle } from "lucide-react";

const BhaiBotWidget = ({ onQuery }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState([
    {
      type: "bot",
      text: 'Assalamu Alaikum! I\'m your AI Assistant. Type "forecast" to filter products, or ask me anything!',
    },
  ]);

  const handleSend = (e) => {
    e.preventDefault();
    if (!message.trim()) return;

    // Add user message
    const userMessage = { type: "user", text: message };
    setChatHistory((prev) => [...prev, userMessage]);

    // Process command
    const query = message.toLowerCase();
    let botResponse = "";

    if (query.includes("forecast") || query.includes("inventory")) {
      onQuery?.(""); // Show all forecasts
      botResponse = "📊 Displaying all inventory forecasts in the dashboard!";
    } else if (query.includes("urgent")) {
      onQuery?.("urgent");
      botResponse =
        "🚨 Filtering for URGENT products that need immediate attention.";
    } else if (query.includes("stable")) {
      onQuery?.("stable");
      botResponse = "✅ Showing stable products with sufficient stock.";
    } else if (query.includes("help")) {
      botResponse = `
🤖 Available Commands:
• "forecast" - View all forecasts
• "urgent" - Show urgent items
• "stable" - Show stable items
• "risk check" - Open COD Shield
• "clear" - Reset filters
      `.trim();
    } else if (query.includes("clear") || query.includes("reset")) {
      onQuery?.("");
      botResponse = "🔄 Filters cleared! Showing all products.";
    } else if (query.includes("risk")) {
      botResponse =
        "🛡️ Use the COD Shield panel on the right to check risk scores!";
    } else {
      // Generic response
      onQuery?.(message);
      botResponse = `🔍 Filtering dashboard for "${message}"...`;
    }

    // Add bot response
    const botMessage = { type: "bot", text: botResponse };
    setChatHistory((prev) => [...prev, botMessage]);

    // Clear input
    setMessage("");
  };

  const quickCommands = [
    { label: "📊 Forecast", value: "forecast" },
    { label: "🚨 Urgent", value: "urgent" },
    { label: "✅ Stable", value: "stable" },
    { label: "❓ Help", value: "help" },
  ];

  return (
    <>
      {/* Floating Action Button */}
      <AnimatePresence>
        {!isOpen && (
          <motion.button
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            exit={{ scale: 0, rotate: 180 }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => setIsOpen(true)}
            className="fixed bottom-6 right-6 z-50 w-16 h-16 rounded-full bg-neon-green text-cyber-night shadow-neon-strong flex items-center justify-center group"
          >
            <Mic className="w-8 h-8 group-hover:animate-pulse" />
            <div className="absolute inset-0 rounded-full bg-neon-green blur-xl opacity-50 animate-pulse"></div>
          </motion.button>
        )}
      </AnimatePresence>

      {/* Chat Widget */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 100, scale: 0.8 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 100, scale: 0.8 }}
            className="fixed bottom-6 right-6 z-50 w-96 max-w-[calc(100vw-3rem)]"
          >
            <div className="glass-card border-2 border-neon-green/50 shadow-neon-strong">
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b border-neon-green/30">
                <div className="flex items-center space-x-2">
                  <div className="relative">
                    <Sparkles className="w-6 h-6 text-neon-green animate-pulse" />
                    <div className="absolute inset-0 blur-lg bg-neon-green opacity-50"></div>
                  </div>
                  <div>
                    <h3 className="font-bold gradient-text">Bhai Bot</h3>
                    <p className="text-xs text-gray-400">AI Assistant</p>
                  </div>
                </div>
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-gray-400 hover:text-neon-green transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Chat History */}
              <div className="h-80 overflow-y-auto p-4 space-y-3 custom-scrollbar">
                {chatHistory.map((msg, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, x: msg.type === "user" ? 20 : -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className={`flex ${
                      msg.type === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg p-3 ${
                        msg.type === "user"
                          ? "bg-neon-green text-cyber-night font-medium"
                          : "bg-cyber-night/80 border border-jamdani-teal/30 text-gray-200"
                      }`}
                    >
                      <p className="text-sm whitespace-pre-line">{msg.text}</p>
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* Quick Commands */}
              <div className="px-4 py-2 border-t border-neon-green/20">
                <div className="flex flex-wrap gap-2">
                  {quickCommands.map((cmd) => (
                    <button
                      key={cmd.value}
                      onClick={() => {
                        setMessage(cmd.value);
                        setTimeout(() => {
                          handleSend({ preventDefault: () => {} });
                        }, 100);
                      }}
                      className="text-xs px-3 py-1 rounded-full bg-cyber-night border border-jamdani-teal/50 hover:border-neon-green hover:text-neon-green transition-all"
                    >
                      {cmd.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Input Form */}
              <form
                onSubmit={handleSend}
                className="p-4 border-t border-neon-green/30"
              >
                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Type a command..."
                    className="flex-1 bg-cyber-night border border-jamdani-teal/50 rounded-lg px-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-neon-green transition-colors"
                  />
                  <button
                    type="submit"
                    disabled={!message.trim()}
                    className={`p-2 rounded-lg transition-all ${
                      message.trim()
                        ? "bg-neon-green text-cyber-night shadow-neon hover:shadow-neon-strong"
                        : "bg-gray-700 text-gray-500 cursor-not-allowed"
                    }`}
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>
              </form>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default BhaiBotWidget;
