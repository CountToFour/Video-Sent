import { createContext, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { createTheme, ThemeProvider } from "@mui/material/styles";

type ColorModeContextType = {
    toggleColorMode: () => void;
};

export const ColorModeContext = createContext<ColorModeContextType>({
    toggleColorMode: () => {}
});

export default function CustomThemeProvider({ children }: { children: ReactNode }) {
    const [mode, setMode] = useState<"light" | "dark">(
        (localStorage.getItem("theme") as "light" | "dark") || "light"
    );

    const colorMode = useMemo(
        () => ({
            toggleColorMode: () => {
                const newMode = mode === "light" ? "dark" : "light";
                setMode(newMode);
                localStorage.setItem("theme", newMode);
            }
        }),
        [mode]
    );

    const theme = useMemo(
        () =>
            createTheme({
                palette: {
                    mode,
                },
            }),
        [mode]
    );

    return (
        <ColorModeContext.Provider value={colorMode}>
            <ThemeProvider theme={theme}>{children}</ThemeProvider>
        </ColorModeContext.Provider>
    );
}
