import { useState } from "react";
import Navbar from "./components/Navbar";
import Onboarding from "./components/Onboarding";
import CommandCenter from "./components/CommandCenter";
import RiskScanner from "./components/RiskScanner";
import HagglingArena from "./components/HagglingArena";
import BhaiBotWidget from "./components/BhaiBotWidget";

function App() {
  const [filterQuery, setFilterQuery] = useState("");
  const [currentScreen, setCurrentScreen] = useState("onboarding"); // onboarding, dashboard, haggling
  const [showOnboarding, setShowOnboarding] = useState(true);

  // Handle onboarding completion
  const handleOnboardingComplete = () => {
    setShowOnboarding(false);
    setCurrentScreen("dashboard");
  };

  // Navigation handler
  const navigateTo = (screen) => {
    setCurrentScreen(screen);
  };

  // If showing onboarding
  if (showOnboarding) {
    return <Onboarding onComplete={handleOnboardingComplete} />;
  }

  return (
    <div className="min-h-screen bg-cyber-gradient">
      {/* Navigation */}
      <Navbar currentScreen={currentScreen} onNavigate={navigateTo} />

      {/* Main Content */}
      <main className="container mx-auto px-6 pt-24 pb-12">
        {/* Dashboard View */}
        {currentScreen === "dashboard" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Command Center - Takes up 2 columns on large screens */}
            <div className="lg:col-span-2">
              <CommandCenter filterQuery={filterQuery} />
            </div>

            {/* Risk Scanner - Sticky sidebar on large screens */}
            <div className="lg:col-span-1">
              <RiskScanner />
            </div>
          </div>
        )}

        {/* Haggling Arena View */}
        {currentScreen === "haggling" && <HagglingArena />}
      </main>

      {/* Floating AI Assistant */}
      <BhaiBotWidget onQuery={setFilterQuery} />

      {/* Background Effects */}
      <div className="fixed top-0 left-0 w-full h-full pointer-events-none overflow-hidden">
        {/* Gradient Orbs */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-neon-green/5 rounded-full blur-3xl"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-jamdani-teal/5 rounded-full blur-3xl"></div>
      </div>
    </div>
  );
}

export default App;
