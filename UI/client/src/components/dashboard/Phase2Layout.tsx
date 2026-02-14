import { motion } from "framer-motion";
import { AlertTriangle, X, Minimize2, Maximize2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import ReactMarkdown from "react-markdown";

interface SmokingGunPanelProps {
  onClose: () => void;
  onMinimize?: () => void;
  onRestore?: () => void;
  isMinimized?: boolean;
  finalResponse?: string;
}

export function SmokingGunPanel({ 
  onClose, 
  onMinimize, 
  onRestore, 
  isMinimized = false,
  finalResponse = ""
}: SmokingGunPanelProps) {
  // Minimized indicator at bottom-right
  if (isMinimized) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.8, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.8, y: 20 }}
        className="fixed bottom-6 right-6 z-50"
      >
        <Button
          onClick={onRestore}
          className="h-14 px-6 bg-gradient-to-r from-red-600/90 to-orange-600/90 hover:from-red-500 hover:to-orange-500 text-white font-bold border border-red-500/30 shadow-[0_0_30px_rgba(220,38,38,0.4)] backdrop-blur-sm transition-all hover:scale-105"
        >
          <AlertTriangle className="h-5 w-5 mr-2 animate-pulse" />
          <span className="font-display text-sm tracking-wider">ANALYSIS COMPLETE</span>
          <Maximize2 className="h-4 w-4 ml-2" />
        </Button>
      </motion.div>
    );
  }

  // Full panel view
  return (
    <motion.div 
        initial={{ opacity: 0, y: 100 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, type: "spring", bounce: 0.3 }}
        className="flex-1 relative rounded-t-2xl border-t border-blue-500/40 bg-gradient-to-b from-blue-950/60 to-slate-950/90 backdrop-blur-2xl overflow-hidden flex flex-col"
    >
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-blue-500 to-transparent opacity-50" />
      
      {/* Header with Minimize and Close buttons */}
      <div className="absolute top-4 right-4 z-20 flex gap-2">
        <Button 
          variant="ghost" 
          size="icon" 
          className="text-slate-200 hover:text-white hover:bg-white/15 rounded-full"
          onClick={onMinimize}
        >
          <Minimize2 className="h-5 w-5" />
        </Button>
        <Button 
          variant="ghost" 
          size="icon" 
          className="text-slate-200 hover:text-white hover:bg-white/15 rounded-full"
          onClick={onClose}
        >
          <X className="h-5 w-5" />
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-8 max-w-6xl mx-auto space-y-6">
          {/* Header Badge */}
          <div className="text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-bold tracking-widest uppercase animate-pulse">
              <AlertTriangle className="h-3 w-3" />
              Analysis Complete
            </div>
          </div>
          
          {/* Investigation Results */}
          <div className="p-6 rounded-xl bg-white/10 border border-white/20 text-left shadow-2xl">
            {finalResponse ? (
              <div className="prose prose-invert prose-slate max-w-none">
                <ReactMarkdown
                  className="markdown-content"
                  components={{
                    h1: ({ children }) => (
                      <h1 className="text-2xl font-bold text-blue-400 mb-4 mt-6 first:mt-0 border-b border-blue-500/20 pb-2">
                        {children}
                      </h1>
                    ),
                    h2: ({ children }) => (
                      <h2 className="text-xl font-semibold text-blue-300 mb-3 mt-5 first:mt-0">
                        {children}
                      </h2>
                    ),
                    h3: ({ children }) => (
                      <h3 className="text-lg font-semibold text-slate-100 mb-2 mt-4 first:mt-0">
                        {children}
                      </h3>
                    ),
                    p: ({ children }) => (
                      <p className="text-slate-100 text-sm leading-relaxed mb-4">
                        {children}
                      </p>
                    ),
                    ul: ({ children }) => (
                      <ul className="list-disc list-inside text-slate-100 text-sm mb-4 space-y-2 ml-4">
                        {children}
                      </ul>
                    ),
                    ol: ({ children }) => (
                      <ol className="list-decimal list-inside text-slate-100 text-sm mb-4 space-y-2 ml-4">
                        {children}
                      </ol>
                    ),
                    li: ({ children }) => (
                      <li className="text-slate-100 text-sm leading-relaxed">
                        {children}
                      </li>
                    ),
                    code: ({ children, className }) => {
                      const isInline = !className;
                      return isInline ? (
                        <code className="bg-slate-800/50 text-blue-300 px-1.5 py-0.5 rounded text-xs font-mono border border-slate-700/50">
                          {children}
                        </code>
                      ) : (
                        <code className="block bg-slate-900/50 text-slate-200 p-4 rounded-lg text-xs font-mono border border-slate-700/50 overflow-x-auto mb-4">
                          {children}
                        </code>
                      );
                    },
                    pre: ({ children }) => (
                      <pre className="bg-slate-900/50 p-4 rounded-lg border border-slate-700/50 overflow-x-auto mb-4">
                        {children}
                      </pre>
                    ),
                    blockquote: ({ children }) => (
                      <blockquote className="border-l-4 border-blue-500/60 pl-4 italic text-slate-200 my-4 bg-slate-900/50 py-2 rounded-r">
                        {children}
                      </blockquote>
                    ),
                    strong: ({ children }) => (
                      <strong className="font-bold text-slate-200">
                        {children}
                      </strong>
                    ),
                    em: ({ children }) => (
                      <em className="italic text-slate-100">
                        {children}
                      </em>
                    ),
                    a: ({ children, href }) => (
                      <a 
                        href={href} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 underline underline-offset-2 transition-colors"
                      >
                        {children}
                      </a>
                    ),
                    hr: () => (
                      <hr className="border-slate-700/50 my-6" />
                    ),
                    table: ({ children }) => (
                      <div className="overflow-x-auto mb-4">
                        <table className="min-w-full border-collapse border border-slate-700/50">
                          {children}
                        </table>
                      </div>
                    ),
                    thead: ({ children }) => (
                      <thead className="bg-slate-800/50">
                        {children}
                      </thead>
                    ),
                    tbody: ({ children }) => (
                      <tbody>
                        {children}
                      </tbody>
                    ),
                    tr: ({ children }) => (
                      <tr className="border-b border-slate-700/50">
                        {children}
                      </tr>
                    ),
                    th: ({ children }) => (
                      <th className="px-4 py-2 text-left text-slate-100 font-semibold text-sm border border-slate-700/60">
                        {children}
                      </th>
                    ),
                    td: ({ children }) => (
                      <td className="px-4 py-2 text-slate-100 text-sm border border-slate-700/60">
                        {children}
                      </td>
                    ),
                  }}
                >
                  {finalResponse}
                </ReactMarkdown>
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-slate-200 text-lg">Analysis completed. No detailed findings available.</p>
              </div>
            )}
          </div>
        </div>
      </ScrollArea>
    </motion.div>
  );
}
