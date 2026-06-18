// Metro config con soporte NativeWind 4 (Tailwind para React Native).
const { getDefaultConfig } = require("expo/metro-config");
const { withNativeWind } = require("nativewind/metro");

const config = getDefaultConfig(__dirname);

// CU-35: permitir bundlear el modelo .tflite como asset (react-native-fast-tflite).
config.resolver.assetExts.push("tflite");

module.exports = withNativeWind(config, { input: "./global.css" });
