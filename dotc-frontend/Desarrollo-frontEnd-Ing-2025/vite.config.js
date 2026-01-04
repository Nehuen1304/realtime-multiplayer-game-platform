import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react'; // Asegúrate de que esta línea esté bien

export default defineConfig({

  plugins: [react()],
  server: {
    allowedHosts: ['.trycloudflare.com'], 
    host: true, // <--- Para permitir acceso externo también
  },
  test: {
    environment: 'jsdom',
    globals: true, // Optional, but recommended for simplicity
    setupFiles: './src/setupTests.js', // Tells Vitest to run this file before tests
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'clover'],
      reportsDirectory: 'coverage',
      // Focus coverage on source files and skip entry points and indexes that don't carry logic
      include: ['src/**/*.{js,jsx}'],
      exclude: [
        'src/main.jsx',
        'src/App.jsx',
        '**/index.jsx', // barrel/aggregator files
        '**/*.css',
        '**/setupTests.js',
      ],
    },
  },
})

