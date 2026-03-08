"use client";

import {
  createContext,
  useContext,
  useReducer,
  useState,
  useEffect,
  useRef,
  useCallback,
  type ReactNode,
} from "react";
import type { TaxReturn, AggressivenessLevel, FilingStatus } from "@/lib/types";
import { saveReturn, loadReturn, saveStep, loadStep } from "@/lib/utils";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

// ── State ─────────────────────────────────────────────────────

export interface ReturnState {
  currentStep: number;
  data: Partial<TaxReturn>;
  /** ID of the backend-saved return, if it has been persisted at least once */
  savedReturnId?: string | null;
}

const initialState: ReturnState = {
  currentStep: 1,
  savedReturnId: null,
  data: {
    tax_year: 2025,
    filing_status: "single",
    aggressiveness: "LOW",
    w2s: [],
    nec_1099s: [],
    int_1099s: [],
    div_1099s: [],
    capital_gains_1099b: [],
    schedule_c_businesses: [],
    state_residencies: [],
    dependents: [],
  },
};

// ── Actions ───────────────────────────────────────────────────

type Action =
  | { type: "SET_STEP"; step: number }
  | { type: "PATCH"; patch: Partial<TaxReturn> }
  | { type: "SET_FILING_STATUS"; status: FilingStatus }
  | { type: "SET_AGGRESSIVENESS"; level: AggressivenessLevel }
  | { type: "RESET" }
  | { type: "LOAD"; state: ReturnState }
  | { type: "SET_SAVED_ID"; id: string | null };

function reducer(state: ReturnState, action: Action): ReturnState {
  switch (action.type) {
    case "SET_STEP":
      return { ...state, currentStep: action.step };
    case "PATCH":
      return { ...state, data: { ...state.data, ...action.patch } };
    case "SET_FILING_STATUS":
      return { ...state, data: { ...state.data, filing_status: action.status } };
    case "SET_AGGRESSIVENESS":
      return { ...state, data: { ...state.data, aggressiveness: action.level } };
    case "RESET":
      return initialState;
    case "LOAD":
      return action.state;
    case "SET_SAVED_ID":
      return { ...state, savedReturnId: action.id };
    default:
      return state;
  }
}

// ── Context ───────────────────────────────────────────────────

interface ReturnContextValue {
  state: ReturnState;
  dispatch: React.Dispatch<Action>;
}

const ReturnContext = createContext<ReturnContextValue | null>(null);

export function ReturnProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState);

  // Restore from session storage on mount
  useEffect(() => {
    const savedData = loadReturn();
    const savedStep = loadStep();
    if (savedData && Object.keys(savedData).length > 0) {
      dispatch({
        type: "LOAD",
        state: {
          currentStep: savedStep,
          savedReturnId: null,
          data: { ...initialState.data, ...savedData },
        },
      });
    }
  }, []);

  // Persist to session storage on change
  useEffect(() => {
    saveReturn(state.data);
    saveStep(state.currentStep);
  }, [state]);

  return (
    <ReturnContext.Provider value={{ state, dispatch }}>
      {children}
    </ReturnContext.Provider>
  );
}

export function useReturn() {
  const ctx = useContext(ReturnContext);
  if (!ctx) throw new Error("useReturn must be used inside <ReturnProvider>");
  return ctx;
}

// ── Auto-save hook ────────────────────────────────────────────
//
// Drop this hook into any page inside the wizard to start auto-saving to the
// backend.  It debounces by 1.5 s and only runs when a user is logged in.
//
// Usage:
//   const { saving, lastSaved, error } = useReturnAutoSave();

export interface AutoSaveStatus {
  saving: boolean;
  lastSaved: Date | null;
  error: string | null;
}

export function useReturnAutoSave(): AutoSaveStatus {
  const { state, dispatch } = useReturn();
  const { user } = useAuth();

  // useState drives re-renders for consumers
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Refs for the async callback to read latest values without stale closures
  const savedReturnIdRef = useRef<string | null | undefined>(state.savedReturnId);
  const dataRef = useRef(state.data);

  useEffect(() => { savedReturnIdRef.current = state.savedReturnId; }, [state.savedReturnId]);
  useEffect(() => { dataRef.current = state.data; }, [state.data]);

  const doSave = useCallback(async () => {
    if (!user) return;
    setSaving(true);
    setError(null);
    try {
      const returnData = dataRef.current as Record<string, unknown>;
      const year = (returnData.tax_year as number | undefined) ?? 2025;
      const label = `TY ${year} Return`;

      if (savedReturnIdRef.current) {
        await api.returns.update(savedReturnIdRef.current, { return_data: returnData, label });
      } else {
        const created = await api.returns.create({ label, tax_year: year, return_data: returnData });
        savedReturnIdRef.current = created.id;
        dispatch({ type: "SET_SAVED_ID", id: created.id });
      }
      setLastSaved(new Date());
    } catch {
      setError("Auto-save failed. Your progress is saved locally.");
    } finally {
      setSaving(false);
    }
  }, [user, dispatch]);

  // Debounced auto-save on data changes
  useEffect(() => {
    if (!user) return;
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(doSave, 1500);
    return () => { if (debounceTimer.current) clearTimeout(debounceTimer.current); };
  }, [state.data, user, doSave]);

  // Best-effort flush on page close
  useEffect(() => {
    const handler = () => {
      if (debounceTimer.current) { clearTimeout(debounceTimer.current); void doSave(); }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [doSave]);

  return { saving, lastSaved, error };
}

