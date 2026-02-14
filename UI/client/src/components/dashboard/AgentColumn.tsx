import { useRef, useEffect, useState } from "react";
import { GitBranch, Server, Slack, Lock, ChevronUp, Loader2, Activity, Waves, X, Maximize2 } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { DEFAULT_PROMPTS } from "@/lib/api";

export type AgentType = "github" | "aws" | "slack";

interface LogEntry {
  id: string;
  timestamp: string;
  level: "info" | "warn" | "error" | "success";
  message: string;
}

interface AgentColumnProps {
  type: AgentType;
  isPhase2: boolean;
  logs: LogEntry[];
  isAnalyzing: boolean;
}

const AGENT_CONFIG = {
  github: {
    icon: GitBranch,
    name: "GITHUB AGENT",
    borderColor: "border-[hsl(270,95%,65%)]",
    glowColor: "shadow-[0_0_30px_rgba(168,85,247,0.1)]",
    textColor: "text-[hsl(270,95%,65%)]",
    bgColor: "bg-[hsl(270,95%,65%,0.05)]",
  },
  aws: {
    icon: Server,
    name: "AWS INFRA AGENT",
    borderColor: "border-[hsl(25,95%,55%)]",
    glowColor: "shadow-[0_0_30px_rgba(249,115,22,0.1)]",
    textColor: "text-[hsl(25,95%,55%)]",
    bgColor: "bg-[hsl(25,95%,55%,0.05)]",
  },
  slack: {
    icon: Slack,
    name: "SLACK AGENT",
    borderColor: "border-[hsl(150,70%,45%)]",
    glowColor: "shadow-[0_0_30px_rgba(16,185,129,0.1)]",
    textColor: "text-[hsl(150,70%,45%)]",
    bgColor: "bg-[hsl(150,70%,45%,0.05)]",
  },
};

export function AgentColumn({ type, isPhase2, logs, isAnalyzing }: AgentColumnProps) {
  const config = AGENT_CONFIG[type];
  const Icon = config.icon;
  const scrollRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [isZoomed, setIsZoomed] = useState(false);
  
  // Map agent type to default prompt key
  const getDefaultPrompt = () => {
    switch (type) {
      case "github":
        return DEFAULT_PROMPTS.GITHUB_AGENT_PROMPT;
      case "aws":
        return DEFAULT_PROMPTS.AWS_CLOUDWATCH_AGENT_PROMPT;
      case "slack":
        return DEFAULT_PROMPTS.SLACK_AGENT_PROMPT;
      default:
        return "";
    }
  };
  
  const [prompt, setPrompt] = useState(getDefaultPrompt());

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      const scrollElement = scrollRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollElement) {
        scrollElement.scrollTop = scrollElement.scrollHeight;
      }
    }
  }, [logs, autoScroll, isZoomed]);

  const AgentHeader = ({ inModal = false }) => (
    <div className={cn("p-4 border-b flex items-center justify-between bg-slate-950/60", config.borderColor)}>
      <div className="flex items-center gap-3">
        <div className={cn("p-2 rounded-lg relative overflow-hidden", config.bgColor)}>
          <Icon className={cn("h-5 w-5 relative z-10", config.textColor)} />
          <div className="absolute inset-0 bg-gradient-to-t from-white/10 to-transparent animate-pulse" />
        </div>
        <div>
          <h3 className={cn("font-display font-bold tracking-widest text-xs", config.textColor)}>{config.name}</h3>
          <div className="flex items-center gap-2 mt-0.5">
             <span className="relative flex h-1.5 w-1.5">
                <span className={cn("animate-ping absolute inline-flex h-full w-full rounded-full opacity-75", config.bgColor)}></span>
                <span className={cn("relative inline-flex rounded-full h-1.5 w-1.5", config.textColor.replace('text-', 'bg-'))}></span>
              </span>
              <span className="text-[9px] text-slate-300 font-mono tracking-tighter">
                {isAnalyzing ? "ANALYZING_DATA" : "WAITING_FOR_COMMAND"}
              </span>
          </div>
        </div>
      </div>
      {!inModal && (
        <Button 
          variant="ghost" 
          size="icon" 
          className="h-8 w-8 text-slate-300 hover:text-white hover:bg-white/15"
          onClick={(e) => {
            e.stopPropagation();
            setIsZoomed(true);
          }}
        >
          <Maximize2 className="h-4 w-4" />
        </Button>
      )}
    </div>
  );

  const PromptSection = () => (
    <div 
      className="border-b border-white/10 bg-slate-950/40 p-3"
      onClick={(e) => e.stopPropagation()}
    >
      <Textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        onClick={(e) => e.stopPropagation()}
        className={cn(
          "min-h-[60px] w-full bg-slate-900/50 border-white/10 text-[11px] font-mono text-slate-200 placeholder:text-slate-500",
          "focus-visible:ring-1 focus-visible:ring-white/20 focus-visible:border-white/20",
          "resize-none"
        )}
        placeholder="Enter prompt for this agent..."
      />
    </div>
  );

  const AgentContent = () => (
    <div className="h-full relative bg-slate-950/50 group flex flex-col">
      {!isAnalyzing && logs.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center p-8 z-10">
           <div className="text-center space-y-4 animate-in fade-in zoom-in duration-1000">
              <div className="relative inline-block">
                  <Waves className="h-12 w-12 text-slate-800 animate-[pulse_3s_infinite]" />
                  <Activity className="h-6 w-6 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-slate-700/50" />
              </div>
              <div className="space-y-1">
                  <p className="text-slate-300 font-mono text-[10px] tracking-[0.3em] font-bold uppercase border-y border-white/15 py-2 px-4 bg-white/8 backdrop-blur-sm">
                      Waiting for analysis trigger
                  </p>
              </div>
           </div>
        </div>
      )}

      {isAnalyzing && logs.length === 0 && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-slate-950/40 backdrop-blur-[2px] z-10">
           <div className="relative">
              <Loader2 className={cn("h-10 w-10 animate-spin opacity-40", config.textColor)} />
              <div className={cn("absolute inset-0 animate-ping rounded-full border border-current opacity-20", config.textColor)} />
           </div>
           <p className={cn("font-mono text-[9px] tracking-[0.4em] uppercase font-bold", config.textColor)}>Initializing Neural Link</p>
        </div>
      )}

      {logs.length > 0 && (
        <ScrollArea ref={scrollRef} className="h-full w-full">
            <div className="p-4 space-y-3 font-mono text-[11px] leading-relaxed">
                {logs.map((log) => {
                  // Truncate tool output messages when minimized (not in modal)
                  const isToolOutput = log.message.startsWith("Tool output:");
                  const displayMessage = !isZoomed && isToolOutput && log.message.length > 150
                    ? log.message.substring(0, 150) + "..."
                    : log.message;
                  
                  return (
                    <div key={log.id} className="flex gap-3 animate-in fade-in slide-in-from-left-1 duration-300">
                        <span className="text-slate-400 shrink-0 font-light select-none">[{log.timestamp}]</span>
                        <span className={cn(
                            "break-all",
                            log.level === "error" ? "text-red-400 font-medium" :
                            log.level === "warn" ? "text-orange-400" :
                            log.level === "success" ? "text-emerald-400" :
                            "text-slate-200"
                        )}>
                            {displayMessage}
                        </span>
                    </div>
                  );
                })}
                <div className="h-4" />
            </div>
        </ScrollArea>
      )}
    </div>
  );

  return (
    <>
      <div className={cn(
        "relative flex flex-col transition-all duration-700 ease-[cubic-bezier(0.25,1,0.5,1)]",
        "border rounded-xl overflow-hidden glass-card cursor-pointer group/card",
        config.borderColor,
        config.glowColor,
        // CRITICAL FIX: Always maintain proper height
        "h-full",
        isPhase2 ? "min-h-[140px]" : ""
      )}
      onClick={() => setIsZoomed(true)}
      >
        <AgentHeader />
        <PromptSection />
        <AgentContent />
      </div>

      <Dialog open={isZoomed} onOpenChange={setIsZoomed}>
        <DialogContent className="max-w-[90vw] w-[1200px] h-[80vh] bg-slate-950/95 backdrop-blur-2xl border-white/10 p-0 overflow-hidden flex flex-col gap-0 shadow-[0_0_50px_rgba(0,0,0,0.5)]">
          <AgentHeader inModal />
          <PromptSection />
          <div className="flex-1 overflow-auto">
             <AgentContent />
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
