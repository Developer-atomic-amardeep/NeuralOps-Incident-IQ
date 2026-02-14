import { useState, useEffect } from "react";
import { FileText, Database, Server, Clock, Download, Loader2, Binary, Cpu, Share2 } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { generatePDFFromMarkdown } from "@/lib/pdfGenerator";

interface SidebarProps {
  progress: number;
  isAnalyzing: boolean;
  finalResponse?: string;
}

export function Sidebar({ progress, isAnalyzing, finalResponse = "" }: SidebarProps) {
  const [sessionTime, setSessionTime] = useState<string>("0m");
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);

  const handleDownloadPDF = async () => {
    if (!finalResponse) return;
    
    setIsGeneratingPDF(true);
    try {
      await generatePDFFromMarkdown(finalResponse, {
        title: "Incident Analysis Report",
        fontSize: 11,
        lineHeight: 1.5,
        margin: 20
      });
    } catch (error) {
      console.error("Error generating PDF:", error);
      alert("Failed to generate PDF. Please try again.");
    } finally {
      setIsGeneratingPDF(false);
    }
  };

  useEffect(() => {
    const startTime = Date.now();

    const updateSessionTime = () => {
      const elapsed = Date.now() - startTime;
      const seconds = Math.floor(elapsed / 1000);
      const minutes = Math.floor(seconds / 60);
      const hours = Math.floor(minutes / 60);
      const days = Math.floor(hours / 24);

      let formattedTime = "";
      if (days > 0) {
        formattedTime = `${days}d ${hours % 24}h`;
      } else if (hours > 0) {
        formattedTime = `${hours}h ${minutes % 60}m`;
      } else {
        formattedTime = `${minutes}m`;
      }

      setSessionTime(formattedTime);
    };

    updateSessionTime();
    const interval = setInterval(updateSessionTime, 1000);

    return () => clearInterval(interval);
  }, []);
  return (
    <div className="w-80 border-l border-white/20 bg-slate-950/85 backdrop-blur-xl flex flex-col h-full shrink-0">
      <div className="p-6 border-b border-white/20">
        <h2 className="font-display font-bold text-lg text-white mb-1">ANALYSIS VAULT</h2>
        <p className="text-xs text-slate-200">Secure Artifact Storage</p>
      </div>

      <div className="flex-1 p-6 space-y-8 overflow-y-auto tech-scrollbar">
        
        {/* PDF Generation Visual */}
        <div className="space-y-4">
          <div className="flex justify-between items-end">
            <span className="text-xs font-mono text-blue-400 tracking-tighter">REPORT_GEN_V2.PDF</span>
            <span className="text-xs font-mono text-slate-200">{progress}%</span>
          </div>
          <Progress value={progress} className="h-1.5 bg-slate-900" indicatorClassName="bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.6)]" />
          
          <div className="relative aspect-[3/4] bg-white/10 border border-white/20 rounded-md overflow-hidden p-3 space-y-3">
             {isAnalyzing && progress < 100 ? (
               <div className="absolute inset-0 flex flex-col items-center justify-center p-6 space-y-4">
                  <div className="grid grid-cols-2 gap-2 opacity-20">
                    <Binary className="h-6 w-6 animate-pulse" />
                    <Cpu className="h-6 w-6 animate-pulse delay-100" />
                    <Share2 className="h-6 w-6 animate-pulse delay-200" />
                    <Loader2 className="h-6 w-6 animate-spin" />
                  </div>
                  <div className="w-full space-y-2">
                    <div className="h-1 w-full bg-white/10 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500/40 animate-progress-indeterminate" />
                    </div>
                    <p className="text-[8px] font-mono text-slate-200 text-center uppercase tracking-widest">Compiling stream segments</p>
                  </div>
               </div>
             ) : progress >= 100 ? (
               <>
                 <div className="h-4 w-3/4 bg-white/10 rounded animate-pulse delay-75" />
                 <div className="space-y-2">
                    <div className="h-2 w-full bg-white/5 rounded animate-pulse delay-100" />
                    <div className="h-2 w-full bg-white/5 rounded animate-pulse delay-150" />
                    <div className="h-2 w-5/6 bg-white/5 rounded animate-pulse delay-200" />
                 </div>
                 <div className="h-20 w-full bg-white/5 rounded mt-4 animate-pulse delay-300 border border-white/5" />
               </>
             ) : (
               <div className="absolute inset-0 flex flex-col items-center justify-center p-6">
                 <p className="text-[10px] font-mono text-slate-600 text-center uppercase tracking-widest">Waiting for analysis</p>
               </div>
             )}
             
             {isAnalyzing && progress < 100 && (
               <div className="absolute inset-0 bg-gradient-to-b from-transparent via-blue-500/5 to-transparent h-[20%] animate-scanline pointer-events-none" />
             )}
          </div>
          
          <div className="flex items-center gap-2 text-[10px] text-slate-200 justify-center font-mono">
            {isAnalyzing && progress < 100 ? (
              <>
                <Loader2 className="h-3 w-3 animate-spin" />
                <span>INDEXING_EVIDENCE...</span>
              </>
            ) : progress >= 100 ? (
              <span className="text-emerald-400 tracking-widest">ARTIFACT_SEALED</span>
            ) : (
              <span className="text-slate-300">READY</span>
            )}
          </div>
          
          {progress >= 100 && finalResponse && (
            <Button
              onClick={handleDownloadPDF}
              disabled={isGeneratingPDF}
              className="w-full mt-4 bg-blue-600 hover:bg-blue-700 text-white font-mono text-xs py-2 h-auto"
            >
              {isGeneratingPDF ? (
                <>
                  <Loader2 className="h-3 w-3 mr-2 animate-spin" />
                  GENERATING...
                </>
              ) : (
                <>
                  <Download className="h-3 w-3 mr-2" />
                  DOWNLOAD PDF
                </>
              )}
            </Button>
          )}
        </div>

        {/* Artifact List */}
        <div className="space-y-4">
          <h3 className="text-xs font-bold text-slate-200 uppercase tracking-widest">Captured Artifacts</h3>
          
          <div className="space-y-2">
            {[
              { icon: Database, label: "DB_DUMP_PARTIAL.sql", size: "2.4 MB" },
              { icon: Server, label: "AWS_CLOUDWATCH.json", size: "1.1 MB" },
              { icon: FileText, label: "AUTH_CONTROLLER.py", size: "14 KB" },
            ].map((item, i) => (
              <div key={i} className="group flex items-center gap-3 p-3 rounded-md border border-white/15 bg-white/10 hover:bg-white/20 hover:border-white/30 transition-all cursor-pointer">
                <div className="p-2 rounded bg-slate-900 text-slate-200 group-hover:text-blue-400 transition-colors">
                  <item.icon className="h-4 w-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-mono text-slate-100 truncate group-hover:text-white">{item.label}</div>
                  <div className="text-[10px] text-slate-300">{item.size}</div>
                </div>
                <Download className="h-3 w-3 text-slate-400 group-hover:text-blue-400 opacity-0 group-hover:opacity-100 transition-all" />
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="p-4 border-t border-white/20 bg-slate-950/90">
        <div className="flex items-center gap-3 text-xs text-slate-200">
           <Clock className="h-3 w-3" />
           <span className="font-mono">SESSION: {sessionTime}</span>
        </div>
      </div>
    </div>
  );
}
