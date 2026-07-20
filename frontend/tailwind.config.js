export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#171717",
        body: "#4d4d4d",
        mute: "#888888",
        hairline: "#ebebeb",
        "hairline-strong": "#a1a1a1",
        canvas: "#ffffff",
        "canvas-soft": "#fafafa",
        "canvas-soft-2": "#f5f5f5",
        link: "#0070f3",
        "link-deep": "#0761d1",
        success: "#0070f3",
        error: "#ee0000",
        "error-soft": "#f7d4d6",
        warning: "#f5a623",
        "warning-soft": "#ffefcf",
        violet: "#7928ca",
        cyan: "#50e3c2",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "monospace"],
      },
      borderRadius: {
        xs: "4px",
        sm: "6px",
        md: "8px",
        lg: "12px",
        xl: "16px",
        pill: "100px",
      },
    },
  },
  plugins: [],
};
