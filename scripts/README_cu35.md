# CU-35 — Clasificador de severidad de daño (on-device)

Modelo MobileNetV2 (transfer learning) que clasifica la foto del daño en
**4 clases**: `sin_dano / leve / moderado / severo`. Corre offline en la app
móvil vía `react-native-fast-tflite`. Ver diseño en `Context.md` (ADR-012).

> `tipo` en `metadata.damage_classification` queda genérico (`"daño_carroceria"`)
> por ahora — el modelo entrenado predice **severidad**, que es lo defendible y
> alcanzable. Un segundo modelo de ubicación (frontal/lateral/trasero) queda
> como mejora opcional fuera del camino crítico.

## 1. Requisitos (ya instalados en esta PC)

```
python -m pip install -r scripts/requirements-train.txt
```
(TensorFlow, Kaggle CLI, Pillow, numpy.)

## 2. Credenciales de Kaggle (único paso manual tuyo)

1. Kaggle → tu perfil → **Settings** → **API** → *Create New Token*.
2. Se baja `kaggle.json`. Movelo a: `C:\Users\hp\.kaggle\kaggle.json`.

## 3. Bajar los datasets

```
kaggle datasets download -d prajwalbhamere/car-damage-severity-dataset -p scripts/data/raw --unzip
kaggle datasets download -d anujms/car-damage-detection           -p scripts/data/raw --unzip
```

## 4. Armar las carpetas por clase

El script entrena leyendo `scripts/data/dataset/<clase>/*.jpg`. Hay que mapear:

| Carpeta destino | De dónde sale |
|---|---|
| `scripts/data/dataset/leve/`     | clase **minor** del severity dataset |
| `scripts/data/dataset/moderado/` | clase **moderate** |
| `scripts/data/dataset/severo/`   | clase **severe** |
| `scripts/data/dataset/sin_dano/` | imágenes **whole / 00-no-damage** de anujms |

(Los nombres exactos de las subcarpetas varían según el dataset; copiá/renombrá
las imágenes a las 4 carpetas destino. Con tener algunos cientos por clase
alcanza para un baseline.)

## 5. Entrenar y exportar

```
python scripts/train_damage_model.py --data-dir scripts/data/dataset
```

Genera:
- `mobile/assets/models/damage_mobilenet.tflite` (float16, ~3–9 MB)
- `mobile/assets/models/damage_labels.json`

## 6. Después (lo hago yo)

- Integrar `react-native-fast-tflite` + helper de inferencia en `mobile/lib/ml/`.
- Cablear en `evidencias.tsx` → `metadata.damage_classification`.
- Rebuild del APK (build local ya disponible).

> Nota: el entrenamiento en CPU funciona (transfer learning sobre dataset chico),
> solo es más lento. No necesitás GPU para el baseline.
