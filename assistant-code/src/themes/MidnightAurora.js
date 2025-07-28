// src/theme/MidnightAurora.js
import { createTheme } from '@fluentui/react';

export const MidnightAurora = createTheme({
  palette: {
    themePrimary: '#a78bfa',   // Soft purple-blue accent
    themeLighterAlt: '#070708',
    themeLighter: '#1e1b2f',
    themeLight: '#302d4a',
    themeTertiary: '#5a51a0',
    themeSecondary: '#8b81d1',
    themeDarkAlt: '#b39afc',
    themeDark: '#c2adff',
    themeDarker: '#d9cfff',
    neutralLighterAlt: '#1d1d27',
    neutralLighter: '#21212d',
    neutralLight: '#262635',
    neutralQuaternaryAlt: '#2c2c3e',
    neutralQuaternary: '#313144',
    neutralTertiaryAlt: '#3f3f55',
    neutralTertiary: '#cccccc',
    neutralSecondary: '#e0e0e0',
    neutralPrimaryAlt: '#eaeaea',
    neutralPrimary: '#ffffff',
    neutralDark: '#f4f4f4',
    black: '#fafafa',
    white: '#14141c'
  },
  fonts: {
    medium: {
      fontSize: '14px',
      fontWeight: 'normal',
    }
  }
});
