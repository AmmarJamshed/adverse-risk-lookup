import { create } from "zustand";
import { persist } from "zustand/middleware";

type ThemeState = {
  theme: "dark" | "light";
  toggle: () => void;
};

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: "light",
      toggle: () => set({ theme: get().theme === "dark" ? "light" : "dark" }),
    }),
    { name: "arl-theme-v2" }
  )
);
