/** @type {import('next').NextConfig} */
const nextConfig = {
  // Habilita el output standalone para el Dockerfile multi-stage.
  // Genera .next/standalone con server.js y todas las dependencias minimas.
  // Solo se activa en producción; en desarrollo interfiere con el dev server.
  ...(process.env.NODE_ENV === "production" && { output: "standalone" }),
};

export default nextConfig;
