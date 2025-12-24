import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, Send, X, Sparkles, MessageCircle, Activity } from "lucide-react";

const BhaiBotWidget = ({ onQuery }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [chatHistory, setChatHistory] = useState([
    {
      type: "bot",
      text: '🤖 Assalamu Alaikum! I am Bhai-Bot. Say "Show urgent stock" or type "forecast"!',
    },
  ]);
  const messagesEndRef = useRef(null);

  // Web Speech API Setup
  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = SpeechRecognition ? new SpeechRecognition() : null;

  useEffect(() => {
    if (recognition) {
      recognition.continuous = false;
      recognition.lang = "en-US"; // Change to 'bn-BD' for Bangla
      recognition.interimResults = false;

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        handleCommand(transcript);
        setIsListening(false);
      };

      recognition.onerror = (event) => {
        console.error("Speech error:", event.error);
        setIsListening(false);
        setChatHistory((prev) => [
          ...prev,
          {
            type: "bot",
            text: "⚠️ Voice not detected. Try again or type your command.",
          },
        ]);
      };

      recognition.onend = () => {
        setIsListening(false);
      };
    }
  }, []);

  const toggleListen = () => {
    if (!recognition) {
      setChatHistory((prev) => [
        ...prev,
        { type: "bot", text: "❌ Voice not supported. Try Chrome!" },
      ]);
      return;
    }
    if (isListening) {
      recognition.stop();
      setIsListening(false);
    } else {
      recognition.start();
      setIsListening(true);
      setChatHistory((prev) => [
        ...prev,
        { type: "bot", text: "🎙️ Listening... Speak now!" },
      ]);
    }
  };

  const handleCommand = (text) => {
    const lowerText = text.toLowerCase();
    const newMessages = [...chatHistory, { type: "user", text: text }];

    let response = "I didn't catch that. Try 'urgent' or 'forecast'.";

    // Simple Keyword Matching (Fake NLP)
    if (
      lowerText.includes("urgent") ||
      lowerText.includes("risk") ||
      lowerText.includes("emergency")
    ) {
      response = "🚨 Filtering for URGENT stock alerts...";
      onQuery?.("urgent");
    } else if (
      lowerText.includes("forecast") ||
      lowerText.includes("prediction") ||
      lowerText.includes("inventory")
    ) {
      response = "📊 Showing all demand forecasts.";
      onQuery?.("");
    } else if (lowerText.includes("profit") || lowerText.includes("labh")) {
      response =
        "💰 Your projected profit is ৳45,000 this week based on current trends.";
    } else if (lowerText.includes("stable") || lowerText.includes("good")) {
      response = "✅ Showing stable products with sufficient stock.";
      onQuery?.("stable");
    } else if (
      lowerText.includes("hello") ||
      lowerText.includes("salam") ||
      lowerText.includes("hi")
    ) {
      response = "🤖 Walaikum Assalam! How can I help your business today?";
    } else if (lowerText.includes("help")) {
      response = `🤖 Try saying:\n• "Show urgent stock"\n• "Check forecast"\n• "What's the profit?"\n• "Stable items"`;
    } else if (lowerText.includes("clear") || lowerText.includes("reset")) {
      response = "🔄 Filters cleared! Showing all products.";
      onQuery?.("");
    } else {
      // Generic search
      onQuery?.(text);
      response = `🔍 Filtering dashboard for "${text}"...`;
    }

    newMessages.push({ type: "bot", text: response });
    setChatHistory(newMessages);
    setMessage("");
  };

  const handleSend = (e) => {
    e.preventDefault();
    if (!message.trim()) return;
    handleCommand(message);
  };

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

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
                <div ref={messagesEndRef} />
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
                    placeholder="Type or speak your command..."
                    className="flex-1 bg-cyber-night border border-jamdani-teal/50 rounded-lg px-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-neon-green transition-colors"
                  />
                  <button
                    type="button"
                    onClick={toggleListen}
                    className={`p-2 rounded-lg transition-all ${
                      isListening
                        ? "bg-red-500 animate-pulse shadow-neon"
                        : "bg-jamdani-teal/20 hover:bg-jamdani-teal/30 border border-jamdani-teal/50"
                    }`}
                  >
                    <Mic
                      className={`w-5 h-5 ${
                        isListening ? "text-white" : "text-jamdani-teal"
                      }`}
                    />
                  </button>
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
