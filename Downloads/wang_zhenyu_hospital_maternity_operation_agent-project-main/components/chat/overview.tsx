import { motion } from "framer-motion";
import { Bed, Baby, AlertTriangle, ClipboardList, Stethoscope, HeartPulse } from "lucide-react";

export const Overview = () => {
  const quickInsights = [
    {
      icon: Bed,
      title: "Ward Status",
      description: "Real-time bed & room availability",
      color: "#2A9D8F",
    },
    {
      icon: Baby,
      title: "Patient Tracking",
      description: "Labor, postpartum & discharge status",
      color: "#F4A261",
    },
    {
      icon: AlertTriangle,
      title: "Risk Alerts",
      description: "High-risk patient flags & warnings",
      color: "#E63946",
    },
    {
      icon: ClipboardList,
      title: "Orders",
      description: "Schedule surgeries & manage orders",
      color: "#2A9D8F",
    },
    {
      icon: Stethoscope,
      title: "Discharge",
      description: "Predict & update discharge times",
      color: "#1D3557",
    },
  ];

  return (
    <motion.div
      key="overview"
      className="max-w-3xl mx-auto md:mt-8"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      transition={{ delay: 0.3 }}
    >
      <div className="bg-white/90 dark:bg-[#1A3A3A]/70 border-3 border-[#2A9D8F] rounded-2xl shadow-[4px_4px_0_rgba(30,122,110,0.3)]" style={{ borderWidth: '3px' }}>
        <div className="py-10 px-8">
          {/* Header */}
          <div className="flex flex-col items-center text-center mb-8">
            <div className="w-14 h-14 bg-[#E63946] rounded-xl flex items-center justify-center border-2 border-[#C62B38] shadow-[3px_3px_0_rgba(198,43,56,0.4)] mb-4">
              <HeartPulse className="w-8 h-8 text-white" strokeWidth={2.5} />
            </div>

            <h2 className="font-display text-3xl sm:text-4xl tracking-tight mb-1 text-[#1D3557] dark:text-white">
              Materni<span className="text-[#2A9D8F]">Flow</span>
            </h2>

            <p className="font-pixel text-lg text-[#2A9D8F] mb-4">
              Your OB/GYN Scheduling Assistant
            </p>

            <div className="flex gap-1.5 mb-4">
              <div className="w-8 h-1.5 bg-[#2A9D8F] rounded-full" />
              <div className="w-4 h-1.5 bg-[#F4A261] rounded-full" />
              <div className="w-2 h-1.5 bg-[#E63946] rounded-full" />
            </div>

            <p className="text-[#1D3557]/60 dark:text-white/60 max-w-md font-body">
              I can help you check ward status, predict patient discharge times, coordinate room assignments, flag high-risk cases, and assist with placing orders. Just ask!
            </p>
          </div>

          {/* Quick Insight Cards */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {quickInsights.map((insight, index) => (
              <motion.div
                key={insight.title}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 + index * 0.1 }}
                className="p-4 rounded-xl bg-[#E8F5F0]/50 dark:bg-[#0F2027]/60 border-2 border-[#2A9D8F]/20 dark:border-[#2A9D8F]/25 shadow-[2px_2px_0_rgba(42,157,143,0.1)] hover:shadow-[3px_3px_0_rgba(42,157,143,0.15)] hover:translate-x-[-1px] hover:translate-y-[-1px] transition-all"
              >
                <insight.icon
                  className="w-6 h-6 mb-2"
                  strokeWidth={2}
                  style={{ color: insight.color }}
                />
                <h3 className="font-display font-medium text-sm text-[#1D3557] dark:text-white">{insight.title}</h3>
                <p className="text-xs text-[#1D3557]/50 dark:text-white/50 mt-0.5 font-body">{insight.description}</p>
              </motion.div>
            ))}
          </div>

          {/* Example prompts */}
          <div className="mt-6 pt-6 border-t-2 border-[#2A9D8F]/15 dark:border-[#2A9D8F]/20">
            <p className="font-pixel text-base text-[#2A9D8F]/70 dark:text-[#5CC0B5]/70 text-center">
              Try: &ldquo;What&apos;s the current ward status?&rdquo; or &ldquo;Which patients are high-risk?&rdquo;
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
