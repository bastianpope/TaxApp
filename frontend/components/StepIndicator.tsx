"use client";

interface Step {
  id: number;
  label: string;
}

const STEPS: Step[] = [
  { id: 1, label: "Personal" },
  { id: 2, label: "Income" },
  { id: 3, label: "Business" },
  { id: 4, label: "Deductions" },
  { id: 5, label: "State" },
  { id: 6, label: "Strategy" },
];

interface Props {
  currentStep: number;
}

export default function StepIndicator({ currentStep }: Props) {
  return (
    <nav aria-label="Progress" className="no-print">
      <ol className="flex items-center gap-0 w-full">
        {STEPS.map((step, idx) => {
          const isCompleted = step.id < currentStep;
          const isCurrent = step.id === currentStep;

          return (
            <li key={step.id} className="flex items-center">
              <div className="flex flex-col items-center">
                <div
                  className={[
                    "w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all",
                    isCompleted
                      ? "bg-brand-500 text-white"
                      : isCurrent
                        ? "bg-brand-500 text-white ring-4 ring-brand-500/20"
                        : "bg-surface-700 text-slate-400",
                  ].join(" ")}
                  aria-current={isCurrent ? "step" : undefined}
                >
                  {isCompleted ? (
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    step.id
                  )}
                </div>
                <span
                  className={[
                    "mt-1.5 text-[10px] font-medium whitespace-nowrap hidden sm:block",
                    isCurrent ? "text-brand-400" : "text-slate-500",
                  ].join(" ")}
                >
                  {step.label}
                </span>
              </div>
              {idx < STEPS.length - 1 && (
                <div
                  className={[
                    "h-px w-2 sm:w-10 md:w-16 mb-5 transition-colors flex-shrink-0",
                    isCompleted ? "bg-brand-500" : "bg-surface-700",
                  ].join(" ")}
                />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
