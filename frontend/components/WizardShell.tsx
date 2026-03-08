"use client";

import { useCallback, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import StepIndicator from "@/components/StepIndicator";
import { useReturn } from "@/context/ReturnContext";

interface Props {
  step: number;
  title: string;
  subtitle?: string;
  children: ReactNode;
  /** If provided, override default Next navigation */
  onNext?: () => void;
  /** Set to false to hide Next button (e.g., for last wizard step that auto-submits) */
  showNext?: boolean;
  nextLabel?: string;
  nextDisabled?: boolean;
  loading?: boolean;
}

const TOTAL_STEPS = 6;

export default function WizardShell({
  step,
  title,
  subtitle,
  children,
  onNext,
  showNext = true,
  nextLabel = "Continue →",
  nextDisabled = false,
  loading = false,
}: Props) {
  const router = useRouter();
  const { dispatch } = useReturn();

  const handleNext = useCallback(() => {
    // Always save step data first (if caller provides a saver)
    if (onNext) onNext();
    // Always navigate to the next step (or to results if final step)
    if (step < TOTAL_STEPS) {
      dispatch({ type: "SET_STEP", step: step + 1 });
      router.push(`/return/${step + 1}`);
    } else {
      router.push("/results");
    }
  }, [onNext, step, dispatch, router]);

  const handleBack = useCallback(() => {
    if (step > 1) {
      dispatch({ type: "SET_STEP", step: step - 1 });
      router.push(`/return/${step - 1}`);
    } else {
      router.push("/");
    }
  }, [step, dispatch, router]);

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "var(--bg-primary)" }}>
      {/* Top bar */}
      <header className="border-b no-print" style={{ borderColor: "var(--border)" }}>
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center gap-4">
          <button
            type="button"
            onClick={() => router.push("/")}
            className="text-sm font-bold tracking-tight text-slate-300 hover:text-white transition-colors flex items-center gap-1"
          >
            📊 TaxApp
          </button>
          <div className="flex-1 flex justify-center">
            <StepIndicator currentStep={step} />
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="flex-1 flex items-start justify-center px-4 py-10">
        <div className="w-full max-w-2xl space-y-6">
          <div>
            <h1 className="text-2xl font-bold mb-1">{title}</h1>
            {subtitle && <p className="text-sm text-slate-400">{subtitle}</p>}
          </div>
          {children}
        </div>
      </main>

      {/* Navigation */}
      <nav
        className="sticky bottom-0 border-t no-print"
        style={{ background: "var(--bg-secondary)", borderColor: "var(--border)" }}
      >
        <div className="max-w-2xl mx-auto px-4 py-3 flex justify-between items-center gap-4">
          <button type="button" onClick={handleBack} className="btn-ghost">
            ← {step === 1 ? "Home" : "Back"}
          </button>
          <span className="text-xs text-slate-500">
            Step {step} of {TOTAL_STEPS}
          </span>
          {showNext && (
            <button
              id={`wizard-next-step-${step}`}
              type="button"
              onClick={handleNext}
              disabled={nextDisabled || loading}
              className="btn-primary"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.4 0 0 5.4 0 12h4z" />
                  </svg>
                  Calculating...
                </span>
              ) : nextLabel}
            </button>
          )}
        </div>
      </nav>
    </div>
  );
}
