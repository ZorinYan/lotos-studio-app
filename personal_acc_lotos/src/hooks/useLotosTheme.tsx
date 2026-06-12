import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

export type ColorScheme = 'light' | 'dark'

const STORAGE_KEY = 'lotos_color_scheme'

type LotosThemeContextValue = {
  colorScheme: ColorScheme
  setColorScheme: (scheme: ColorScheme) => void
  toggleColorScheme: () => void
  isDark: boolean
}

const LotosThemeContext = createContext<LotosThemeContextValue | null>(null)

function readStoredScheme(): ColorScheme {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'dark' || stored === 'light') {
      return stored
    }
  } catch {
    // ignore
  }
  return 'light'
}

export function LotosThemeProvider({ children }: { children: ReactNode }) {
  const [colorScheme, setColorSchemeState] = useState<ColorScheme>(readStoredScheme)

  useEffect(() => {
    document.documentElement.setAttribute('data-lotos-theme', colorScheme)
    document.documentElement.style.colorScheme = colorScheme
    try {
      localStorage.setItem(STORAGE_KEY, colorScheme)
    } catch {
      // ignore
    }
  }, [colorScheme])

  const setColorScheme = useCallback((scheme: ColorScheme) => {
    setColorSchemeState(scheme)
  }, [])

  const toggleColorScheme = useCallback(() => {
    setColorSchemeState((current) => (current === 'dark' ? 'light' : 'dark'))
  }, [])

  const value = useMemo(
    () => ({
      colorScheme,
      setColorScheme,
      toggleColorScheme,
      isDark: colorScheme === 'dark',
    }),
    [colorScheme, setColorScheme, toggleColorScheme],
  )

  return <LotosThemeContext.Provider value={value}>{children}</LotosThemeContext.Provider>
}

export function useLotosTheme(): LotosThemeContextValue {
  const context = useContext(LotosThemeContext)
  if (!context) {
    throw new Error('useLotosTheme must be used within LotosThemeProvider')
  }
  return context
}
