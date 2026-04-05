import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#f4efe4",
        ink: "#172126",
        sand: "#d8c6a5",
        ember: "#bb5a3c",
        sage: "#8ca17f",
        mist: "#dfe6de"
      }
    }
  },
  plugins: []
};

export default config;

