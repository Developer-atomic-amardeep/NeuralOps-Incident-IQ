import { useState, useEffect, useRef } from "react";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { AgentColumn, AgentType } from "./AgentColumn";
import { SmokingGunPanel } from "./Phase2Layout";
import { cn } from "@/lib/utils";
import { streamInvestigatorAnalysis, healthCheck, AgentLogEntry, LogUpdateAction } from "@/lib/api";

export function Dashboard() {
  const [phase, setPhase] = useState<1 | 2>(1);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isPanelMinimized, setIsPanelMinimized] = useState(false);
  const [logs, setLogs] = useState<Record<AgentType, AgentLogEntry[]>>({
    github: [],
    aws: [],
    slack: []
  });
  const [progress, setProgress] = useState(0);
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean | null>(null);
  const [finalResponse, setFinalResponse] = useState<string>("");
  const abortControllerRef = useRef<AbortController | null>(null);

  // Check backend health on mount
  useEffect(() => {
    const checkHealth = async () => {
      const healthy = await healthCheck();
      setIsBackendHealthy(healthy);
      
      if (!healthy) {
        console.error("Backend Connection Failed: Unable to connect to the Incident IQ backend");
      } else {
        console.log("Backend Connected: Successfully connected to Incident IQ API");
      }
    };
    
    checkHealth();
  }, []);

  // Simulate progress during analysis
  useEffect(() => {
    if (!isAnalyzing) return;

    const interval = setInterval(() => {
      setProgress(p => {
        const next = Math.min(p + 0.8, 95); // Cap at 95% until completion
        return next;
      });
    }, 500);

    return () => clearInterval(interval);
  }, [isAnalyzing]);

  const handleTrigger = async () => {
    if (!isBackendHealthy) {
      console.error("Backend Unavailable: Cannot start analysis");
      alert("Backend server is not responding. Please check the connection.");
      return;
    }

    // Reset state
    setLogs({ github: [], aws: [], slack: [] });
    setIsAnalyzing(true);
    setPhase(1);
    setProgress(0);
    setIsPanelMinimized(false);
    setFinalResponse("");

    try {
      // Start streaming
      const controller = await streamInvestigatorAnalysis(
        // onEvent callback - receives logs for each agent
        (agentType, action: LogUpdateAction) => {
          setLogs(prev => {
            const currentLogs = prev[agentType];
            
            if (action.type === "add") {
              // Add new log entry
              return {
                ...prev,
                [agentType]: [...currentLogs.slice(-50), action.logEntry] // Keep last 50 logs
              };
            } else if (action.type === "update") {
              // Update existing log entry by ID
              const updatedLogs = currentLogs.map(log => 
                log.id === action.id 
                  ? { ...log, ...action.updates }
                  : log
              );
              return {
                ...prev,
                [agentType]: updatedLogs
              };
            }
            
            return prev;
          });
        },
        
        // onComplete callback
        (response) => {
          setIsAnalyzing(false);
          setProgress(100);
          
          if (response) {
            setFinalResponse(response);
            // Short delay before showing critical finding
            setTimeout(() => {
              setPhase(2);
            }, 500);
          } else {
            console.log("Analysis Complete: No critical findings detected");
          }
        },
        
        // onError callback
        (error) => {
          setIsAnalyzing(false);
          setProgress(0);
          console.error("Stream error:", error);
          alert("Analysis failed: " + (error.message || "An error occurred"));
        }
      );

      abortControllerRef.current = controller;
    } catch (error) {
      setIsAnalyzing(false);
      setProgress(0);
      console.error("Failed to start analysis:", error);
      alert("Failed to start analysis. Could not connect to the backend.");
    }
  };

  const handleClosePanel = () => {
    setPhase(1);
    setIsPanelMinimized(false);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Agent columns should shrink only when panel is visible (phase 2 AND not minimized)
  const shouldShrinkColumns = phase === 2 && !isPanelMinimized;

  return (
    <div className="flex flex-col h-screen bg-[url('/grid-pattern.svg')] bg-cover overflow-hidden">
      <div className="absolute inset-0 bg-slate-950/75 pointer-events-none" />
      
      <Header onTrigger={handleTrigger} isPhase2={phase === 2 || isAnalyzing} />

      {/* Desktop layout - Fixed height with internal scrolling */}
      <div className="hidden lg:flex flex-1 overflow-hidden relative z-10">
        <main className="flex-1 flex flex-col p-6 gap-6 overflow-hidden transition-all duration-700">
          <div 
            className={cn(
              "grid grid-cols-3 gap-6 transition-all duration-700 ease-[cubic-bezier(0.25,1,0.5,1)]",
              shouldShrinkColumns ? "h-[30%] shrink-0" : "h-full"
            )}
          >
            <AgentColumn type="github" isPhase2={shouldShrinkColumns} logs={logs.github} isAnalyzing={isAnalyzing} />
            <AgentColumn type="aws" isPhase2={shouldShrinkColumns} logs={logs.aws} isAnalyzing={isAnalyzing} />
            <AgentColumn type="slack" isPhase2={shouldShrinkColumns} logs={logs.slack} isAnalyzing={isAnalyzing} />
          </div>

          {phase === 2 && !isPanelMinimized && (
            <SmokingGunPanel 
              onClose={handleClosePanel}
              onMinimize={() => setIsPanelMinimized(true)}
              finalResponse={finalResponse}
            />
          )}
        </main>

        <Sidebar progress={Math.floor(progress)} isAnalyzing={isAnalyzing} finalResponse={finalResponse} />
      </div>

      {/* Mobile/Tablet layout - Scrollable with proper spacing */}
      <div className="flex lg:hidden flex-1 overflow-y-auto relative z-10">
        <main className="flex-1 flex flex-col p-3 sm:p-4 gap-3 sm:gap-4 pb-20">
          {/* Agent columns - each with fixed height on mobile */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
            <div className={cn(
              "transition-all duration-700",
              shouldShrinkColumns ? "h-48" : "h-96"
            )}>
              <AgentColumn type="github" isPhase2={shouldShrinkColumns} logs={logs.github} isAnalyzing={isAnalyzing} />
            </div>
            <div className={cn(
              "transition-all duration-700",
              shouldShrinkColumns ? "h-48" : "h-96"
            )}>
              <AgentColumn type="aws" isPhase2={shouldShrinkColumns} logs={logs.aws} isAnalyzing={isAnalyzing} />
            </div>
            <div className={cn(
              "transition-all duration-700 sm:col-span-2",
              shouldShrinkColumns ? "h-48" : "h-96"
            )}>
              <AgentColumn type="slack" isPhase2={shouldShrinkColumns} logs={logs.slack} isAnalyzing={isAnalyzing} />
            </div>
          </div>

          {phase === 2 && !isPanelMinimized && (
            <div className="min-h-[400px]">
              <SmokingGunPanel 
                onClose={handleClosePanel}
                onMinimize={() => setIsPanelMinimized(true)}
                finalResponse={finalResponse}
              />
            </div>
          )}
        </main>
        
        {/* Mobile progress indicator */}
        {isAnalyzing && (
          <div className="fixed bottom-0 left-0 right-0 bg-slate-950/95 backdrop-blur-sm border-t border-slate-800 p-4 z-50">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-mono text-slate-200">Analysis Progress</span>
              <span className="text-sm font-bold text-primary">{Math.floor(progress)}%</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-primary to-blue-400 transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Minimized panel floating button - shows when minimized */}
      {phase === 2 && isPanelMinimized && (
        <SmokingGunPanel 
          onClose={handleClosePanel}
          onMinimize={() => setIsPanelMinimized(true)}
          onRestore={() => setIsPanelMinimized(false)}
          isMinimized={true}
          finalResponse={finalResponse}
        />
      )}
    </div>
  );
}
