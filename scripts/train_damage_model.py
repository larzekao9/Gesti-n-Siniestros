"""CU-35 — Entrenamiento del clasificador de severidad de daño (on-device).

Transfer learning sobre **MobileNetV2** (ImageNet) para clasificar la foto del
daño en 4 clases: ``sin_dano / leve / moderado / severo``. Exporta a **TFLite
float16** para correr offline en la app móvil (``react-native-fast-tflite``).

Diseño (ver Context.md ADR-012 y §Ciclo 8):
  - Input 224x224x3, preprocess MobileNetV2 a [-1, 1].
  - Fase 1: backbone congelado, se entrena solo la cabeza densa.
  - Fase 2: fine-tune de las capas superiores con LR bajo.
  - Salida: softmax(4). En inferencia, si max_prob < umbral -> no se setea
    clasificacion (F-A1, "no inventar"). El umbral vive en la app, no acá.
  - CU-36 ("¿hay vehiculo?") reutiliza este MobileNet/ImageNet, no entrena extra.

Layout de datos esperado (carpetas ASCII, una por clase)::

    <data-dir>/
        sin_dano/   *.jpg   (autos sin danio -> imagenes "whole" de anujms)
        leve/       *.jpg   (minor)
        moderado/   *.jpg   (moderate)
        severo/     *.jpg   (severe)

Ver scripts/README_cu35.md para como armar estas carpetas desde los datasets
de Kaggle.

Uso::

    python scripts/train_damage_model.py --data-dir scripts/data/dataset
    # opcional: --epochs-head 12 --epochs-finetune 8 --batch 32

Genera (por defecto, dentro del proyecto movil)::

    mobile/assets/models/damage_mobilenet.tflite
    mobile/assets/models/damage_labels.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import tensorflow as tf

IMG_SIZE = 224
# Orden canonico de clases (se persiste en damage_labels.json; el indice del
# softmax mapea a esta lista). De menor a mayor severidad.
CLASS_ORDER = ["sin_dano", "leve", "moderado", "severo"]
# Etiquetas "bonitas" para la UI movil (mismo orden que CLASS_ORDER).
PRETTY_LABELS = {
    "sin_dano": "Sin daño",
    "leve": "Leve",
    "moderado": "Moderado",
    "severo": "Severo",
}


def build_datasets(data_dir: Path, batch: int, val_split: float):
    """Carga train/val desde carpetas-por-clase y fija el orden de clases."""
    common = dict(
        directory=str(data_dir),
        labels="inferred",
        label_mode="categorical",
        class_names=CLASS_ORDER,  # fuerza el orden canonico
        image_size=(IMG_SIZE, IMG_SIZE),
        batch_size=batch,
        seed=1337,
    )
    train_ds = tf.keras.utils.image_dataset_from_directory(
        validation_split=val_split, subset="training", **common
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        validation_split=val_split, subset="validation", **common
    )
    autotune = tf.data.AUTOTUNE
    train_ds = train_ds.cache().shuffle(1000).prefetch(autotune)
    val_ds = val_ds.cache().prefetch(autotune)
    return train_ds, val_ds


def build_model(num_classes: int) -> tf.keras.Model:
    """MobileNetV2 (ImageNet) + augmentacion + cabeza densa."""
    augment = tf.keras.Sequential(
        [
            tf.keras.layers.RandomFlip("horizontal"),
            tf.keras.layers.RandomRotation(0.08),
            tf.keras.layers.RandomZoom(0.1),
            tf.keras.layers.RandomBrightness(0.1),
        ],
        name="augment",
    )
    base = tf.keras.applications.MobileNetV2(
        input_shape=(IMG_SIZE, IMG_SIZE, 3), include_top=False, weights="imagenet"
    )
    base.trainable = False  # Fase 1

    inputs = tf.keras.Input(shape=(IMG_SIZE, IMG_SIZE, 3))
    x = augment(inputs)
    x = tf.keras.applications.mobilenet_v2.preprocess_input(x)  # -> [-1, 1]
    x = base(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)
    model = tf.keras.Model(inputs, outputs)
    model._base = base  # guardamos ref para el fine-tune
    return model


def export_tflite(model: tf.keras.Model, out_model: Path, out_labels: Path) -> None:
    """Convierte a TFLite float16 y escribe el labels.json."""
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float16]
    tflite = converter.convert()

    out_model.parent.mkdir(parents=True, exist_ok=True)
    out_model.write_bytes(tflite)

    labels = {
        "input_size": IMG_SIZE,
        "preprocess": "mobilenet_v2 (-1..1)",
        "classes": CLASS_ORDER,
        "pretty": [PRETTY_LABELS[c] for c in CLASS_ORDER],
        "note": "El indice del softmax mapea a 'classes'. Umbral de confianza "
        "sugerido 0.6 (debajo -> no setear, F-A1).",
    }
    out_labels.write_text(json.dumps(labels, ensure_ascii=False, indent=2), "utf-8")
    size_mb = out_model.stat().st_size / (1024 * 1024)
    print(f"\n  TFLite -> {out_model}  ({size_mb:.1f} MB)")
    print(f"  labels -> {out_labels}")


def main() -> None:
    repo = Path(__file__).resolve().parent.parent  # Gesti-n-Siniestros/
    ap = argparse.ArgumentParser(description="Entrena el clasificador de severidad (CU-35)")
    ap.add_argument("--data-dir", type=Path, default=repo / "scripts" / "data" / "dataset")
    ap.add_argument("--out-model", type=Path,
                    default=repo / "mobile" / "assets" / "models" / "damage_mobilenet.tflite")
    ap.add_argument("--out-labels", type=Path,
                    default=repo / "mobile" / "assets" / "models" / "damage_labels.json")
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--val-split", type=float, default=0.2)
    ap.add_argument("--epochs-head", type=int, default=12)
    ap.add_argument("--epochs-finetune", type=int, default=8)
    args = ap.parse_args()

    if not args.data_dir.exists():
        raise SystemExit(
            f"No existe {args.data_dir}. Arma las carpetas por clase "
            f"({', '.join(CLASS_ORDER)}) — ver scripts/README_cu35.md."
        )

    print(f"Dataset: {args.data_dir}")
    train_ds, val_ds = build_datasets(args.data_dir, args.batch, args.val_split)

    model = build_model(len(CLASS_ORDER))
    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    print("\n== Fase 1: entrenando la cabeza (backbone congelado) ==")
    model.fit(train_ds, validation_data=val_ds, epochs=args.epochs_head)

    print("\n== Fase 2: fine-tune de las capas superiores ==")
    base = model._base
    base.trainable = True
    for layer in base.layers[:-30]:  # solo las ultimas ~30 capas
        layer.trainable = False
    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-5),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    model.fit(train_ds, validation_data=val_ds, epochs=args.epochs_finetune)

    val_loss, val_acc = model.evaluate(val_ds)
    print(f"\n  Val accuracy final: {val_acc:.3f}")

    export_tflite(model, args.out_model, args.out_labels)
    print("\nListo. Bundlealo en el APK (mobile/assets/models) y rebuildea.")


if __name__ == "__main__":
    main()
