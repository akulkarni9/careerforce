import { createContext, useCallback, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";

/**
 * Field names that are shared across tools. When one tool fills any of these,
 * the value is remembered and pre-fills the matching field in every other tool
 * (e.g. paste a JD once, reuse it in Cover Letter, Research, and Skill Gap).
 */
export const SHARED_KEYS = new Set(["jd_text", "company", "role"]);

type SharedState = Record<string, string>;

interface SharedContextValue {
  readonly shared: SharedState;
  readonly mergeShared: (partial: SharedState) => void;
  readonly clearShared: () => void;
}

const STORAGE_KEY = "ja:shared-context";

function loadInitial(): SharedState {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as SharedState) : {};
  } catch {
    return {};
  }
}

const SharedContext = createContext<SharedContextValue | null>(null);

export function SharedProvider({ children }: { readonly children: ReactNode }) {
  const [shared, setShared] = useState<SharedState>(loadInitial);

  const persist = useCallback((next: SharedState) => {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    } catch {
      /* storage full or unavailable — ignore */
    }
  }, []);

  const mergeShared = useCallback(
    (partial: SharedState) => {
      setShared((prev) => {
        // Only keep non-empty values; skip no-op updates to avoid churn.
        const next = { ...prev };
        let changed = false;
        for (const [k, v] of Object.entries(partial)) {
          const val = v?.trim() ?? "";
          if (val && next[k] !== val) {
            next[k] = val;
            changed = true;
          }
        }
        if (!changed) return prev;
        persist(next);
        return next;
      });
    },
    [persist],
  );

  const clearShared = useCallback(() => {
    setShared({});
    try {
      window.localStorage.removeItem(STORAGE_KEY);
    } catch {
      /* ignore */
    }
  }, []);

  const value = useMemo(
    () => ({ shared, mergeShared, clearShared }),
    [shared, mergeShared, clearShared],
  );

  return <SharedContext.Provider value={value}>{children}</SharedContext.Provider>;
}

export function useSharedContext(): SharedContextValue {
  const ctx = useContext(SharedContext);
  if (!ctx) throw new Error("useSharedContext must be used within a SharedProvider");
  return ctx;
}
