import { Shield, Check, Loader2, Link as LinkIcon } from "lucide-react";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface HeaderProps {
  onTrigger: () => void;
  isPhase2: boolean;
}

export function Header({ onTrigger, isPhase2 }: HeaderProps) {
  const [status, setStatus] = useState<"idle" | "loading" | "success">("idle");
  const [pulseActive, setPulseActive] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setPulseActive(true);
      setTimeout(() => setPulseActive(false), 3000);
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  const handleTrigger = () => {
    if (status !== "idle") return;
    setStatus("loading");
    setTimeout(() => {
      setStatus("success");
      setTimeout(() => {
        setStatus("idle");
        onTrigger();
      }, 1000);
    }, 2000);
  };

  return (
    <header className="h-16 border-b border-white/20 bg-slate-950/80 backdrop-blur-md flex items-center justify-between px-6 shrink-0 z-50 relative">
      <div className="flex items-center gap-6 w-full max-w-4xl">
        <div className="flex items-center gap-2 text-primary font-display font-bold text-xl tracking-wider">
          <Shield className="h-6 w-6" />
          <span>INCIDENT<span className="text-white">IQ</span></span>
        </div>

        <div className="flex-1 flex items-center gap-3">
          <div className="relative group max-w-[280px] w-full">
            <LinkIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-primary/50 group-focus-within:text-primary transition-colors" />
            <Input 
              defaultValue="INC-3928: Latency Spike" 
              className="pl-9 bg-slate-900/60 border-white/20 focus:border-primary/60 font-mono text-xs h-8 text-slate-100 rounded-sm" 
            />
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className={cn(
          "flex items-center gap-2 px-3 py-1.5 rounded-full border transition-all duration-1000",
          pulseActive 
            ? "bg-emerald-500/20 border-emerald-500/40 scale-105 shadow-[0_0_15px_rgba(16,185,129,0.2)]" 
            : "bg-emerald-500/5 border-emerald-500/10 opacity-70"
        )}>
          <div className={cn(
            "h-2 w-2 rounded-full bg-emerald-500",
            pulseActive ? "animate-pulse-ring" : ""
          )} />
          <span className="text-[10px] font-bold text-emerald-400 tracking-widest uppercase">SYSTEM OPTIMAL</span>
        </div>

        <div className="h-6 w-px bg-white/20 mx-2" />

        <Button 
          onClick={handleTrigger}
          disabled={status !== "idle" || isPhase2}
          className={cn(
            "min-w-[120px] h-9 font-display font-bold tracking-widest transition-all duration-500 rounded-sm",
            status === "success" ? "bg-emerald-600" : "bg-blue-600 hover:bg-blue-500 shadow-[0_0_20px_rgba(37,99,235,0.2)]"
          )}
        >
          {status === "idle" && "ANALYZE"}
          {status === "loading" && <Loader2 className="h-4 w-4 animate-spin" />}
          {status === "success" && <Check className="h-4 w-4" />}
        </Button>
      </div>
    </header>
  );
}
